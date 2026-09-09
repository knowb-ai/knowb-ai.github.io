"""Registry and repo-owned manifest loading with strict path containment."""

from __future__ import annotations

import os
import re
import hashlib
import sys
from pathlib import Path
from typing import Any

import yaml

from .discovery import read_origin
from .models import CapabilityConfig, DesignAssetConfig, KnowledgeSource, Project, Registry


_PROJECT_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
_DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+$")


class ConfigurationError(ValueError):
    """Raised when local registry data is invalid or unsafe."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration file does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"Expected a YAML mapping in {path}")
    return data


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve(base: Path, raw: str | os.PathLike[str]) -> Path:
    value = Path(raw).expanduser()
    return (base / value).resolve() if not value.is_absolute() else value.resolve()


def _is_verified_checkout(root: Path) -> bool:
    """Recognize the connector source layout without trusting arbitrary folders."""

    return (
        (root / "config.toml").is_file()
        and (root / "config").is_dir()
        and (root / "mcp" / "pyproject.toml").is_file()
    )


def _find_repository_root() -> Path:
    override = os.environ.get("KNOWB_ORG_ROOT")
    if override:
        root = Path(override).expanduser().resolve()
        if _is_verified_checkout(root):
            return root
        raise ConfigurationError(
            "KNOWB_ORG_ROOT must point to a verified KnowB checkout containing "
            "config.toml, config/, and mcp/pyproject.toml"
        )
    candidates = [Path.cwd().resolve()]
    for candidate in candidates:
        for parent in (candidate, *candidate.parents):
            if _is_verified_checkout(parent):
                return parent
    raise ConfigurationError(
        "Cannot locate the KnowB repository root. Set KNOWB_ORG_ROOT explicitly."
    )


def default_config_path() -> Path:
    override = os.environ.get("KNOWB_ORG_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    root = _find_repository_root()
    local = root / "config" / "local-projects.yml"
    return local if local.is_file() else root / "config" / "local-projects.example.yml"


def _default_state_root() -> Path:
    override = os.environ.get("KNOWB_STATE_ROOT", "").strip()
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise ConfigurationError("KNOWB_STATE_ROOT must be an absolute path")
        return path.resolve()
    if sys.platform == "darwin":
        return (Path.home() / "Library" / "Application Support").resolve()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")).resolve()
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")).expanduser().resolve()


def _state_dir(base: Path, data: dict[str, Any], resolved_config: Path) -> Path:
    if "state_dir" in data:
        return _resolve(base, data["state_dir"])
    key = hashlib.sha256(str(resolved_config).encode("utf-8")).hexdigest()[:24]
    return _default_state_root() / "knowb-org-index" / key


def _capabilities(value: Any) -> CapabilityConfig:
    if value is None:
        return CapabilityConfig()
    if not isinstance(value, dict):
        raise ConfigurationError("capabilities must be a mapping")
    github = value.get("github", {})
    if isinstance(github, bool):
        enabled = github
    elif isinstance(github, dict):
        raw_enabled = github.get("enabled", True)
        if not isinstance(raw_enabled, bool):
            raise ConfigurationError("capabilities.github.enabled must be a boolean")
        enabled = raw_enabled
    else:
        raise ConfigurationError("capabilities.github must be a mapping or boolean")
    return CapabilityConfig(github_enabled=enabled)


def _string_list(value: Any, *, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigurationError("Expected a list of string patterns")
    return tuple(value)


def _knowledge_sources(value: Any) -> tuple[KnowledgeSource, ...]:
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise ConfigurationError("knowledge must be a mapping")

    roots = value.get("roots")
    if roots is None and "root" in value:
        roots = [
            {
                "path": value["root"],
                "include": value.get("include", ["**/*.md"]),
                "exclude": value.get("exclude", []),
            }
        ]
    if not isinstance(roots, list) or not roots:
        raise ConfigurationError("knowledge must define root or a non-empty roots list")

    sources: list[KnowledgeSource] = []
    for raw in roots:
        item = {"path": raw} if isinstance(raw, str) else raw
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ConfigurationError("Each knowledge root must be a path string or mapping")
        source_path = item["path"].strip()
        if not source_path or Path(source_path).is_absolute():
            raise ConfigurationError("Knowledge roots must be non-empty project-relative paths")
        sources.append(
            KnowledgeSource(
                path=source_path,
                include=_string_list(item.get("include"), default=("**/*.md",)),
                exclude=_string_list(item.get("exclude")),
            )
        )
    return tuple(sources)


def _design_assets(
    value: Any,
    *,
    base: Path,
    allowed_roots: tuple[Path, ...],
) -> DesignAssetConfig:
    """Load a disabled-by-default, explicitly scoped private Drive policy."""

    if value is None:
        return DesignAssetConfig()
    if not isinstance(value, dict):
        raise ConfigurationError("design_assets must be a mapping")

    enabled = bool(value.get("enabled", False))
    folder_id = str(value.get("google_drive_folder_id", "")).strip()
    google_email = str(value.get("allowed_google_email", "")).strip().casefold()
    github_logins = tuple(
        login.strip().casefold()
        for login in _string_list(value.get("allowed_github_logins"))
        if login.strip()
    )
    if folder_id and not _DRIVE_ID.fullmatch(folder_id):
        raise ConfigurationError("design_assets.google_drive_folder_id is not a valid Drive id")
    if google_email and not _EMAIL.fullmatch(google_email):
        raise ConfigurationError("design_assets.allowed_google_email must be an email address")
    if enabled and not folder_id:
        raise ConfigurationError("Enabled design_assets must define google_drive_folder_id")
    if enabled and not google_email:
        raise ConfigurationError("Enabled design_assets must define allowed_google_email")
    if enabled and not github_logins:
        raise ConfigurationError("Enabled design_assets must define allowed_github_logins")

    raw_upload_roots = value.get("allowed_upload_roots", [])
    if not isinstance(raw_upload_roots, list) or not all(
        isinstance(item, str) and item.strip() for item in raw_upload_roots
    ):
        raise ConfigurationError("design_assets.allowed_upload_roots must be a list of paths")
    upload_roots = tuple(_resolve(base, item) for item in raw_upload_roots)
    if enabled and not upload_roots:
        raise ConfigurationError("Enabled design_assets must define allowed_upload_roots")
    for root in upload_roots:
        if not any(_is_within(root, allowed_root) for allowed_root in allowed_roots):
            raise ConfigurationError(
                f"Design asset upload root is outside allowed_roots: {root}"
            )

    max_file_bytes = max(
        1024,
        min(int(value.get("max_file_bytes", 5 * 1024 * 1024)), 20_971_520),
    )
    extensions = tuple(
        extension.strip().casefold()
        if extension.strip().startswith(".")
        else f".{extension.strip().casefold()}"
        for extension in _string_list(
            value.get("allowed_extensions"),
            default=DesignAssetConfig().allowed_extensions,
        )
        if extension.strip()
    )
    if not extensions:
        raise ConfigurationError("design_assets.allowed_extensions cannot be empty")

    return DesignAssetConfig(
        enabled=enabled,
        google_drive_folder_id=folder_id,
        allowed_google_email=google_email,
        allowed_github_logins=github_logins,
        allowed_upload_roots=upload_roots,
        max_file_bytes=max_file_bytes,
        allowed_extensions=extensions,
    )


def load_registry(config_path: str | Path | None = None) -> Registry:
    """Load and validate the local registry plus repo-owned manifests."""

    explicit_config = config_path is not None or bool(os.environ.get("KNOWB_ORG_CONFIG", "").strip())
    resolved_config = Path(config_path).expanduser().resolve() if config_path else default_config_path()
    data = _load_yaml(resolved_config)
    if data.get("version") != 1:
        raise ConfigurationError("Registry version must be 1")

    base = resolved_config.parent
    repository_root = base if explicit_config else _find_repository_root()
    raw_roots = data.get("allowed_roots")
    if not isinstance(raw_roots, list) or not raw_roots:
        raise ConfigurationError("allowed_roots must contain at least one local directory")
    allowed_roots = tuple(_resolve(base, item) for item in raw_roots if isinstance(item, str))
    if len(allowed_roots) != len(raw_roots):
        raise ConfigurationError("allowed_roots entries must be strings")

    organization = str(data.get("organization", "knowb-ai")).strip()
    if not organization:
        raise ConfigurationError("organization cannot be empty")
    strict_manifests = bool(data.get("strict_manifests", True))
    state_dir = _state_dir(base, data, resolved_config)
    forbidden_paths = _string_list(data.get("forbidden_paths"))
    max_depth = max(0, min(int(data.get("max_discovery_depth", 2)), 5))
    max_file_bytes = max(1024, min(int(data.get("max_file_bytes", 1_048_576)), 20_971_520))
    design_assets = _design_assets(
        data.get("design_assets"), base=base, allowed_roots=allowed_roots
    )
    capabilities = _capabilities(data.get("capabilities"))

    raw_projects = data.get("projects", [])
    if not isinstance(raw_projects, list):
        raise ConfigurationError("projects must be a list")

    projects: list[Project] = []
    seen_ids: set[str] = set()
    for raw in raw_projects:
        if not isinstance(raw, dict):
            raise ConfigurationError("Each project registry entry must be a mapping")
        project_id = str(raw.get("id", "")).strip()
        if not _PROJECT_ID.fullmatch(project_id):
            raise ConfigurationError(f"Invalid project id: {project_id!r}")
        folded_id = project_id.casefold()
        if folded_id in seen_ids:
            raise ConfigurationError(f"Duplicate project id: {project_id}")
        seen_ids.add(folded_id)

        if not isinstance(raw.get("path"), str):
            raise ConfigurationError(f"Project {project_id} must define a local path")
        project_path = _resolve(base, raw["path"])
        if not any(_is_within(project_path, root) for root in allowed_roots):
            raise ConfigurationError(
                f"Project {project_id} is outside allowed_roots: {project_path}"
            )

        manifest_path = project_path / ".knowb" / "project.yml"
        manifest_present = manifest_path.is_file() and not manifest_path.is_symlink()
        manifest: dict[str, Any] = _load_yaml(manifest_path) if manifest_present else {}
        warnings: list[str] = []
        if manifest_present:
            manifest_id = str(manifest.get("id", "")).strip()
            if manifest.get("version") != 1 or manifest_id != project_id:
                raise ConfigurationError(
                    f"Manifest identity/version mismatch for {project_id}: {manifest_path}"
                )
        elif strict_manifests and bool(raw.get("enabled", True)):
            warnings.append("Missing required .knowb/project.yml; project is not indexable")
        elif bool(raw.get("enabled", True)):
            warnings.append("Using explicit registry knowledge policy until repo manifest is adopted")

        policy = manifest.get("knowledge") if manifest_present else raw.get("knowledge")
        sources = _knowledge_sources(policy) if policy is not None else ()
        if strict_manifests and not manifest_present:
            sources = ()

        for source in sources:
            source_root = (project_path / source.path).resolve()
            if not _is_within(source_root, project_path):
                raise ConfigurationError(
                    f"Knowledge root escapes project {project_id}: {source.path}"
                )

        directory = manifest.get("directory") if manifest_present else raw.get("directory", {})
        directory = directory if isinstance(directory, dict) else {}
        projects.append(
            Project(
                id=project_id,
                name=str(manifest.get("name") or raw.get("name") or project_id),
                path=project_path,
                owner=str(manifest.get("owner") or raw.get("owner") or organization),
                lifecycle=str(manifest.get("lifecycle") or raw.get("lifecycle") or "active"),
                enabled=bool(raw.get("enabled", True)),
                sources=sources,
                manifest_path=manifest_path,
                manifest_present=manifest_present,
                manifest_source="repository" if manifest_present else "registry",
                remote=read_origin(project_path) if project_path.is_dir() else None,
                visibility=str(directory.get("visibility", "local")),
                warnings=tuple(warnings),
            )
        )

    return Registry(
        config_path=resolved_config,
        repository_root=repository_root,
        organization=organization,
        allowed_roots=allowed_roots,
        state_dir=state_dir,
        strict_manifests=strict_manifests,
        max_discovery_depth=max_depth,
        max_file_bytes=max_file_bytes,
        forbidden_paths=forbidden_paths,
        projects=tuple(projects),
        design_assets=design_assets,
        capabilities=capabilities,
    )
