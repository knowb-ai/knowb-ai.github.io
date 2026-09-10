"""Folder onboarding and portable client configuration."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from .config import ConfigurationError, _find_repository_root, _is_within, _resolve
from .models import KnowledgeSource


_PROJECT_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
_JSON_INDENT = 2


class OnboardingError(ConfigurationError):
    """Raised when a folder cannot be onboarded safely."""


def _safe_name(name: str) -> str:
    candidate = re.sub(r"[^A-Za-z0-9_.-]", "-", name.strip())
    return candidate or "project"


def _project_root(folder: str | Path) -> Path:
    return Path(folder).expanduser().absolute()


def _manifest_template(project_id: str, name: str, visibility: str = "local") -> dict[str, Any]:
    return {
        "version": 1,
        "id": project_id,
        "name": name,
        "owner": "knowb-ai",
        "lifecycle": "active",
        "knowledge": {"roots": [{"path": ".", "include": ["**/*.md"]}]},
        "directory": {"visibility": visibility},
    }


def _registry_template(project_path: Path, project_id: str, name: str) -> dict[str, Any]:
    return {
        "version": 1,
        "organization": "knowb-ai",
        "strict_manifests": False,
        "max_discovery_depth": 2,
        "max_file_bytes": 1048576,
        "allowed_roots": [str(project_path)],
        "state_dir": str(project_path / ".knowb-state"),
        "forbidden_paths": [],
        "projects": [
            {
                "id": project_id,
                "name": name,
                "path": str(project_path),
                "knowledge": {"roots": [{"path": "."}]},
            }
        ],
    }


def init_folder(
    folder: str | Path,
    *,
    name: str | None = None,
    project_id: str | None = None,
    visibility: str = "local",
    force: bool = False,
) -> dict[str, Any]:
    """Create a portable KnowB folder with manifest, registry, and client config.

    The folder becomes self-contained: a repo-owned manifest, a connector
    registry that scopes discovery to the folder, and a client configuration
    that points at the local connector. Nothing is written outside the folder
    except the state directory, which is created inside it.
    """

    project_path = _project_root(folder)
    if not project_path.exists():
        raise OnboardingError(f"Folder does not exist: {project_path}")
    if not project_path.is_dir():
        raise OnboardingError(f"Path is not a directory: {project_path}")

    pid = _safe_name(project_id or project_path.name)
    if not _PROJECT_ID.fullmatch(pid):
        raise OnboardingError(f"Invalid project id: {pid!r}")
    display_name = (name or project_path.name).strip() or project_path.name

    knowb_dir = project_path / ".knowb"
    manifest_path = knowb_dir / "project.yml"
    registry_path = knowb_dir / "connector.yml"
    client_path = project_path / "knowb.json"
    state_dir = project_path / ".knowb-state"

    if manifest_path.exists() and not force:
        raise OnboardingError(
            f"Folder already onboarded: {manifest_path}. Pass force=True to overwrite."
        )
    if registry_path.exists() and not force:
        raise OnboardingError(
            f"Folder already onboarded: {registry_path}. Pass force=True to overwrite."
        )

    created: list[str] = []
    knowb_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    for path, data in (
        (manifest_path, _manifest_template(pid, display_name, visibility)),
        (registry_path, _registry_template(project_path, pid, display_name)),
    ):
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        created.append(str(path))

    client_config = write_client_config(project_path, pid, display_name)
    created.append(str(client_config["path"]))

    return {
        "project_id": pid,
        "name": display_name,
        "path": str(project_path),
        "manifest_path": str(manifest_path),
        "registry_path": str(registry_path),
        "client_path": str(client_config["path"]),
        "state_dir": str(state_dir),
        "created": created,
    }


def write_client_config(
    folder: str | Path,
    project_id: str,
    name: str,
    *,
    command: str = "knowb-org-mcp",
) -> dict[str, Any]:
    """Write a portable client configuration pointing at the local connector.

    The configuration is intentionally minimal: it references the installed
    connector by name and the local registry by absolute path, so any MCP
    client can consume it without knowing the website checkout layout.
    """

    project_path = _project_root(folder)
    if not project_path.is_dir():
        raise OnboardingError(f"Folder is not a directory: {project_path}")

    registry_path = project_path / ".knowb" / "connector.yml"
    if not registry_path.is_file():
        raise OnboardingError(
            f"Connector registry missing: {registry_path}. Run knowb-org init first."
        )

    config = {
        "mcpServers": {
            "knowb-org-index": {
                "command": command,
                "args": ["--config", str(registry_path)],
                "env": {"KNOWB_ORG_CONFIG": str(registry_path)},
            }
        }
    }
    client_path = project_path / "knowb.json"
    client_path.write_text(
        json.dumps(config, indent=_JSON_INDENT, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "path": str(client_path),
        "command": command,
        "registry": str(registry_path),
        "config": config,
    }


def client_config_for(folder: str | Path) -> dict[str, Any]:
    """Return the portable client configuration for a folder, if present."""

    project_path = _project_root(folder)
    client_path = project_path / "knowb.json"
    if not client_path.is_file():
        raise OnboardingError(f"No client configuration found: {client_path}")
    try:
        return json.loads(client_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OnboardingError(f"Invalid client configuration: {client_path}") from exc