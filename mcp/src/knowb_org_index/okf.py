"""Export scoped documents as OKF and query the pinned Rust search adapter."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import platform
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

from .index import IndexError
from .protocol import (
    ADAPTER_VERSION,
    MAX_INFO_BYTES,
    MAX_QUERY_BYTES,
    MAX_REQUEST_BYTES,
    MAX_RESULTS,
    OKF_RS_REVISION,
    AdapterInfo,
    parse_adapter_info,
)
from .build_targets import TARGET_PLATFORMS


class AdapterError(IndexError):
    """A bounded, typed failure while invoking or validating the bridge."""


def bridge_path() -> str:
    """Return the deterministic adapter path selected for this installation."""

    configured = os.environ.get("KNOWB_OKF_BRIDGE", "").strip()
    if configured:
        return str(Path(configured).expanduser())
    package = _packaged_bridge()
    if package is not None and package.is_file():
        return str(package)
    checkout = _checkout_bridge()
    if checkout is not None:
        return str(checkout)
    if package is not None:
        return str(package)
    return str(Path(__file__).resolve().parents[2] / "okf-bridge/target/release/knowb-okf-bridge")


def _runtime_target() -> str | None:
    machine = platform.machine().casefold()
    if sys_platform := platform.system().casefold():
        if sys_platform == "darwin":
            target = f"{'aarch64' if machine in {'arm64', 'aarch64'} else 'x86_64'}-apple-darwin"
        elif sys_platform == "linux":
            target = f"{'aarch64' if machine in {'arm64', 'aarch64'} else 'x86_64'}-unknown-linux-gnu"
        elif sys_platform == "windows":
            target = f"{'aarch64' if machine in {'arm64', 'aarch64'} else 'x86_64'}-pc-windows-msvc"
        else:
            return None
        return target if target in TARGET_PLATFORMS else None
    return None


def _packaged_bridge() -> Path | None:
    target = _runtime_target()
    if target is None:
        return None
    name = f"knowb-okf-bridge-{target}" + (".exe" if os.name == "nt" else "")
    resource = resources.files("knowb_org_index").joinpath("_bin", name)
    try:
        return Path(resource)
    except TypeError:
        # A zipped/non-filesystem loader cannot safely execute a native resource.
        return None


def _checkout_bridge() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    if not (
        (root / "okf-bridge" / "Cargo.toml").is_file()
        and (root.parent / "config.toml").is_file()
        and (root.parent / "config").is_dir()
    ):
        return None
    binary = root / "okf-bridge" / "target" / "release" / "knowb-okf-bridge"
    if os.name == "nt":
        binary = binary.with_suffix(".exe")
    return binary


def diagnostics() -> dict[str, Any]:
    binary = bridge_path()
    configured = os.environ.get("KNOWB_OKF_BRIDGE", "").strip()
    source = "override" if configured else "package"
    packaged = _packaged_bridge()
    if not configured and (packaged is None or not packaged.is_file()):
        source = "checkout" if _checkout_bridge() else "package"
    path = Path(binary)
    result: dict[str, Any] = {
        "backend": "okf-rs",
        "binary": str(path),
        "source": source,
        "target": _runtime_target(),
        "available": path.is_file() and os.access(path, os.X_OK) and not path.is_symlink(),
    }
    if configured and not path.is_absolute():
        result.update({"available": False, "error": "KNOWB_OKF_BRIDGE must be absolute"})
    elif path.is_symlink():
        result.update({"available": False, "error": "adapter path must not be a symlink"})
    if result["available"]:
        try:
            info = adapter_info(str(path))
            result["info"] = info.to_dict()
        except AdapterError as exc:
            result.update({"available": False, "error": str(exc)})
    return result


def adapter_info(binary: str | None = None, *, timeout: float = 5.0) -> AdapterInfo:
    """Run the bridge handshake and validate its advertised contract."""

    selected = binary or bridge_path()
    path = Path(selected)
    if not path.is_file():
        raise AdapterError("okf-rs adapter is missing")
    if not os.access(path, os.X_OK):
        raise AdapterError("okf-rs adapter is not executable")
    try:
        result = subprocess.run(
            [str(path), "--info"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterError("okf-rs adapter handshake timed out") from exc
    except OSError as exc:
        raise AdapterError("okf-rs adapter could not be executed") from exc
    if result.returncode:
        raise AdapterError("okf-rs adapter handshake failed")
    output = result.stdout
    if len(output.encode("utf-8", errors="replace")) > MAX_INFO_BYTES:
        raise AdapterError("okf-rs adapter handshake exceeded output limit")
    try:
        parsed = parse_adapter_info(json.loads(output))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AdapterError("okf-rs adapter returned invalid handshake metadata") from exc
    if parsed.okf_rs_revision != OKF_RS_REVISION:
        raise AdapterError("okf-rs adapter revision is incompatible")
    if parsed.adapter_version != ADAPTER_VERSION:
        raise AdapterError("okf-rs adapter version is incompatible")
    return parsed


def search_documents(
    documents: list[dict[str, Any]], query: str, limit: int, state_dir: Path,
) -> list[dict[str, Any]]:
    """One scoped bundle gives all selected projects comparable BM25 scores."""
    if not query.strip():
        raise IndexError("query cannot be empty")
    if len(query.encode("utf-8")) > MAX_QUERY_BYTES:
        raise IndexError("query exceeds 16 KiB")
    if not documents:
        return []
    binary = bridge_path()
    diag = diagnostics()
    if not diag["available"]:
        detail = diag.get("error", "adapter is missing")
        raise AdapterError(
            "okf-rs search adapter is missing. Build with: cargo build --release --locked "
            f"--manifest-path mcp/okf-bridge/Cargo.toml; {detail}."
        )
    limit = max(1, min(limit, MAX_RESULTS))
    # Per-call private snapshots isolate simultaneous requests and never include
    # unselected projects, disabled repositories, or arbitrary source files.
    with tempfile.TemporaryDirectory(prefix="okf-", dir=state_dir) as directory:
        bundle = Path(directory)
        identities: dict[str, dict[str, Any]] = {}
        for doc in documents:
            identity = hashlib.sha256(
                json.dumps([doc["project_id"], doc["relative_path"]]).encode()
            ).hexdigest()
            identities[identity] = doc
            metadata = {
                "type": "DITA Document", "title": doc["title"],
                "resource": Path(doc["source_path"]).as_uri(),
                "generated": {"by": "knowb-org-index/okf-export-1"},
                "knowb_project": doc["project_id"], "knowb_path": doc["relative_path"],
            }
            (bundle / f"{identity}.md").write_text(
                "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
                + "---\n" + doc["content"], encoding="utf-8",
            )
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.2"\n---\n\n# KnowB search snapshot\n\n'
            + "\n".join(f"- [{key}]({key}.md)" for key in identities) + "\n",
            encoding="utf-8",
        )
        request = json.dumps(
            {"bundle": directory, "query": query, "limit": limit, "documents": len(documents)}
        )
        if len(request.encode("utf-8")) > MAX_REQUEST_BYTES:
            raise AdapterError("okf-rs request exceeds 64 KiB")
        try:
            result = subprocess.run(
                [binary], input=request, text=True, capture_output=True, timeout=60,
                cwd=directory, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdapterError("okf-rs adapter unavailable or timed out") from exc
        if result.returncode:
            # Never echo source-bearing diagnostics to an unrelated tool caller.
            raise AdapterError("okf-rs search failed; check the adapter build and bundle compatibility")
        if len((result.stdout or "").encode("utf-8", errors="replace")) > MAX_REQUEST_BYTES:
            raise AdapterError("Invalid response from okf-rs adapter")
        try:
            response = json.loads(result.stdout)
            hits = response["results"]
            if response["protocol"] != 1 or not isinstance(hits, list) or len(hits) > limit:
                raise ValueError("invalid protocol")
            results = []
            seen = set()
            for hit in hits:
                identity = hit["id"]
                if identity in seen:
                    raise ValueError("duplicate result")
                seen.add(identity)
                doc = identities[identity]
                score = float(hit["score"])
                if not math.isfinite(score):
                    raise ValueError("invalid score")
                terms = re.findall(r"\w+", query.casefold())
                positions = [doc["content"].casefold().find(term) for term in terms]
                start = max(0, min((p for p in positions if p >= 0), default=0) - 100)
                excerpt = doc["content"][start:start + 500]
                results.append({
                    "project": doc["project_id"], "path": doc["relative_path"],
                    "title": doc["title"], "headings": doc["headings"].splitlines(),
                    "excerpt": excerpt, "score": score, "source_path": doc["source_path"],
                    "uri": f"knowb://project/{quote(doc['project_id'], safe='')}/doc/{quote(doc['relative_path'])}",
                    "indexed_at": doc["indexed_at"], "backend": "okf-rs",
                })
            return results
        except (ValueError, KeyError, TypeError) as exc:
            raise AdapterError("Invalid response from okf-rs adapter") from exc
