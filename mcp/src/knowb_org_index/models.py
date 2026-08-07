"""Typed domain models shared by the registry, index, CLI, and MCP surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    """An allowlisted document root inside one project."""

    path: str
    include: tuple[str, ...] = ("**/*.md",)
    exclude: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "include": list(self.include),
            "exclude": list(self.exclude),
        }


@dataclass(frozen=True, slots=True)
class Project:
    """A project explicitly registered for local knowledge access."""

    id: str
    name: str
    path: Path
    owner: str
    lifecycle: str
    enabled: bool
    sources: tuple[KnowledgeSource, ...]
    manifest_path: Path
    manifest_present: bool
    manifest_source: str
    remote: str | None = None
    visibility: str = "local"
    warnings: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return self.path.is_dir()

    @property
    def active(self) -> bool:
        return self.enabled and self.available and bool(self.sources)

    @property
    def status(self) -> str:
        if not self.enabled:
            return "disabled"
        if not self.available:
            return "unavailable"
        if not self.sources:
            return "no_knowledge_policy"
        if self.manifest_present:
            return "registered"
        return "registered_migration"

    def to_dict(self, *, include_path: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "lifecycle": self.lifecycle,
            "enabled": self.enabled,
            "available": self.available,
            "active": self.active,
            "status": self.status,
            "remote": self.remote,
            "manifest_present": self.manifest_present,
            "manifest_source": self.manifest_source,
            "visibility": self.visibility,
            "knowledge": [source.to_dict() for source in self.sources],
            "warnings": list(self.warnings),
        }
        if include_path:
            result["path"] = str(self.path)
            result["manifest_path"] = str(self.manifest_path)
        return result


@dataclass(frozen=True, slots=True)
class Registry:
    """Validated local registry configuration."""

    config_path: Path
    repository_root: Path
    organization: str
    allowed_roots: tuple[Path, ...]
    state_dir: Path
    strict_manifests: bool
    max_discovery_depth: int
    max_file_bytes: int
    forbidden_paths: tuple[str, ...]
    projects: tuple[Project, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def database_path(self) -> Path:
        return self.state_dir / "org-index.sqlite"

    def project_map(self) -> dict[str, Project]:
        return {project.id: project for project in self.projects}


@dataclass(frozen=True, slots=True)
class Candidate:
    """A discovered local KnowB Git clone that is not implicitly trusted."""

    id: str
    path: Path
    remote: str
    registered: bool
    manifest_present: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": str(self.path),
            "remote": self.remote,
            "registered": self.registered,
            "manifest_present": self.manifest_present,
            "status": "registered" if self.registered else "candidate",
        }
