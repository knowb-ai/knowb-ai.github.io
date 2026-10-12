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


_ANCHORED_REGISTRY = """\
version: 1
organization: knowb-ai
strict_manifests: false
allowed_roots: [.]
state_dir: ./state
default_knowledge: &default_knowledge
  roots:
    - path: docs
      include: ["**/*.md"]
projects:
  # Operator note that must survive.
  - id: alpha
    name: Alpha
    path: ./alpha
    enabled: false
    lifecycle: unclassified
    knowledge: *default_knowledge
  - id: beta
    path: ./beta
    enabled: true
    knowledge: *default_knowledge
"""


class RegistryOpsYamlFeaturesTest(unittest.TestCase):
    """Registries that use anchors, aliases, merge keys, and nested keys.

    The portfolio registry shares one knowledge policy through an anchor and
    nests an `enabled` flag under `repository_sync`, so enable and disable must
    handle both without touching the wrong key.
    """

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(prefix="knowb-registry-yaml-")
        self.root = Path(self._directory.name).resolve()
        self.addCleanup(self._directory.cleanup)
        for name in ("alpha", "beta"):
            (self.root / name / "docs").mkdir(parents=True)
        self.registry = self.root / "registry.yml"

    def _write(self, text: str) -> None:
        self.registry.write_text(text, encoding="utf-8")

    def _text(self) -> str:
        return self.registry.read_text(encoding="utf-8")

    def _entry(self, project_id: str) -> dict:
        data = yaml.safe_load(self._text())
        return next(item for item in data["projects"] if item["id"] == project_id)

    def test_enable_works_when_an_entry_uses_an_alias(self) -> None:
        self._write(_ANCHORED_REGISTRY)

        result = set_project_enabled(self.registry, "alpha", enabled=True)

        self.assertTrue(result["changed"])
        self.assertIs(self._entry("alpha")["enabled"], True)

    def test_disable_works_when_an_entry_uses_an_alias(self) -> None:
        self._write(_ANCHORED_REGISTRY)

        set_project_enabled(self.registry, "beta", enabled=False)

        self.assertIs(self._entry("beta")["enabled"], False)

    def test_only_the_toggled_line_changes(self) -> None:
        self._write(_ANCHORED_REGISTRY)
        before = self._text().splitlines()

        set_project_enabled(self.registry, "alpha", enabled=True)

        after = self._text().splitlines()
        changed = [(a, b) for a, b in zip(before, after) if a != b]
        self.assertEqual(len(before), len(after))
        self.assertEqual(changed, [("    enabled: false", "    enabled: true")])
        self.assertIn("  # Operator note that must survive.", after)

    def test_disable_then_enable_restores_the_file_exactly(self) -> None:
        self._write(_ANCHORED_REGISTRY)

        set_project_enabled(self.registry, "beta", enabled=False)
        set_project_enabled(self.registry, "beta", enabled=True)

        self.assertEqual(self._text(), _ANCHORED_REGISTRY)

    def test_an_entry_that_merges_a_shared_mapping_can_be_toggled(self) -> None:
        self._write(
            "version: 1\n"
            "organization: knowb-ai\n"
            "strict_manifests: false\n"
            "allowed_roots: [.]\n"
            "state_dir: ./state\n"
            "defaults: &defaults\n"
            "  lifecycle: active\n"
            "projects:\n"
            "  - <<: *defaults\n"
            "    id: alpha\n"
            "    path: ./alpha\n"
            "    enabled: false\n"
        )

        set_project_enabled(self.registry, "alpha", enabled=True)

        self.assertIs(self._entry("alpha")["enabled"], True)

    def test_a_nested_enabled_key_is_not_mistaken_for_the_entrys_own(self) -> None:
        """A nested flag listed first used to be flipped instead of the entry's."""

        self._write(
            "version: 1\n"
            "organization: knowb-ai\n"
            "strict_manifests: false\n"
            "allowed_roots: [.]\n"
            "state_dir: ./state\n"
            "projects:\n"
            "  - id: alpha\n"
            "    path: ./alpha\n"
            "    repository_sync:\n"
            "      enabled: false\n"
            "      repository: knowb-ai/alpha\n"
            "    enabled: false\n"
        )

        set_project_enabled(self.registry, "alpha", enabled=True)

        entry = self._entry("alpha")
        self.assertIs(entry["enabled"], True)
        self.assertIs(entry["repository_sync"]["enabled"], False)

    def test_an_entry_with_only_a_nested_flag_gets_its_own_key(self) -> None:
        self._write(
            "version: 1\n"
            "organization: knowb-ai\n"
            "strict_manifests: false\n"
            "allowed_roots: [.]\n"
            "state_dir: ./state\n"
            "projects:\n"
            "  - id: alpha\n"
            "    path: ./alpha\n"
            "    repository_sync:\n"
            "      enabled: true\n"
            "      repository: knowb-ai/alpha\n"
        )

        set_project_enabled(self.registry, "alpha", enabled=False)

        entry = self._entry("alpha")
        self.assertIs(entry["enabled"], False)
        self.assertIs(entry["repository_sync"]["enabled"], True)

    def test_an_inline_comment_on_the_flag_survives(self) -> None:
        self._write(_ANCHORED_REGISTRY.replace("enabled: false", "enabled: false  # waiting on review"))

        set_project_enabled(self.registry, "alpha", enabled=True)

        self.assertIn("    enabled: true  # waiting on review", self._text())

    def test_the_flag_as_the_first_key_is_edited_not_duplicated(self) -> None:
        self._write(
            "version: 1\n"
            "organization: knowb-ai\n"
            "strict_manifests: false\n"
            "allowed_roots: [.]\n"
            "state_dir: ./state\n"
            "projects:\n"
            "  - enabled: false\n"
            "    id: alpha\n"
            "    path: ./alpha\n"
        )

        set_project_enabled(self.registry, "alpha", enabled=True)

        self.assertEqual(self._text().count("enabled:"), 1)
        self.assertIs(self._entry("alpha")["enabled"], True)

    def test_a_missing_project_is_still_reported(self) -> None:
        self._write(_ANCHORED_REGISTRY)

        with self.assertRaises(RegistryOpsError):
            set_project_enabled(self.registry, "missing", enabled=True)
