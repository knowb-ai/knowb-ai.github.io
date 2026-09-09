"""Versioned protocol constants shared by the Python connector and Rust bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROTOCOL_VERSION = 1
ADAPTER_VERSION = "0.2.0"
OKF_RS_REVISION = "6d52cc7ad0b5afea2e0001779b4498e268905ddc"
MAX_REQUEST_BYTES = 65_536
MAX_QUERY_BYTES = 16_384
MAX_RESULTS = 50
MAX_INFO_BYTES = 8_192
MAX_DOCUMENTS = 10_000


@dataclass(frozen=True, slots=True)
class AdapterInfo:
    """Validated metadata returned by ``knowb-okf-bridge --info``."""

    protocol: int
    adapter_version: str
    okf_rs_revision: str
    build_target: str
    max_request_bytes: int
    max_query_bytes: int
    max_results: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "adapter_version": self.adapter_version,
            "okf_rs_revision": self.okf_rs_revision,
            "build_target": self.build_target,
            "max_request_bytes": self.max_request_bytes,
            "max_query_bytes": self.max_query_bytes,
            "max_results": self.max_results,
        }


def parse_adapter_info(value: Any) -> AdapterInfo:
    """Validate an adapter info object without accepting coercive values."""

    if not isinstance(value, dict):
        raise ValueError("adapter info must be a JSON object")
    required = {
        "protocol",
        "adapter_version",
        "okf_rs_revision",
        "build_target",
        "max_request_bytes",
        "max_query_bytes",
        "max_results",
    }
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unknown {', '.join(extra)}")
        raise ValueError("invalid adapter info fields: " + "; ".join(detail))
    if value["protocol"] != PROTOCOL_VERSION:
        raise ValueError(f"unsupported adapter protocol: {value['protocol']!r}")
    for field in ("adapter_version", "okf_rs_revision", "build_target"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f"adapter info field {field!r} must be a non-empty string")
    limits = {
        "max_request_bytes": MAX_REQUEST_BYTES,
        "max_query_bytes": MAX_QUERY_BYTES,
        "max_results": MAX_RESULTS,
    }
    for field, expected in limits.items():
        actual = value[field]
        if isinstance(actual, bool) or not isinstance(actual, int) or actual < 1:
            raise ValueError(f"adapter info field {field!r} must be a positive integer")
        if actual < expected:
            raise ValueError(
                f"adapter limit {field!r} is below the connector minimum ({expected})"
            )
    return AdapterInfo(**value)
