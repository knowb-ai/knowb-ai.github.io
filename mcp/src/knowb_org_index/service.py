"""Application service composing discovery, local knowledge, and GitHub work."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .config import ConfigurationError, load_registry
from .design_assets import DesignAssetOperations
from .discovery import discover_candidates
from .env import load_dotenv
from .github_ops import GitHubOperations
from .index import IndexError, LocalIndex
from .models import Project, Registry
from .okf import diagnostics as _adapter_diagnostics
from .remix import build_design_remix
from .scaffold import build_repository_blueprint


_TICKET_REFERENCE = re.compile(r"(?<![\w/])#(?P<number>\d+)\b")


class OrgIndexService:
    """Single local control-plane facade used by both the CLI and MCP server."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        load_dotenv()
        self.registry: Registry = load_registry(config_path)
        self.index = LocalIndex(self.registry)
        self.github = GitHubOperations(
            self.registry.organization, self.index, self.registry.allowed_roots
        )
        self.design_assets = DesignAssetOperations(self.registry.design_assets, self.index)

    def health(self) -> dict[str, Any]:
        """Structured capability and readiness report.

        The report never returns a silent degraded state: every capability is
        declared, and a failing adapter is reported as unavailable rather than
        silently falling back to SQLite. Clients can gate behavior on this.
        """

        adapter = _adapter_diagnostics()
        projects = []
        for project in self.registry.projects:
            stats = self.index.project_stats(project.id)
            projects.append(
                {
                    "id": project.id,
                    "active": project.active,
                    "available": project.available,
                    "manifest_present": project.manifest_present,
                    "manifest_source": project.manifest_source,
                    "documents": stats.get("documents", 0),
                    "status": stats.get("status"),
                    "warnings": list(project.warnings),
                }
            )
        return {
            "ok": bool(adapter["available"]) and not any(
                project["warnings"] for project in projects
            ),
            "adapter": adapter,
            "config_path": str(self.registry.config_path),
            "state_dir": str(self.registry.state_dir),
            "database_path": str(self.registry.database_path),
            "organization": self.registry.organization,
            "strict_manifests": self.registry.strict_manifests,
            "projects": projects,
            "capabilities": self.capabilities(),
        }

    def capabilities(self) -> dict[str, Any]:
        """Declare what the server can do and what it cannot."""

        adapter = _adapter_diagnostics()
        return {
            "search_backend": "okf-rs" if adapter["available"] else "unavailable",
            "search_backend_note": (
                "okf-rs ranked full-text retrieval over scoped project snapshots"
                if adapter["available"]
                else "search_knowledge will fail until the adapter is installed"
            ),
            "knowledge_scopes": [
                "list_projects",
                "discover_local_repos",
                "refresh_index",
                "search_knowledge",
                "read_project_doc",
                "get_project_context",
                "find_related_work",
            ],
            "github_scopes": [
                "list_work",
                "get_ticket",
                "get_github_project",
                "propose_ticket_create",
                "propose_ticket_update",
                "propose_project_update",
                "confirm_ticket_create",
                "confirm_ticket_update",
                "confirm_project_update",
                "audit_log",
            ],
            "design_asset_scopes": [
                "verify_design_asset_vault",
                "authenticate_design_asset_vault",
                "list_design_assets",
                "read_design_asset",
                "propose_design_asset_upload",
                "confirm_design_asset_upload",
            ],
            "remix_scopes": ["remix", "draft_repository_blueprint"],
            "boundaries": {
                "discovery": "bounded to allowed_roots; never scans the whole computer",
                "discovered_are_candidates": True,
                "knowledge_source": "explicitly registered local clones only",
                "transport": "local stdio; no listening port",
                "network_egress": "GitHub only via explicit ticket/project tools",
                "no_silent_fallback": "missing adapter fails search; no SQLite FTS fallback",
                "design_assets_disabled_by_default": not self.registry.design_assets.enabled,
            },
        }

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
