import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from knowb_org_index.config import ConfigurationError, load_registry
from knowb_org_index.env import EnvironmentFileError, load_dotenv
from knowb_org_index.service import OrgIndexService


class PortableRuntimeTests(unittest.TestCase):
    def _config(self, root: Path, name: str, *, state_dir: str | None = None) -> Path:
        project = root / f"{name}-project"
        (project / "docs").mkdir(parents=True)
        data = {
            "version": 1,
            "organization": "knowb-ai",
            "strict_manifests": False,
            "allowed_roots": [str(root)],
            "projects": [
                {
                    "id": name,
                    "path": str(project),
                    "enabled": True,
                    "knowledge": {"roots": [{"path": "docs"}]},
                }
            ],
        }
        if state_dir is not None:
            data["state_dir"] = state_dir
        path = root / f"{name}.yml"
        path.write_text(yaml.safe_dump(data), encoding="utf-8")
        return path

    def test_explicit_config_does_not_scan_or_require_checkout_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = self._config(root, "portable")
            with patch.dict(
                os.environ,
                {
                    "KNOWB_ORG_ROOT": str(root / "not-a-checkout"),
                    "KNOWB_ENV_FILE": "",
                    "KNOWB_STATE_ROOT": str(root / "state-root"),
                },
                clear=False,
            ):
                registry = load_registry(config)
                self.assertEqual(registry.repository_root, root)
                self.assertEqual(registry.projects[0].id, "portable")
                service = OrgIndexService(config)
                self.assertEqual(service.registry.config_path, config)

    def test_default_state_is_stable_per_canonical_config_and_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            first = self._config(root, "first")
            second = self._config(root, "second")
            with patch.dict(os.environ, {"KNOWB_STATE_ROOT": str(root / "state-root")}, clear=False):
                first_registry = load_registry(first)
                second_registry = load_registry(second)
                self.assertNotEqual(first_registry.state_dir, second_registry.state_dir)
                self.assertEqual(first_registry.state_dir, load_registry(first).state_dir)
                self.assertTrue(str(first_registry.state_dir).startswith(str(root / "state-root")))

    def test_explicit_env_file_is_required_and_project_env_is_not_implicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with patch.dict(os.environ, {"KNOWB_ENV_FILE": str(root / "missing.env")}, clear=False):
                with self.assertRaisesRegex(EnvironmentFileError, "does not exist"):
                    load_dotenv()
            (root / ".env").write_text("LEAK_MARKER=from-project\n", encoding="utf-8")
            with patch.dict(os.environ, {"KNOWB_ENV_FILE": ""}, clear=False):
                load_dotenv(legacy_checkout_root=None)
            self.assertNotEqual(os.environ.get("LEAK_MARKER"), "from-project")

    def test_capability_policy_defaults_on_and_can_disable_github(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            config = self._config(root, "disabled")
            data = yaml.safe_load(config.read_text(encoding="utf-8"))
            data["capabilities"] = {"github": {"enabled": False}}
            config.write_text(yaml.safe_dump(data), encoding="utf-8")
            registry = load_registry(config)
            self.assertFalse(registry.capabilities.github_enabled)
            data.pop("capabilities")
            config.write_text(yaml.safe_dump(data), encoding="utf-8")
            self.assertTrue(load_registry(config).capabilities.github_enabled)


if __name__ == "__main__":
    unittest.main()
