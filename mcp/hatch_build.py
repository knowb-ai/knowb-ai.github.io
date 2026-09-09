"""Hatchling build hook: compile the pinned okf-rs adapter and package it.

The hook runs `cargo build --release --locked` against the checked-in
`okf-bridge` crate, then force-includes the resulting native executable under
`knowb_org_index/_bin/`. It also emits platform-specific wheel metadata
(`pure_python=false`) so installers never accept a native artifact inside a
`py3-none-any` wheel. Compilers are build-time requirements only; the shipped
wheel contains the finished binary and no Cargo dependency graph.

The hook is invoked by the `custom` build hook registered by hatchling itself.
It is defined in `pyproject.toml` under
`[tool.hatch.build.hooks.custom]`.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _adapter_name() -> str:
    """Native executable name for the current platform."""
    return "knowb-okf-bridge.exe" if sys.platform == "win32" else "knowb-okf-bridge"


def _platform_tag() -> str:
    """A PEP 425 platform tag matching the host that built the artifact."""
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        return f"macosx_11_0_{machine}"
    if sys.platform.startswith("linux"):
        return f"manylinux_2_28_{machine}"
    if sys.platform == "win32":
        return f"win_{machine}"
    raise RuntimeError(f"Unsupported build platform: {sys.platform!r}")


class KnowbOrgIndexBuildHook(BuildHookInterface):
    """Compile and package the okf-rs Rust adapter for the current target."""

    PLUGIN_NAME = "knowb-org-index"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:  # noqa: ARG002
        root = _project_root()
        adapter = _adapter_name()
        crate = root / "okf-bridge"
        target_dir = crate / "target" / "release"
        binary = target_dir / adapter

        # The sdist ships source/build inputs (hook, Cargo files, lockfile,
        # Rust source) so a wheel can be rebuilt elsewhere; it never ships the
        # compiled binary. Only the wheel target packages the native artifact.
        if self.target_name != "wheel":
            return

        # Rebuild only when the binary is absent or older than its sources.
        needs_build = not binary.is_file()
        if not needs_build:
            newest_source = max(
                (p.stat().st_mtime for p in crate.rglob("*") if p.is_file()),
                default=0.0,
            )
            needs_build = binary.stat().st_mtime < newest_source

        if needs_build:
            env = dict(os.environ)
            # Prefer the Command Line Tools on macOS when Xcode is broken;
            # this is a documented developer convenience, not a runtime need.
            if sys.platform == "darwin" and "DEVELOPER_DIR" not in env:
                clt = "/Library/Developer/CommandLineTools"
                if Path(clt).is_dir():
                    env["DEVELOPER_DIR"] = clt
            result = subprocess.run(
                ["cargo", "build", "--release", "--locked", "--manifest-path", str(crate / "Cargo.toml")],
                cwd=str(root),
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "Failed to build the okf-rs adapter:\n"
                    + (result.stderr or result.stdout)
                )

        if not binary.is_file():
            raise RuntimeError(
                f"okf-rs adapter binary is missing after build: {binary}"
            )

        # Force-include the native executable inside the package tree. The
        # distribution path is stable so runtime code can locate it without
        # guessing at checkout layout.
        build_data["force_include"][str(binary)] = f"knowb_org_index/_bin/{adapter}"

        # Runtime schemas and templates ship as package data.
        resources = root / "src" / "knowb_org_index" / "resources"
        if resources.is_dir():
            build_data["force_include"][str(resources)] = "knowb_org_index/resources"

        # Platform metadata: never ship native contents in a pure wheel.
        build_data["pure_python"] = False
        build_data["infer_tag"] = False
        build_data["tag"] = f"cp311-abi3-{_platform_tag()}"

        # License notices travel with the wheel.
        license_dir = root / "licenses"
        if license_dir.is_dir():
            for entry in sorted(license_dir.iterdir()):
                if entry.is_file():
                    build_data["force_include"][str(entry)] = f"licenses/{entry.name}"