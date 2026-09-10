"""Reusable, privacy-safe fixtures for connector contract tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Iterator

import yaml


def isolated_registry(root: Path, *, state_dir: Path | None = None) -> Path:
    """Create a minimal registry whose project data stays under ``root``."""

    project = root / "project"
    (project / "docs").mkdir(parents=True, exist_ok=True)
    registry = root / "registry.yml"
    registry.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "organization": "knowb-ai",
                "strict_manifests": False,
                "allowed_roots": [str(root)],
                "state_dir": str(state_dir or root / "state"),
                "projects": [
                    {
                        "id": "project",
                        "path": str(project),
                        "enabled": True,
                        "knowledge": {"roots": [{"path": "docs", "include": ["**/*.md"]}]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return registry


def sanitized_environment(*, keep: tuple[str, ...] = ()) -> dict[str, str]:
    """Return a copy with connector discovery variables removed."""

    environment = {
        key: value
        for key, value in os.environ.items()
        if key in keep or not key.startswith("KNOWB_")
    }
    environment.pop("PYTHONPATH", None)
    return environment


def temporary_workspace() -> Iterator[Path]:
    """Yield a temporary workspace helper for tests that need a real directory."""

    return _temporary_workspace()


def _temporary_workspace() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="knowb-test-") as directory:
        yield Path(directory).resolve()


def compatibility_summary(registry: Any) -> dict[str, Any]:
    """Return the non-sensitive compatibility fields used in assertions."""

    return {
        "organization": registry.organization,
        "config_path": str(registry.config_path),
        "state_dir": str(registry.state_dir),
        "projects": [
            {
                "id": project.id,
                "enabled": project.enabled,
                "active": project.active,
                "manifest_source": project.manifest_source,
            }
            for project in registry.projects
        ],
    }
