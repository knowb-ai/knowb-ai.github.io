import unittest
from pathlib import Path

from knowb_org_index.config import load_registry


class ContractFixtureTests(unittest.TestCase):
    def test_knowledgehq_fixture_captures_public_compatibility_shape(self):
        fixture = Path(__file__).parent / "fixtures" / "knowledgehq-compatibility.yml"
        registry = load_registry(fixture)
        self.assertEqual(registry.organization, "knowb-ai")
        self.assertEqual(registry.state_dir, Path("/workspace/knowledgeHQ/.knowb-state"))
        self.assertEqual(
            [project.id for project in registry.projects],
            ["knowb-ai.github.io", "knowledgeHQ"],
        )
        self.assertTrue(registry.projects[0].enabled)
        self.assertTrue(registry.projects[1].sources)


if __name__ == "__main__":
    unittest.main()
