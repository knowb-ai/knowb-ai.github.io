"""Operator-invoked registration and enablement of local projects.

These operations replace hand-editing the registry YAML. They deliberately do
not weaken the consent boundary: registering a project does not enable it, and
nothing here is exposed as an MCP tool, so a connected model cannot widen what
it is allowed to index.

Edits are line-scoped rather than a YAML round-trip so that operator comments,
ordering, and formatting in a human-maintained registry survive a write. Every
candidate file is validated by a full registry load before it replaces the
original, and writes are atomic.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .config import ConfigurationError, _is_within, _resolve, load_registry
from .discovery import github_identity, read_origin

_PROJECT_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
_TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:")
_DEFAULT_ITEM_INDENT = 2


class RegistryOpsError(ConfigurationError):
    """Raised when a registry mutation would be unsafe or ambiguous."""


def _scalar(value: Any) -> str:
    """Render one YAML scalar with correct quoting."""

    return yaml.safe_dump(value, allow_unicode=True, default_flow_style=True).split("\n")[0]


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise RegistryOpsError(f"Registry file does not exist: {path}") from exc


def _is_blank_or_comment(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _projects_block(lines: list[str]) -> tuple[int, int, int]:
    """Return (header index, end index exclusive, item indent) for ``projects:``.

    A header index of -1 means the key is absent.
    """

    header = -1
    for number, line in enumerate(lines):
        if _TOP_LEVEL_KEY.match(line) and line.split(":", 1)[0] == "projects":
            header = number
            break
    if header == -1:
        return -1, len(lines), _DEFAULT_ITEM_INDENT

    end = len(lines)
    for number in range(header + 1, len(lines)):
        line = lines[number]
        if _is_blank_or_comment(line):
            continue
        if _TOP_LEVEL_KEY.match(line):
            end = number
            break

    indent = _DEFAULT_ITEM_INDENT
    for number in range(header + 1, end):
        stripped = lines[number].lstrip()
        if stripped.startswith("- "):
            indent = len(lines[number]) - len(stripped)
            break

    while end > header + 1 and _is_blank_or_comment(lines[end - 1]):
        end -= 1
    return header, end, indent


def _item_spans(lines: list[str], header: int, end: int, indent: int) -> list[tuple[int, int]]:
    """Return inclusive-exclusive line spans for each project list item."""

    starts = [
        number
        for number in range(header + 1, end)
        if lines[number].startswith(" " * indent + "- ")
    ]
    return [
        (start, starts[position + 1] if position + 1 < len(starts) else end)
        for position, start in enumerate(starts)
    ]


def _entry_lines(
    *,
    project_id: str,
    name: str | None,
    path_value: str,
    enabled: bool,
    indent: int,
) -> list[str]:
    key_indent = " " * (indent + 2)
    lines = [f"{' ' * indent}- id: {_scalar(project_id)}"]
    if name and name != project_id:
        lines.append(f"{key_indent}name: {_scalar(name)}")
    lines.extend(
        [
            f"{key_indent}path: {_scalar(path_value)}",
            f"{key_indent}enabled: {_scalar(enabled)}",
        ]
    )
    return lines


def _registry_path(config_path: str | Path | None) -> Path:
    if config_path is None:
        raise RegistryOpsError("An explicit registry path is required")
    path = Path(config_path).expanduser().resolve()
    if not path.is_file():
        raise RegistryOpsError(f"Registry file does not exist: {path}")
    if path.name.endswith(".example.yml"):
        raise RegistryOpsError(
            f"Refusing to modify the committed example registry: {path}. "
            "Copy it to a real registry first."
        )
    return path


def _identity_from_project(project_path: Path) -> tuple[str | None, str | None]:
    """Derive (id, name) from the repo-owned manifest, then the git remote."""

    manifest_path = project_path / ".knowb" / "project.yml"
    if manifest_path.is_file() and not manifest_path.is_symlink():
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise RegistryOpsError(f"Invalid manifest at {manifest_path}: {exc}") from exc
        if isinstance(manifest, dict):
            manifest_id = str(manifest.get("id", "")).strip() or None
            manifest_name = str(manifest.get("name", "")).strip() or None
            return manifest_id, manifest_name

    remote = read_origin(project_path)
    identity = github_identity(remote) if remote else None
    return (identity[1] if identity else None), None


def _relative_path(project_path: Path, registry_path: Path) -> str:
    try:
        return os.path.relpath(project_path, registry_path.parent)
    except ValueError:
        return str(project_path)


def _commit(registry_path: Path, lines: list[str]) -> None:
    """Validate a candidate registry, then replace the original atomically."""

    content = "\n".join(lines) + "\n"
    directory = registry_path.parent
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=directory,
        prefix=f".{registry_path.name}.",
        suffix=".tmp",
        delete=False,
    )
    candidate = Path(handle.name)
    try:
        with handle:
            handle.write(content)
        try:
            load_registry(candidate)
        except ConfigurationError as exc:
            raise RegistryOpsError(
                f"Refusing to write an invalid registry: {exc}. The original file is unchanged."
            ) from exc
        os.replace(candidate, registry_path)
    except BaseException:
        candidate.unlink(missing_ok=True)
        raise


def register_project(
    config_path: str | Path | None,
    project: str | Path,
    *,
    project_id: str | None = None,
    name: str | None = None,
    enabled: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add one local project to the registry without enabling it by default.

    Registration and enablement stay separate decisions: a freshly registered
    project is inert until an operator enables it.
    """

    registry_path = _registry_path(config_path)
    registry = load_registry(registry_path)

    project_path = Path(project).expanduser()
    project_path = (
        project_path.resolve()
        if project_path.is_absolute()
        else _resolve(Path.cwd(), project_path)
    )
    if not project_path.is_dir():
        raise RegistryOpsError(f"Project path is not a directory: {project_path}")
    if not any(_is_within(project_path, root) for root in registry.allowed_roots):
        raise RegistryOpsError(
            f"Project path is outside allowed_roots and cannot be registered: {project_path}"
        )

    derived_id, derived_name = _identity_from_project(project_path)
    resolved_id = (project_id or derived_id or project_path.name).strip()
    if not _PROJECT_ID.fullmatch(resolved_id):
        raise RegistryOpsError(f"Invalid project id: {resolved_id!r}")
    resolved_name = (name or derived_name or "").strip() or None

    for existing in registry.projects:
        if existing.id.casefold() == resolved_id.casefold():
            return {
                "action": "register",
                "changed": False,
                "reason": "already registered",
                "dry_run": dry_run,
                "registry": str(registry_path),
                "project": {
                    "id": existing.id,
                    "name": existing.name,
                    "path": str(existing.path),
                    "enabled": existing.enabled,
                },
            }
        if existing.path == project_path:
            raise RegistryOpsError(
                f"Path already registered under a different id {existing.id!r}: {project_path}"
            )

    lines = _read_lines(registry_path)
    header, end, indent = _projects_block(lines)
    entry = _entry_lines(
        project_id=resolved_id,
        name=resolved_name,
        path_value=_relative_path(project_path, registry_path),
        enabled=enabled,
        indent=indent,
    )

    if header == -1:
        updated = [*lines, "projects:", *entry]
    else:
        spans = _item_spans(lines, header, end, indent)
        inline = lines[header].split(":", 1)[1].strip()
        if not spans and inline in {"[]", "{}"}:
            updated = [*lines[:header], "projects:", *entry, *lines[header + 1 :]]
        else:
            updated = [*lines[:end], *entry, *lines[end:]]

    result: dict[str, Any] = {
        "action": "register",
        "changed": True,
        "dry_run": dry_run,
        "registry": str(registry_path),
        "project": {
            "id": resolved_id,
            "name": resolved_name or resolved_id,
            "path": str(project_path),
            "enabled": enabled,
        },
        "entry": "\n".join(entry),
    }
    if dry_run:
        return result
    _commit(registry_path, updated)
    return result


def set_project_enabled(
    config_path: str | Path | None,
    project_id: str,
    *,
    enabled: bool,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Flip one registered project's ``enabled`` flag."""

    action = "enable" if enabled else "disable"
    registry_path = _registry_path(config_path)
    registry = load_registry(registry_path)

    target = next(
        (item for item in registry.projects if item.id.casefold() == project_id.casefold()),
        None,
    )
    if target is None:
        raise RegistryOpsError(f"Project is not registered: {project_id}")

    payload: dict[str, Any] = {
        "action": action,
        "changed": target.enabled != enabled,
        "dry_run": dry_run,
        "registry": str(registry_path),
        "project": {
            "id": target.id,
            "name": target.name,
            "path": str(target.path),
            "enabled": enabled,
        },
    }
    if target.enabled == enabled:
        payload["reason"] = f"already {action}d"
        return payload
    if dry_run:
        return payload

    lines = _read_lines(registry_path)
    header, end, indent = _projects_block(lines)
    key_indent = " " * (indent + 2)
    span = None
    for start, stop in _item_spans(lines, header, end, indent):
        block = "\n".join(lines[start:stop])
        parsed = yaml.safe_load(block)
        entry = parsed[0] if isinstance(parsed, list) and parsed else None
        if isinstance(entry, dict) and str(entry.get("id", "")).casefold() == target.id.casefold():
            span = (start, stop)
            break
    if span is None:
        raise RegistryOpsError(f"Could not locate the registry entry for {target.id}")

    start, stop = span
    updated = list(lines)
    for number in range(start, stop):
        stripped = updated[number].strip()
        if stripped.startswith("enabled:"):
            prefix = updated[number][: len(updated[number]) - len(updated[number].lstrip())]
            updated[number] = f"{prefix}enabled: {_scalar(enabled)}"
            break
    else:
        updated.insert(start + 1, f"{key_indent}enabled: {_scalar(enabled)}")

    _commit(registry_path, updated)
    return payload
