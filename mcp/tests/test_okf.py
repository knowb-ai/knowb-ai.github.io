"""Contract and real pinned-okf-rs retrieval tests."""
import asyncio
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from knowb_org_index.index import IndexError
from knowb_org_index.okf import diagnostics
from knowb_org_index.service import OrgIndexService


class OkfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.projects = []
        for name in ("alpha", "beta"):
            root = self.root / name
            (root / "docs").mkdir(parents=True)
            self.projects.append({"id": name, "path": str(root), "knowledge": {
                "roots": [{"path": "docs", "include": ["**/*.md"], "exclude": ["private/**"]}]
            }})
        self.config = self.root / "registry.yml"
        self.save_config()

    def save_config(self):
        self.config.write_text(yaml.safe_dump({
            "version": 1, "organization": "knowb-ai", "strict_manifests": False,
            "allowed_roots": [str(self.root)], "state_dir": str(self.root / "state"),
            "projects": self.projects,
        }))

    def document(self, project, name, body):
        path = self.root / project / "docs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        return path

    def service(self):
        return OrgIndexService(self.config)

    def test_snapshot_is_scoped_and_original_citation_survives(self):
        original = self.document("alpha", "index.md", "# Navigation\nbodyonlyword")
        self.document("alpha", "private/secret.md", "secretword")
        self.document("beta", "other.md", "otherprojectword")
        (original.parent / "link.md").symlink_to(original)
        original.parent.joinpath("linked").symlink_to(original.parent, target_is_directory=True)

        def adapter(_args, **kwargs):
            request = json.loads(kwargs["input"])
            files = list(Path(request["bundle"]).glob("*.md"))
            self.assertEqual(request["documents"], 1)
            self.assertEqual(len(files), 2)
            concept = next(path for path in files if path.name != "index.md")
            self.assertIn("bodyonlyword", concept.read_text())
            self.assertNotIn("otherprojectword", concept.read_text())
            return subprocess.CompletedProcess([], 0, json.dumps({
                "protocol": 1, "results": [{"id": concept.stem, "score": 2.5}]
            }), "")

        service = self.service()
        with patch("knowb_org_index.okf.diagnostics", return_value={"available": True}), \
             patch("knowb_org_index.okf.subprocess.run", side_effect=adapter):
            hits = service.search_knowledge("bodyonlyword", projects=["ALPHA"])["results"]
        self.assertEqual(hits[0]["source_path"], str(original))
        self.assertEqual(hits[0]["path"], "docs/index.md")
        self.assertEqual(hits[0]["backend"], "okf-rs")
        self.assertFalse(list((self.root / "state").glob("okf-*")))

    def test_disabled_and_empty_selection_cannot_return_cached_content(self):
        self.document("alpha", "one.md", "# Document\nconfidential")
        self.service().refresh_index()
        self.projects[0]["enabled"] = False
        self.save_config()
        service = self.service()
        self.assertEqual(service.search_knowledge("confidential", projects=["alpha"])["results"], [])
        self.assertEqual(service.search_knowledge("confidential", projects=[])["results"], [])
        with self.assertRaises(IndexError):
            service.read_project_doc("alpha", "docs/one.md")

    def test_missing_adapter_fails_without_sqlite_fallback(self):
        self.document("alpha", "one.md", "# Document\nneedle")
        with patch.dict(os.environ, {"KNOWB_OKF_BRIDGE": str(self.root / "missing")}):
            with self.assertRaisesRegex(IndexError, "adapter is missing"):
                self.service().search_knowledge("needle")

    def test_search_migration_preserves_confirmation_ledger(self):
        service = self.service()
        pending = service.index.create_pending_action(
            kind="test", payload={"value": 1}, preview={"title": "Existing proposal"},
            idempotency_key="migration-test",
        )
        service.refresh_index()
        reopened = self.service().index
        self.assertEqual(reopened.get_pending_action(pending["token"]), pending)
        _, claimed = reopened.claim_pending_action(pending["token"])
        self.assertTrue(claimed)
        _, claimed_again = self.service().index.claim_pending_action(pending["token"])
        self.assertFalse(claimed_again)

    def test_bad_adapter_response_and_timeout_are_errors_and_clean_up(self):
        self.document("alpha", "one.md", "# Document\nneedle")
        service = self.service()
        for response in ("not-json", '{"protocol":1,"results":[{"id":"outside","score":1}]}'):
            with patch("knowb_org_index.okf.diagnostics", return_value={"available": True}), \
                 patch("knowb_org_index.okf.subprocess.run", return_value=subprocess.CompletedProcess([], 0, response, "")):
                with self.assertRaises(IndexError):
                    service.search_knowledge("needle")
        with patch("knowb_org_index.okf.diagnostics", return_value={"available": True}), \
             patch("knowb_org_index.okf.subprocess.run", side_effect=subprocess.TimeoutExpired("adapter", 60)):
            with self.assertRaisesRegex(IndexError, "timed out"):
                service.search_knowledge("needle")
        self.assertFalse(list((self.root / "state").glob("okf-*")))

    @unittest.skipUnless(diagnostics()["available"], "build mcp/okf-bridge for real-engine tests")
    def test_mcp_search_and_read_contract_with_real_backend(self):
        from mcp import Client
        from knowb_org_index.server import create_server

        self.document("alpha", "one.md", "# Mission\nprotocolneedle")

        async def exercise():
            async with Client(create_server(self.config)) as client:
                result = await client.call_tool("search_knowledge", {
                    "query": "protocolneedle", "projects": ["alpha"], "limit": 1,
                })
                self.assertFalse(result.is_error)
                hit = result.structured_content["results"][0]
                self.assertEqual(hit["backend"], "okf-rs")
                read = await client.call_tool("read_project_doc", {
                    "project": hit["project"], "path": hit["path"],
                })
                self.assertIn("protocolneedle", read.structured_content["content"])

        asyncio.run(exercise())

    @unittest.skipUnless(diagnostics()["available"], "build mcp/okf-bridge for real-engine tests")
    def test_real_engine_full_body_unicode_limits_and_freshness(self):
        original = self.document("alpha", "résumé with spaces.md", "# A title\n" + "ordinary " * 100 + "quasarunique")
        self.document("beta", "one.md", "# Another\nquasarunique")
        service = self.service()
        hits = service.search_knowledge("quasarunique", projects=["alpha"])["results"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source_path"], str(original))
        self.assertIn("quasarunique", hits[0]["excerpt"])
        self.assertEqual(len(service.search_knowledge("quasarunique", limit=1)["results"]), 1)
        original.write_text("# Changed\nreplacementunique")
        self.assertEqual(service.search_knowledge("quasarunique", projects=["alpha"])["results"], [])
        self.assertEqual(len(service.search_knowledge("replacementunique", projects=["alpha"])["results"]), 1)
        original.unlink()
        self.assertEqual(service.search_knowledge("replacementunique", projects=["alpha"])["results"], [])


if __name__ == "__main__":
    unittest.main()
