"""Installed-artifact and portable-folder acceptance tests.

These tests run against an installed wheel in an isolated venv with no
repository checkout, no Cargo, and no Git on PATH. They prove the package is
self-contained: the bundled adapter runs, a freshly onboarded folder serves
search, and the CLI exposes the new init/client-config/health commands.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MCP = ROOT / "mcp"
WHEEL = os.environ.get("KNOWB_PORTABLE_WHEEL", "")
VENV_PY = os.environ.get("KNOWB_PORTABLE_PYTHON", sys.executable)
VENV_BIN = os.environ.get("KNOWB_PORTABLE_VENV_BIN", "")


def _run(args, *, env=None, cwd=None, timeout=120):
    return subprocess.run(
        [VENV_PY, "-m", "knowb_org_index.cli", *args],
        capture_output=True, text=True, env=env, cwd=cwd, timeout=timeout,
    )


def _clean_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in (
        "KNOWB_ORG_ROOT", "KNOWB_ORG_CONFIG", "PYTHONPATH", "CARGO_HOME",
        "RUSTUP_HOME", "KNOWB_OKF_BRIDGE",
    )}
    env["PATH"] = "/usr/bin:/bin"
    return env


class PortableInstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WHEEL:
            raise unittest.SkipTest("set KNOWB_PORTABLE_WHEEL to a built platform wheel")
        if not Path(WHEEL).is_file():
            raise unittest.SkipTest(f"wheel not found: {WHEEL}")
        cls.root = Path(tempfile.mkdtemp(prefix="knowb-portable-"))
        (cls.root / "docs").mkdir(parents=True)
        (cls.root / "docs" / "index.md").write_text(
            "# Plain Project\nThis is a plain folder with no git, no manifest, and no identity.\n",
            encoding="utf-8",
        )
        cls.env = _clean_env()
        cls.env["KNOWB_ORG_CONFIG"] = str(cls.root / ".knowb" / "connector.yml")
        result = _run(["init", str(cls.root), "--name", "Plain Project", "--id", "plain-project"], env=cls.env)
        if result.returncode != 0:
            raise RuntimeError(f"init failed:\n{result.stderr}\n{result.stdout}")
        cls.config_path = cls.root / ".knowb" / "connector.yml"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_init_creates_self_contained_folder(self):
        self.assertTrue((self.root / ".knowb" / "project.yml").is_file())
        self.assertTrue((self.root / ".knowb" / "connector.yml").is_file())
        self.assertTrue((self.root / "knowb.json").is_file())

    def test_client_config_is_portable(self):
        config = json.loads((self.root / "knowb.json").read_text())
        server = config["mcpServers"]["knowb-org-index"]
        self.assertEqual(server["command"], "knowb-org-mcp")
        self.assertEqual(
            os.path.realpath(server["env"]["KNOWB_ORG_CONFIG"]),
            os.path.realpath(str(self.config_path)),
        )

    def test_status_lists_onboarded_project(self):
        result = _run(["--config", str(self.config_path), "status"], env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["summary"]["registered"], 1)
        self.assertEqual(data["projects"][0]["id"], "plain-project")

    def test_health_reports_adapter_and_capabilities(self):
        result = _run(["--config", str(self.config_path), "health"], env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("adapter", data)
        self.assertIn("capabilities", data)
        self.assertIn("boundaries", data["capabilities"])

    def test_search_uses_bundled_adapter(self):
        result = _run(
            ["--config", str(self.config_path), "search", "plain folder"],
            env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["results"][0]["backend"], "okf-rs")
        self.assertTrue(
            os.path.realpath(data["results"][0]["source_path"]).startswith(
                os.path.realpath(str(self.root))
            )
        )

    def test_read_returns_allowlisted_document(self):
        result = _run(
            ["--config", str(self.config_path), "read", "plain-project", "docs/index.md"],
            env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["path"], "docs/index.md")

    def test_read_rejects_unindexed_path(self):
        result = _run(
            ["--config", str(self.config_path), "read", "plain-project", "secret.md"],
            env=self.env,
        )
        self.assertNotEqual(result.returncode, 0)


class PortableMissingAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WHEEL:
            raise unittest.SkipTest("set KNOWB_PORTABLE_WHEEL to a built platform wheel")
        cls.root = Path(tempfile.mkdtemp(prefix="knowb-portable-"))
        (cls.root / "docs").mkdir(parents=True)
        (cls.root / "docs" / "index.md").write_text("# Missing Adapter\n", encoding="utf-8")
        cls.env = _clean_env()
        cls.env["KNOWB_OKF_BRIDGE"] = "/tmp/definitely-not-an-adapter"
        result = _run(["init", str(cls.root), "--id", "missing-adapter"], env=cls.env)
        if result.returncode != 0:
            raise RuntimeError(f"init failed:\n{result.stderr}\n{result.stdout}")
        cls.config_path = cls.root / ".knowb" / "connector.yml"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_health_reports_unavailable_adapter(self):
        result = _run(["--config", str(self.config_path), "health"], env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertFalse(data["adapter"]["available"])

    def test_search_fails_without_silent_fallback(self):
        result = _run(
            ["--config", str(self.config_path), "search", "missing adapter"],
            env=self.env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("adapter", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
