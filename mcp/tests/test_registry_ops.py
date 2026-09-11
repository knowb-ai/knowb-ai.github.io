"""Contract tests for operator-invoked registry registration and enablement."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from knowb_org_index.config import load_registry
from knowb_org_index.registry_ops import (
    RegistryOpsError,
    register_project,
    set_project_enabled,
)

_COMMENTED_REGISTRY = """\
# Portfolio registry. Keep this comment.
version: 1
organization: knowb-ai
strict_manifests: false
allowed_roots: [.]
state_dir: ./state
projects:
  # An existing project, with its own note.
  - id: alpha
    name: Alpha
    path: ./alpha
    enabled: true
"""


class RegistryOpsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(prefix="knowb-registry-ops-")
        self.root = Path(self._directory.name).resolve()
        self.addCleanup(self._directory.cleanup)
        (self.root / "alpha" / "docs").mkdir(parents=True)
        (self.root / "beta" / "docs").mkdir(parents=True)
        self.registry = self.root / "registry.yml"
        self.registry.write_text(_COMMENTED_REGISTRY, encoding="utf-8")

    def _entries(self) -> list[dict]:
        data = yaml.safe_load(self.registry.read_text(encoding="utf-8"))
        return data["projects"]

    def _entry(self, project_id: str) -> dict:
        return next(item for item in self._entries() if item["id"] == project_id)

    def test_register_adds_a_disabled_entry_by_default(self) -> None:
        result = register_project(self.registry, self.root / "beta")

        self.assertTrue(result["changed"])
        self.assertEqual(result["project"]["id"], "beta")
        entry = self._entry("beta")
        self.assertIs(entry["enabled"], False)
        self.assertEqual((self.root / entry["path"]).resolve(), self.root / "beta")

    def test_register_can_enable_explicitly(self) -> None:
        register_project(self.registry, self.root / "beta", enabled=True)

        self.assertIs(self._entry("beta")["enabled"], True)

    def test_register_is_idempotent(self) -> None:
        register_project(self.registry, self.root / "beta")
        repeated = register_project(self.registry, self.root / "beta")

        self.assertFalse(repeated["changed"])
        self.assertEqual(repeated["reason"], "already registered")
        self.assertEqual(len([item for item in self._entries() if item["id"] == "beta"]), 1)

    def test_register_preserves_operator_comments(self) -> None:
        register_project(self.registry, self.root / "beta")

        content = self.registry.read_text(encoding="utf-8")
        self.assertIn("# Portfolio registry. Keep this comment.", content)
        self.assertIn("# An existing project, with its own note.", content)

    def test_register_derives_identity_from_the_repo_manifest(self) -> None:
        manifest_dir = self.root / "beta" / ".knowb"
        manifest_dir.mkdir()
        (manifest_dir / "project.yml").write_text(
            yaml.safe_dump({"version": 1, "id": "beta-service", "name": "Beta Service"}),
            encoding="utf-8",
        )

        result = register_project(self.registry, self.root / "beta")

        self.assertEqual(result["project"]["id"], "beta-service")
        self.assertEqual(self._entry("beta-service")["name"], "Beta Service")

    def test_register_rejects_paths_outside_allowed_roots(self) -> None:
        with tempfile.TemporaryDirectory(prefix="knowb-outside-") as outside:
            with self.assertRaises(RegistryOpsError) as caught:
                register_project(self.registry, outside)

        self.assertIn("allowed_roots", str(caught.exception))
        self.assertEqual(len(self._entries()), 1)

    def test_register_rejects_a_second_id_for_the_same_path(self) -> None:
        with self.assertRaises(RegistryOpsError):
            register_project(self.registry, self.root / "alpha", project_id="alpha-again")

    def test_dry_run_writes_nothing(self) -> None:
        before = self.registry.read_text(encoding="utf-8")
        result = register_project(self.registry, self.root / "beta", dry_run=True)

        self.assertTrue(result["changed"])
        self.assertTrue(result["dry_run"])
        self.assertIn("id: beta", result["entry"])
        self.assertEqual(self.registry.read_text(encoding="utf-8"), before)

    def test_enable_and_disable_flip_the_flag(self) -> None:
        register_project(self.registry, self.root / "beta")

        enabled = set_project_enabled(self.registry, "beta", enabled=True)
        self.assertTrue(enabled["changed"])
        self.assertIs(self._entry("beta")["enabled"], True)

        disabled = set_project_enabled(self.registry, "beta", enabled=False)
        self.assertTrue(disabled["changed"])
        self.assertIs(self._entry("beta")["enabled"], False)

    def test_enable_is_idempotent(self) -> None:
        repeated = set_project_enabled(self.registry, "alpha", enabled=True)

        self.assertFalse(repeated["changed"])
        self.assertEqual(repeated["reason"], "already enabled")

    def test_enable_inserts_a_missing_flag(self) -> None:
        self.registry.write_text(
            "version: 1\n"
            "organization: knowb-ai\n"
            "strict_manifests: false\n"
            "allowed_roots: [.]\n"
            "state_dir: ./state\n"
            "projects:\n"
            "  - id: alpha\n"
            "    path: ./alpha\n",
            encoding="utf-8",
        )

        set_project_enabled(self.registry, "alpha", enabled=False)

        self.assertIs(self._entry("alpha")["enabled"], False)

    def test_enable_rejects_an_unregistered_project(self) -> None:
        with self.assertRaises(RegistryOpsError):
            set_project_enabled(self.registry, "missing", enabled=True)

    def test_register_handles_an_empty_projects_list(self) -> None:
        self.registry.write_text(
            "version: 1\n"
            "organization: knowb-ai\n"
            "strict_manifests: false\n"
            "allowed_roots: [.]\n"
            "state_dir: ./state\n"
            "projects: []\n",
            encoding="utf-8",
        )

        register_project(self.registry, self.root / "beta")

        self.assertEqual([item["id"] for item in self._entries()], ["beta"])

    def test_register_keeps_trailing_top_level_keys_intact(self) -> None:
        self.registry.write_text(
            _COMMENTED_REGISTRY + "forbidden_paths:\n  - secret.md\n",
            encoding="utf-8",
        )

        register_project(self.registry, self.root / "beta")

        data = yaml.safe_load(self.registry.read_text(encoding="utf-8"))
        self.assertEqual(data["forbidden_paths"], ["secret.md"])
        self.assertEqual([item["id"] for item in data["projects"]], ["alpha", "beta"])

    def test_registered_project_loads_through_the_validating_reader(self) -> None:
        register_project(self.registry, self.root / "beta", enabled=True)

        registry = load_registry(self.registry)

        beta = next(item for item in registry.projects if item.id == "beta")
        self.assertTrue(beta.enabled)
        self.assertEqual(beta.path, self.root / "beta")

    def test_example_registries_are_never_modified(self) -> None:
        example = self.root / "local-projects.example.yml"
        example.write_text(_COMMENTED_REGISTRY, encoding="utf-8")

        with self.assertRaises(RegistryOpsError) as caught:
            register_project(example, self.root / "beta")

        self.assertIn("example registry", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
