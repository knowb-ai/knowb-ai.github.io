import json
import unittest

from knowb_org_index.remix import build_design_remix
from knowb_org_index.scaffold import build_repository_blueprint, render_repository_files


class RepositoryScaffoldTests(unittest.TestCase):
    def test_new_repository_includes_knowb_connector_contract(self):
        remix = build_design_remix(
            project_name="Atlas Companion",
            purpose="help teams navigate durable project context",
            audience="builders and operators",
            personality="clear, calm, precise",
            desired_feeling="oriented and ready",
            visual_metaphor="a readable star chart",
            content_priority="the next useful decision",
            interface_mode="internal",
            surfaces=["workspace", "decision detail", "mobile review"],
            avoid=["opaque automation"],
            require_complete=True,
        )
        blueprint = build_repository_blueprint(
            name="atlas-companion",
            display_name="Atlas Companion",
            purpose="help teams navigate durable project context",
            audience="builders and operators",
            primary_users="project builders",
            strategic_direction="become the trusted context layer for project work",
            success_criteria="teams make fewer context-blind decisions",
            brand_tone="clear, calm, precise",
            visibility="private",
            interface_mode="internal",
            tech_stack=["Python"],
            design_remix=remix["brief"],
            remix_digest=remix["remix_digest"],
            require_complete=True,
        )
        files = render_repository_files(blueprint["brief"])

        self.assertIn(".knowb/project.yml", files)
        self.assertIn(".knowb/mcp-client.example.json", files)
        self.assertIn("docs/operations/knowb-mcp-validation.md", files)
        self.assertIn("KnowB MCP and KnowledgeHQ", files["AGENTS.md"])
        self.assertIn("doctor", files["docs/operations/knowb-mcp-validation.md"])
        self.assertIn("atlas-companion", files["AGENTS.md"])

        client = json.loads(files[".knowb/mcp-client.example.json"])
        server = client["mcpServers"]["knowb-ai-portfolio"]
        self.assertEqual(server["command"], "uv")
        self.assertTrue(any("knowb-ai.github.io/mcp" in item for item in server["args"]))
        self.assertTrue(
            any("knowledgeHQ/.knowb/knowb-ai-portfolio.yml" in item for item in server["args"])
        )
        self.assertIn(".knowb-state/", files[".gitignore"])


if __name__ == "__main__":
    unittest.main()
