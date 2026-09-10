"""Inspection helpers for packaged connector artifacts."""

from __future__ import annotations

import zipfile
from pathlib import Path


class ArtifactError(ValueError):
    """Raised when a connector wheel does not contain a safe native payload."""


_FORBIDDEN_PARTS = {
    "config",
    ".env",
    ".knowb-state",
    "org-index.sqlite",
    "local-projects.yml",
}


def audit_wheel(path: str | Path) -> dict[str, object]:
    """Validate wheel purity metadata, native payload count, and private-file exclusion."""

    wheel = Path(path)
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            wheel_files = [name for name in names if name.endswith(".dist-info/WHEEL")]
            if len(wheel_files) != 1:
                raise ArtifactError("wheel must contain exactly one WHEEL metadata file")
            metadata = archive.read(wheel_files[0]).decode("utf-8")
            if "Root-Is-Purelib: false" not in metadata:
                raise ArtifactError("native connector wheel must be marked non-pure")
            binaries = [
                name
                for name in names
                if "/_bin/knowb-okf-bridge-" in f"/{name}" and not name.endswith("/")
            ]
            if len(binaries) != 1:
                raise ArtifactError("wheel must contain exactly one native okf-rs bridge")
            binary = archive.read(binaries[0])
            if not binary:
                raise ArtifactError("packaged okf-rs bridge is empty")
            forbidden = [
                name
                for name in names
                if any(part in _FORBIDDEN_PARTS for part in Path(name).parts)
                or name.endswith("local-projects.yml")
            ]
            if forbidden:
                raise ArtifactError(f"wheel contains forbidden private files: {forbidden[:3]}")
    except zipfile.BadZipFile as exc:
        raise ArtifactError("wheel is not a valid zip archive") from exc
    return {"path": str(wheel), "binary": binaries[0], "files": len(names)}
