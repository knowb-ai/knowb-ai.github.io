"""Application service composing discovery, local knowledge, and GitHub work."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .config import ConfigurationError, _find_repository_root, load_registry
from .design_assets import DesignAssetOperations
from .discovery import discover_candidates
from .env import load_dotenv
from .github_ops import GitHubOperations
from .index import IndexError, LocalIndex
from .models import Project, Registry
from .okf import AdapterError, diagnostics, search_documents
from .remix import build_design_remix
from .scaffold import build_repository_blueprint


_TICKET_REFERENCE = re.compile(r"(?<![\w/])#(?P<number>\d+)\b")


class OrgIndexService:
    """Single local control-plane facade used by both the CLI and MCP server."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        legacy_root = None
        if config_path is None and not os.environ.get("KNOWB_ORG_CONFIG", "").strip():
            try:
                legacy_root = _find_repository_root()
            except ConfigurationError:
                legacy_root = None
        load_dotenv(legacy_checkout_root=legacy_root)
        self.registry: Registry = load_registry(config_path)
        self.index = LocalIndex(self.registry)
        self.github = GitHubOperations(
            self.registry.organization,
            self.index,
            self.registry.allowed_roots,
            enabled=self.registry.capabilities.github_enabled,
        )
        self.design_assets = DesignAssetOperations(
            self.registry.design_assets,
            self.index,
            github_enabled=self.registry.capabilities.github_enabled,
        )

    def draft_repository_blueprint(self, **brief: Any) -> dict[str, Any]:
        """Ideate and render a reviewable repository blueprint without writing files."""

        return build_repository_blueprint(**brief)

    def remix(self, **brief: Any) -> dict[str, Any]:
        """Run the two-place Socratic design remix without writing files."""

        return build_design_remix(**brief)

    def _project(self, project_id: str) -> Project:
        project = self.registry.project_map().get(project_id)
        if project is None:
            folded = project_id.casefold()
            project = next(
                (item for item in self.registry.projects if item.id.casefold() == folded),
                None,
            )
        if project is None:
            raise ConfigurationError(f"Unknown registered project: {project_id}")
        return project

    def list_projects(self, *, include_candidates: bool = True) -> dict[str, Any]:
        projects = []
        for project in self.registry.projects:
            item = project.to_dict()
            item["index"] = self.index.project_stats(project.id)
            projects.append(item)
        registered_paths = {project.path.resolve() for project in self.registry.projects}
        candidates = []
        if include_candidates:
            candidates = [
                candidate.to_dict()
                for candidate in discover_candidates(self.registry)
                if candidate.path.resolve() not in registered_paths
            ]
        return {
            "organization": self.registry.organization,
            "config_path": str(self.registry.config_path),
            "state_dir": str(self.registry.state_dir),
            "strict_manifests": self.registry.strict_manifests,
            "projects": projects,
            "candidates": candidates,
            "summary": {
                "registered": len(projects),
                "active": sum(1 for project in self.registry.projects if project.active),
                "unavailable": sum(1 for project in self.registry.projects if not project.available),
                "unregistered_candidates": len(candidates),
            },
        }

    def discover_local_repos(self) -> dict[str, Any]:
        """Return every local organization clone found inside allowed roots."""

        candidates = [candidate.to_dict() for candidate in discover_candidates(self.registry)]
        return {
            "organization": self.registry.organization,
            "allowed_roots": [str(root) for root in self.registry.allowed_roots],
            "repositories": candidates,
            "summary": {
                "found": len(candidates),
                "registered": sum(1 for item in candidates if item["registered"]),
                "unregistered": sum(1 for item in candidates if not item["registered"]),
            },
        }

    def refresh_index(self, project_ids: list[str] | None = None) -> dict[str, Any]:
        selected = (
            [self._project(project_id) for project_id in project_ids]
            if project_ids
            else list(self.registry.projects)
        )
        results = [self.index.refresh_project(project) for project in selected]
        return {
            "results": results,
            "summary": {
                "projects": len(results),
                "indexed": sum(result.get("indexed", 0) for result in results),
                "unchanged": sum(result.get("unchanged", 0) for result in results),
                "deleted": sum(result.get("deleted", 0) for result in results),
                "documents": sum(result.get("documents", 0) for result in results),
            },
        }

    def search_knowledge(
        self,
        query: str,
        *,
        projects: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        selected_projects = ([self._project(project_id) for project_id in projects]
                             if projects is not None else list(self.registry.projects))
        selected = list(dict.fromkeys(project.id for project in selected_projects if project.active))
        for project in selected_projects:
            self.index.refresh_project(project)
        combined = " ".join([query, *(tags or [])]).strip()
        results = self.index.search(combined, project_ids=selected, limit=limit)
        return {"query": query, "projects": selected, "tags": tags or [], "results": results}

    def read_project_doc(self, project_id: str, path: str) -> dict[str, Any]:
        project = self._project(project_id)
        if not project.active:
            raise IndexError(f"Project is not active: {project.id}")
        self.index.refresh_project(project)
        document = self.index.get_document(project.id, path)
        if document is None:
            raise IndexError(f"Document is not indexed/allowlisted: {project.id}/{path}")
        source = Path(document["source_path"]).resolve()
        try:
            source.relative_to(project.path.resolve())
        except ValueError as exc:
            raise IndexError("Indexed source no longer belongs to its project root") from exc
        if source.is_symlink() or not source.is_file():
            raise IndexError("Indexed source is no longer a safe local file")
        return document

    def get_project_context(self, project_id: str) -> dict[str, Any]:
        project = self._project(project_id)
        refresh = self.index.refresh_project(project)
        documents = self.index.list_documents(project.id)
        references: set[int] = set()
        decisions: list[dict[str, Any]] = []
        for item in documents:
            if "decision" in item["path"].casefold():
                decisions.append(item)
            document = self.index.get_document(project.id, item["path"])
            if document:
                references.update(
                    int(match.group("number"))
                    for match in _TICKET_REFERENCE.finditer(document["content"])
                )
        return {
            "project": project.to_dict(),
            "refresh": refresh,
            "documents": documents,
            "decisions": decisions,
            "ticket_references": sorted(references),
        }

    def find_related_work(
        self,
        *,
        project: str,
        ticket: int | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if ticket is None and not query:
            raise IndexError("Provide ticket or query")
        terms = [query or ""]
        if ticket is not None:
            terms.extend([f"#{int(ticket)}", str(int(ticket))])
        return self.search_knowledge(
            " ".join(terms), projects=[project], limit=limit
        )

    def org_overview(self) -> dict[str, Any]:
        directory = self.list_projects(include_candidates=True)
        return {
            "name": "KnowB Org Index",
            "organization": self.registry.organization,
            "privacy": {
                "knowledge_source": "explicitly registered local clones only",
                "transport": "stdio by default",
                "network_boundary": "GitHub is contacted only by explicit ticket/project tools",
                "design_asset_vault": self.registry.design_assets.to_dict(),
                "capabilities": self.registry.capabilities.to_dict(),
                "design_asset_network_boundary": (
                    "Google Drive is contacted only by identity-gated design-asset tools; "
                    "folder and file ACLs must not include public, domain, or group access"
                ),
                "hosted_model_warning": (
                    "A hosted MCP client can transmit returned tool content to its model provider. "
                    "Use a local client/model for strict no-egress handling."
                ),
            },
            "directory": directory,
        }

    def doctor(self) -> dict[str, Any]:
        """Run bounded local health checks without contacting optional services."""

        config_section = {
            "path": str(self.registry.config_path),
            "status": "ok",
            "organization": self.registry.organization,
            "projects": len(self.registry.projects),
            "active_projects": sum(project.active for project in self.registry.projects),
            "capabilities": self.registry.capabilities.to_dict(),
        }
        state_section: dict[str, Any] = {
            "path": str(self.registry.state_dir),
            "directory": self.registry.state_dir.is_dir(),
            "writable": False,
            "database": str(self.registry.database_path),
            "database_open": False,
            "schema_version": 0,
        }
        try:
            self.registry.state_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                prefix=".doctor-", dir=self.registry.state_dir, delete=True
            ):
                state_section["writable"] = True
            with self.index._connect() as connection:
                connection.execute("SELECT 1")
                state_section["database_open"] = True
                tables = {
                    row["name"]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                state_section["schema_version"] = 1 if "documents" in tables else 0
        except (OSError, ValueError) as exc:
            state_section["error"] = str(exc)[:300]

        search_section: dict[str, Any] = diagnostics()
        search_section["self_test"] = False
        if search_section.get("available"):
            token = "knowb-doctor-token-7f4c"
            try:
                with tempfile.TemporaryDirectory(
                    prefix="doctor-", dir=self.registry.state_dir
                ) as directory:
                    source = Path(directory) / "doctor.md"
                    content = f"# Doctor\n{token}\n"
                    source.write_text(content, encoding="utf-8")
                    hits = search_documents(
                        [
                            {
                                "project_id": "__doctor__",
                                "relative_path": "doctor.md",
                                "title": "Doctor",
                                "headings": "Doctor",
                                "source_path": str(source),
                                "content": content,
                                "indexed_at": "doctor",
                            }
                        ],
                        token,
                        1,
                        self.registry.state_dir,
                    )
                    search_section["self_test"] = bool(
                        hits and hits[0]["path"] == "doctor.md"
                    )
            except (AdapterError, IndexError, OSError) as exc:
                search_section["error"] = str(exc)[:300]

        capabilities = {
            "local_knowledge": {"enabled": True, "ready": True},
            "github": {
                "enabled": self.registry.capabilities.github_enabled,
                "ready": bool(
                    self.registry.capabilities.github_enabled and shutil.which("gh")
                ),
                "optional": True,
                "cli": bool(shutil.which("gh")),
            },
            "design_vault": {
                "enabled": self.registry.design_assets.enabled,
                "ready": False,
                "optional": True,
            },
        }
        core_ok = bool(
            state_section["writable"]
            and state_section["database_open"]
            and search_section.get("available")
            and search_section.get("self_test")
        )
        return {
            "ok": core_ok,
            "config": config_section,
            "state": state_section,
            "search": search_section,
            "capabilities": capabilities,
        }

    def project_manifest_template(self, project_id: str) -> str:
        project = self._project(project_id)
        return (
            "version: 1\n"
            f"id: {project.id}\n"
            f"name: {project.name}\n"
            f"owner: {project.owner}\n"
            f"lifecycle: {project.lifecycle}\n"
            "knowledge:\n"
            "  roots:\n"
            "    - path: docs\n"
            "      include: [\"**/*.md\"]\n"
            "      exclude: [\"private/**\", \"drafts/**\"]\n"
            "directory:\n"
            "  visibility: local\n"
        )
