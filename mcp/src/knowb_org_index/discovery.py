"""Bounded, local-only discovery of KnowB Git repositories."""

from __future__ import annotations

import re
import subprocess
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from .models import Candidate, Registry


_SCP_REMOTE = re.compile(r"^(?:[^@]+@)?github\.com:(?P<org>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$")


def github_identity(remote: str) -> tuple[str, str] | None:
    """Return (organization, repository) for GitHub SSH/HTTPS remotes."""

    value = remote.strip()
    match = _SCP_REMOTE.match(value)
    if match:
        return match.group("org"), match.group("repo")

    parsed = urlparse(value)
    if parsed.hostname and parsed.hostname.lower() == "github.com":
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) >= 2:
            repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
            return parts[0], repo
    return None


def read_origin(project_path: Path) -> str | None:
    """Read origin without contacting a remote."""

    try:
        result = subprocess.run(
            ["git", "-C", str(project_path), "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value or None


def _repositories_under(root: Path, max_depth: int) -> list[Path]:
    """Find repositories without following symlinks or crossing the depth cap."""

    found: list[Path] = []
    queue: deque[tuple[Path, int]] = deque([(root, 0)])
    while queue:
        directory, depth = queue.popleft()
        if directory.is_symlink() or not directory.is_dir():
            continue
        if (directory / ".git").exists():
            found.append(directory.resolve())
            continue
        if depth >= max_depth:
            continue
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            continue
        for child in children:
            if child.name.startswith(".") or child.is_symlink() or not child.is_dir():
                continue
            queue.append((child, depth + 1))
    return found


def discover_candidates(registry: Registry) -> list[Candidate]:
    """Discover organization repos inside allowlisted roots only."""

    registered_paths = {project.path.resolve() for project in registry.projects}
    candidates: dict[Path, Candidate] = {}
    for root in registry.allowed_roots:
        for project_path in _repositories_under(root, registry.max_discovery_depth):
            remote = read_origin(project_path)
            if not remote:
                continue
            identity = github_identity(remote)
            if not identity or identity[0].casefold() != registry.organization.casefold():
                continue
            candidate = Candidate(
                id=identity[1],
                path=project_path,
                remote=remote,
                registered=project_path in registered_paths,
                manifest_present=(project_path / ".knowb" / "project.yml").is_file(),
            )
            candidates[project_path] = candidate
    return sorted(candidates.values(), key=lambda item: item.id.casefold())
