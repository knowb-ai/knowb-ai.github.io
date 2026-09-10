#!/usr/bin/env python3
"""Generate deterministic evidence for the exact connector artifacts to release.

The command never copies source registries, state databases, or credentials into
the report. Artifact names, hashes, dependency metadata, and build provenance
are the only release inputs written to the output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import tarfile
import tomllib
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_FORBIDDEN_NAME_PARTS = {
    ".env",
    ".knowb-state",
    "local-projects.yml",
    "knowb-ai-portfolio.yml",
    "org-index.sqlite",
    "credentials.json",
}
_REVISION_RE = re.compile(r'^OKF_RS_REVISION\s*=\s*"([0-9a-f]{40})"', re.MULTILINE)


class EvidenceError(ValueError):
    """Raised when release inputs are unsafe or incomplete."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_files(directory: Path) -> list[Path]:
    files = sorted(
        path for path in directory.iterdir()
        if path.is_file() and (path.name.endswith(".whl") or path.name.endswith(".tar.gz"))
    )
    if not files:
        raise EvidenceError(f"No wheel or sdist found in {directory}")
    return files


def _assert_safe_archive(path: Path) -> None:
    names: list[str]
    try:
        if path.name.endswith(".whl"):
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
        else:
            with tarfile.open(path, "r:gz") as archive:
                names = archive.getnames()
    except (OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
        raise EvidenceError(f"Cannot inspect artifact {path.name}") from exc

    forbidden = [
        name for name in names
        if any(part.casefold() in {item.casefold() for item in _FORBIDDEN_NAME_PARTS}
               for part in Path(name).parts)
        or any(marker.casefold() in name.casefold() for marker in ("knowledgeHQ", "knowb-ai-portfolio"))
    ]
    if forbidden:
        raise EvidenceError(f"Artifact contains private paths: {forbidden[:3]}")


def _wheel_metadata(path: Path) -> tuple[str, str, list[str]]:
    try:
        with zipfile.ZipFile(path) as archive:
            candidates = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(candidates) != 1:
                raise EvidenceError(f"{path.name} must contain one METADATA file")
            text = archive.read(candidates[0]).decode("utf-8")
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
        raise EvidenceError(f"Cannot read wheel metadata from {path.name}") from exc
    name = next((line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("Name:")), "")
    version = next((line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("Version:")), "")
    requires = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("Requires-Dist:")]
    if not name or not version:
        raise EvidenceError(f"{path.name} has incomplete package metadata")
    return name, version, requires


def _cargo_inventory(root: Path) -> list[dict[str, Any]]:
    command = ["cargo", "metadata", "--locked", "--format-version", "1"]
    try:
        result = subprocess.run(
            command,
            cwd=root / "okf-bridge",
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        payload = json.loads(result.stdout)
        packages = payload.get("packages", [])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
        packages = []
    inventory: list[dict[str, Any]] = []
    for package in packages:
        source = package.get("source") or "workspace"
        licenses = package.get("license") or "UNKNOWN"
        inventory.append({
            "type": "library",
            "name": package.get("name", "unknown"),
            "version": package.get("version", "unknown"),
            "scope": "required",
            "source": source,
            "licenses": [licenses],
            "purl": f"pkg:cargo/{package.get('name', 'unknown')}@{package.get('version', 'unknown')}",
        })
    return sorted(inventory, key=lambda item: (item["name"], item["version"]))


def _python_inventory(root: Path) -> list[dict[str, Any]]:
    lock_path = root / "uv.lock"
    try:
        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise EvidenceError(f"Cannot read {lock_path}") from exc
    inventory: list[dict[str, Any]] = []
    for package in lock.get("package", []):
        name = str(package.get("name", ""))
        version = str(package.get("version", ""))
        if not name or not version or package.get("source", {}).get("editable"):
            continue
        license_name = "UNKNOWN"
        try:
            metadata = importlib.metadata.metadata(name)
            license_name = metadata.get("License-Expression") or metadata.get("License") or next(
                (value.split("::", 1)[-1].strip() for value in metadata.get_all("Classifier", [])
                 if value.startswith("License ::")),
                "UNKNOWN",
            )
        except importlib.metadata.PackageNotFoundError:
            pass
        inventory.append({
            "type": "library",
            "name": name,
            "version": version,
            "scope": "required",
            "licenses": [license_name],
            "purl": f"pkg:pypi/{name}@{version}",
        })
    return sorted(inventory, key=lambda item: (item["name"], item["version"]))


def _upstream_revision(root: Path) -> str:
    text = (root / "src" / "knowb_org_index" / "protocol.py").read_text(encoding="utf-8")
    match = _REVISION_RE.search(text)
    if not match:
        raise EvidenceError("Could not determine pinned okf-rs revision")
    return match.group(1)


def generate(
    artifact_dir: str | Path,
    output_dir: str | Path,
    *,
    source_commit: str,
    target: str,
    root: str | Path | None = None,
) -> dict[str, Any]:
    project_root = Path(root) if root else Path(__file__).resolve().parents[1]
    artifacts = _artifact_files(Path(artifact_dir).resolve())
    for artifact in artifacts:
        _assert_safe_archive(artifact)

    wheel = next((path for path in artifacts if path.name.endswith(".whl")), None)
    if wheel is None:
        raise EvidenceError("At least one wheel is required for release evidence")
    package_name, version, requirements = _wheel_metadata(wheel)
    revision = _upstream_revision(project_root)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = [
        {"name": path.name, "sha256": _sha256(path), "size": path.stat().st_size}
        for path in artifacts
    ]
    python_components = _python_inventory(project_root)
    cargo_components = _cargo_inventory(project_root)
    components = python_components + cargo_components
    serial_seed = hashlib.sha256(
        f"{package_name}:{version}:{source_commit}:{target}".encode("utf-8")
    ).hexdigest()
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:knowb:release:{serial_seed}",
        "version": 1,
        "metadata": {
            "component": {"type": "application", "name": package_name, "version": version},
            "properties": [
                {"name": "source.commit", "value": source_commit},
                {"name": "okf-rs.revision", "value": revision},
                {"name": "build.target", "value": target},
            ],
        },
        "components": components,
    }
    manifest = {
        "schema_version": 1,
        "package": package_name,
        "version": version,
        "source_commit": source_commit,
        "target": target,
        "okf_rs_revision": revision,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "requires_dist": requirements,
        "artifacts": files,
        "evidence": {
            "archive_audit": "passed",
            "private_content_policy": "no registry, credentials, state database, or corpus",
            "sbom": "sbom.cdx.json",
            "licenses": "licenses.json",
            "checksums": "checksums.txt",
        },
    }
    (output / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "sbom.cdx.json").write_text(
        json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    licenses = {
        "schema_version": 1,
        "package": package_name,
        "version": version,
        "source_commit": source_commit,
        "components": components,
        "unknown_license_count": sum(
            1 for item in components if "UNKNOWN" in item.get("licenses", [])
        ),
    }
    (output / "licenses.json").write_text(
        json.dumps(licenses, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "checksums.txt").write_text(
        "".join(f"{item['sha256']}  {item['name']}\n" for item in files), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", "local"))
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    try:
        manifest = generate(
            args.artifact_dir,
            args.output_dir,
            source_commit=args.source_commit,
            target=args.target,
        )
    except (EvidenceError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
