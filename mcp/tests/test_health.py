import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from knowb_org_index.config import load_registry
from knowb_org_index.design_assets import DesignAssetError
from knowb_org_index.github_ops import GitHubError
from knowb_org_index.service import OrgIndexService


class HealthAndCapabilityTests(unittest.TestCase):
    def _config(self, root: Path, *, github_enabled: bool = True) -> Path:
        project = root / "project"
        (project / "docs").mkdir(parents=True)
        config = root / "registry.yml"
        config.write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "organization": "knowb-ai",
                    "strict_manifests": False,
                    "allowed_roots": [str(root)],
                    "state_dir": str(root / "state"),
                    "capabilities": {"github": {"enabled": github_enabled}},
                    "projects": [
                        {
                            "id": "project",
                            "path": str(project),
                            "enabled": True,
                            "knowledge": {"roots": [{"path": "docs"}]},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return config

    def test_doctor_reports_core_health_and_optional_capabilities(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = self._config(root)
            bridge = Path(__file__).resolve().parents[1] / "okf-bridge/target/release/knowb-okf-bridge"
            if not bridge.is_file():
                self.skipTest("build the release bridge for doctor integration")
            with patch.dict(os.environ, {"KNOWB_OKF_BRIDGE": str(bridge)}, clear=False):
                report = OrgIndexService(config).doctor()
            self.assertTrue(report["ok"], report)
            self.assertTrue(report["config"]["status"] == "ok")
            self.assertTrue(report["state"]["database_open"])
            self.assertTrue(report["search"]["self_test"])
            self.assertIn("github", report["capabilities"])

    def test_doctor_fails_core_when_adapter_is_incompatible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = self._config(root)
            missing = root / "missing-bridge"
            with patch.dict(os.environ, {"KNOWB_OKF_BRIDGE": str(missing)}, clear=False):
                report = OrgIndexService(config).doctor()
            self.assertFalse(report["ok"])
            self.assertFalse(report["search"]["available"])

    def test_disabled_github_blocks_every_public_operation_before_subprocess(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            service = OrgIndexService(self._config(root, github_enabled=False))
            service.github._run = Mock(side_effect=AssertionError("gh must not run"))
            with self.assertRaisesRegex(GitHubError, "disabled"):
                service.github.list_work()
            with self.assertRaisesRegex(GitHubError, "disabled"):
                service.github.get_ticket("knowb/repo", 1)
            with self.assertRaisesRegex(GitHubError, "disabled"):
                service.github.propose_ticket_create(repository="knowb/repo", title="x")

    def test_disabled_github_blocks_design_vault_before_identity_or_oauth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = self._config(root, github_enabled=False)
            data = yaml.safe_load(config.read_text(encoding="utf-8"))
            data["design_assets"] = {
                "enabled": True,
                "google_drive_folder_id": "folder-id",
                "allowed_google_email": "owner@example.com",
                "allowed_github_logins": ["owner"],
                "allowed_upload_roots": [str(root / "project")],
            }
            config.write_text(yaml.safe_dump(data), encoding="utf-8")
            service = OrgIndexService(config)
            service.design_assets._github_identity = Mock(
                side_effect=AssertionError("identity must not run")
            )
            with self.assertRaisesRegex(DesignAssetError, "disabled"):
                service.design_assets.verify()


if __name__ == "__main__":
    unittest.main()
