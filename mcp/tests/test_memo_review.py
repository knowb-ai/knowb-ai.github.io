"""Formal memo review, citation validation, and non-persistence contract tests."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import yaml

from knowb_org_index.service import OrgIndexService
from support import isolated_registry


class MemoReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = isolated_registry(self.root)
        self.source = self.root / "project" / "docs" / "direction.md"
        self.source.write_text("# Direction\nTrusted source text.\n", encoding="utf-8")
        self.service = OrgIndexService(self.config)

    def review(self, **changes):
        inputs = {
            "project": "project",
            "title": "Memo review contract",
            "memo_kind": "plan",
            "draft": "A reviewed draft with a clear conclusion.\n",
            "purpose": "Define the formal review and approval workflow.",
            "scope": "The connector review gate and its caller-owned recording step.",
            "next_actions": ["Implement the review tool", "Add contract documentation"],
            "open_questions_reviewed": True,
            "related_paths": ["docs/direction.md"],
            "external_sources": ["https://example.com/research"],
        }
        inputs.update(changes)
        return self.service.review_memo(**inputs)

    def test_ready_result_has_deterministic_digest_and_exact_citations(self):
        first = self.review()
        second = self.review(draft="  A reviewed draft with a clear conclusion.\r\n")

        self.assertEqual(first["status"], "ready_for_user_approval")
        self.assertTrue(first["approval_required"])
        self.assertFalse(first["draft_persisted"])
        self.assertEqual(first["review_signature"]["digest"], second["review_signature"]["digest"])
        citation = first["sources"]["local"][0]
        self.assertEqual(citation["path"], "docs/direction.md")
        self.assertEqual(citation["title"], "Direction")
        self.assertTrue(citation["uri"].startswith("knowb://project/project/doc/"))
        self.assertEqual(len(citation["content_hash"]), 64)
        self.assertEqual(first["sources"]["external"][0]["validation"], "URL syntax only; not fetched")

    def test_editing_memo_or_source_changes_digest(self):
        original = self.review()["review_signature"]["digest"]
        self.assertNotEqual(original, self.review(draft="An edited draft.")["review_signature"]["digest"])
        self.source.write_text("# Direction\nUpdated trusted source text with different length.\n", encoding="utf-8")
        self.assertNotEqual(original, self.review()["review_signature"]["digest"])

    def test_missing_fields_and_open_questions_return_refinement_questions(self):
        result = self.review(
            title="", purpose="", scope="", next_actions=[], open_questions_reviewed=False,
        )

        self.assertEqual(result["status"], "needs_refinement")
        failed = {item["name"] for item in result["checklist"] if item["status"] != "passed"}
        self.assertTrue({"title", "purpose", "scope", "next_actions", "open_questions_reviewed"} <= failed)
        self.assertGreaterEqual(len(result["refinement_questions"]), 5)

    def test_kind_size_and_external_url_are_checked(self):
        too_large = "x" * 65_537
        result = self.review(memo_kind="story", draft=too_large, external_sources=["file:///etc/passwd"])

        self.assertEqual(result["status"], "needs_refinement")
        failed = {item["name"] for item in result["checklist"] if item["status"] != "passed"}
        self.assertTrue({"memo_kind", "draft", "external_sources"} <= failed)
        self.assertEqual(len(result["sources"]["external_errors"]), 1)

    def test_unallowlisted_traversal_and_symlink_paths_fail(self):
        outside = self.root / "outside.md"
        outside.write_text("# Outside\nprivate", encoding="utf-8")
        linked = self.source.parent / "escape.md"
        linked.symlink_to(outside)
        (self.root / "project" / "internal").mkdir()
        (self.root / "project" / "internal" / "secret.md").write_text("# Secret", encoding="utf-8")

        result = self.review(related_paths=["../outside.md", "docs/missing.md", "docs/escape.md", "internal/secret.md"])

        self.assertEqual(result["status"], "needs_refinement")
        self.assertEqual(result["sources"]["local"], [])
        self.assertEqual(len(result["sources"]["local_errors"]), 4)

    def test_inactive_project_fails_even_without_related_paths(self):
        data = yaml.safe_load(self.config.read_text(encoding="utf-8"))
        data["projects"][0]["enabled"] = False
        self.config.write_text(yaml.safe_dump(data), encoding="utf-8")
        self.service = OrgIndexService(self.config)
        result = self.review(related_paths=[])
        self.assertEqual(result["status"], "needs_refinement")
        self.assertIn("project_access", {item["name"] for item in result["checklist"]})

    def test_review_does_not_store_draft_or_create_pending_github_actions(self):
        marker = "unique-memo-review-draft-marker"
        result = self.review(draft=marker, related_paths=[])
        self.assertEqual(result["status"], "ready_for_user_approval")
        with sqlite3.connect(self.service.index.path) as connection:
            pending_count = connection.execute("SELECT COUNT(*) FROM pending_actions").fetchone()[0]
            stored_draft = connection.execute(
                "SELECT COUNT(*) FROM documents WHERE content LIKE ?", (f"%{marker}%",)
            ).fetchone()[0]
        self.assertEqual(pending_count, 0)
        self.assertEqual(stored_draft, 0)


if __name__ == "__main__":
    unittest.main()
