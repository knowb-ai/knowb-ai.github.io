"""Supported native target to wheel platform mappings."""

from __future__ import annotations

import re


TARGET_PLATFORMS = {
    "aarch64-apple-darwin": "macosx_11_0_arm64",
    "x86_64-apple-darwin": "macosx_10_9_x86_64",
    "aarch64-unknown-linux-gnu": "manylinux_2_17_aarch64",
    "x86_64-unknown-linux-gnu": "manylinux_2_17_x86_64",
    "aarch64-pc-windows-msvc": "win_arm64",
    "x86_64-pc-windows-msvc": "win_amd64",
}
_TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*-[a-z0-9][a-z0-9_.-]*-[a-z0-9][a-z0-9_.-]*$")


def platform_tag_for_target(target: str) -> str:
    """Return the conservative wheel platform tag for a supported Rust target."""

    if not _TARGET_RE.fullmatch(target) or target not in TARGET_PLATFORMS:
        supported = ", ".join(sorted(TARGET_PLATFORMS))
        raise ValueError(f"Unsupported KNOWB_BUILD_TARGET {target!r}; supported: {supported}")
    return TARGET_PLATFORMS[target]
