"""Hatch build hook that embeds one native okf-rs bridge in each wheel."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_SOURCE_ROOT = Path(__file__).resolve().parent / "src"
if str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))
from knowb_org_index.build_targets import platform_tag_for_target  # noqa: E402


def _native_target() -> str:
    configured = os.environ.get("KNOWB_BUILD_TARGET", "").strip()
    if configured:
        return configured
    try:
        result = subprocess.run(
            ["rustc", "-vV"], check=True, capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Cargo and rustc are required to build the okf-rs adapter") from exc
    for line in result.stdout.splitlines():
        if line.startswith("host:"):
            return line.split(":", 1)[1].strip()
        raise RuntimeError("rustc did not report a host target")


class CustomBuildHook(BuildHookInterface):
    """Compile and force-include the target-specific bridge in a wheel."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        if self.target_name != "wheel":
            return
        configured_target = os.environ.get("KNOWB_BUILD_TARGET", "").strip()
        target = configured_target or _native_target()
        platform_tag = platform_tag_for_target(target)
        if os.environ.get("KNOWB_WHEEL_PLATFORM", platform_tag) != platform_tag:
            raise ValueError(
                "KNOWB_WHEEL_PLATFORM does not match the declared Rust target "
                f"{target}: expected {platform_tag}"
            )
        configured_target_dir = os.environ.get("KNOWB_CARGO_TARGET_DIR", "").strip()
        staging = None if configured_target_dir else Path(tempfile.mkdtemp(prefix="knowb-okf-build-"))
        self._staging = staging
        cargo_target = Path(configured_target_dir) if configured_target_dir else staging / "cargo-target"
        manifest = Path(self.root) / "okf-bridge" / "Cargo.toml"
        environment = os.environ.copy()
        environment["CARGO_TARGET_DIR"] = str(cargo_target)
        # Prefer the standalone macOS toolchain when the active Xcode selection
        # is broken; this keeps local builds deterministic in CI and developer
        # shells without changing the user's global xcode-select setting.
        command_line_tools = Path("/Library/Developer/CommandLineTools")
        if "DEVELOPER_DIR" not in environment and command_line_tools.is_dir():
            environment["DEVELOPER_DIR"] = str(command_line_tools)
        try:
            cargo_args = [
                "cargo",
                "build",
                "--release",
                "--locked",
            ]
            if configured_target:
                cargo_args.extend(["--target", configured_target])
            cargo_args.extend(["--manifest-path", str(manifest)])
            subprocess.run(
                cargo_args,
                cwd=self.root,
                env=environment,
                check=True,
                timeout=900,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            if staging:
                shutil.rmtree(staging, ignore_errors=True)
            raise RuntimeError("Failed to build the pinned okf-rs adapter") from exc
        release_dir = cargo_target / target / "release" if configured_target else cargo_target / "release"
        executable = release_dir / "knowb-okf-bridge"
        if os.name == "nt":
            executable = executable.with_suffix(".exe")
        if not executable.is_file():
            if staging:
                shutil.rmtree(staging, ignore_errors=True)
            raise RuntimeError(f"Cargo build did not produce {executable.name}")
        if os.name != "nt":
            executable.chmod(executable.stat().st_mode | 0o111)
        resource_name = f"knowb-okf-bridge-{target}" + (".exe" if os.name == "nt" else "")
        package_path = f"knowb_org_index/_bin/{resource_name}"
        build_data.setdefault("force_include", {})[str(executable)] = package_path
        build_data["pure_python"] = False
        build_data["infer_tag"] = False
        build_data["tag"] = f"py3-none-{platform_tag}"

    def finalize(
        self, version: str, build_data: dict[str, object], artifact_path: str
    ) -> None:
        staging = getattr(self, "_staging", None)
        if staging:
            shutil.rmtree(staging, ignore_errors=True)
