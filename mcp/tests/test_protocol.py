import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from knowb_org_index.okf import AdapterError, adapter_info
from knowb_org_index.protocol import (
    ADAPTER_VERSION,
    MAX_QUERY_BYTES,
    MAX_REQUEST_BYTES,
    MAX_RESULTS,
    OKF_RS_REVISION,
    parse_adapter_info,
)


def _payload(**overrides):
    payload = {
        "protocol": 1,
        "adapter_version": ADAPTER_VERSION,
        "okf_rs_revision": OKF_RS_REVISION,
        "build_target": "aarch64-apple-darwin",
        "max_request_bytes": MAX_REQUEST_BYTES,
        "max_query_bytes": MAX_QUERY_BYTES,
        "max_results": MAX_RESULTS,
    }
    payload.update(overrides)
    return payload


class ProtocolTests(unittest.TestCase):
    def test_parse_info_accepts_contract(self):
        info = parse_adapter_info(_payload())
        self.assertEqual(info.build_target, "aarch64-apple-darwin")

    def test_parse_info_rejects_protocol_fields_and_limits(self):
        for overrides in (
            {"protocol": 2},
            {"max_results": 1},
            {"max_query_bytes": MAX_QUERY_BYTES - 1},
            {"adapter_version": ""},
            {"unexpected": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    parse_adapter_info(_payload(**overrides))

    def test_adapter_info_reports_typed_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "bridge"
            binary.write_text("#!/bin/sh\nprintf '%s' not-json\n", encoding="utf-8")
            binary.chmod(0o755)
            with self.assertRaisesRegex(AdapterError, "invalid handshake"):
                adapter_info(str(binary))

        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "bridge"
            binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            binary.chmod(0o755)
            with patch(
                "knowb_org_index.okf.subprocess.run",
                side_effect=subprocess.TimeoutExpired("bridge", 5),
            ):
                with self.assertRaisesRegex(AdapterError, "handshake timed out"):
                    adapter_info(str(binary))


if __name__ == "__main__":
    unittest.main()
