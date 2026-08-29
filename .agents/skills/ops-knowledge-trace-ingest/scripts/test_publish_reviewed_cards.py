#!/usr/bin/env python3

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import publish_reviewed_cards as publisher
from publish_reviewed_cards import publish
from validate_review_receipt import build_subject

REPO = Path(__file__).resolve().parents[4]


def _card() -> str:
    return """---
type: "Runbook"
title: "审核发布卡"
description: "验证审核后发布器的最小 Runbook 卡片。"
tags: [task.debugging, topic.compilation]
status: stable
sources: []
created_at: '2026-08-28T00:00:00Z'
updated_at: '2026-08-28T00:00:00Z'
platforms: [a3]
---

# 审核发布卡
"""


class PublishReviewedCardsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(REPO / "governance", self.root / "governance")
        self.cards = self.root / "staged-cards"
        (self.cards / "precision").mkdir(parents=True)
        self.staged = self.cards / "precision/card.md"
        self.staged.write_text(_card(), encoding="utf-8")
        self.ledger = self.root / "ledger.json"
        self.ledger.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "operation": "new",
                            "status": "published",
                            "target_slug": "card",
                            "target_path": "precision/card.md",
                            "evidence_audit": {
                                "mode": "trace_snapshot",
                                "result": "pass",
                                "trace_snapshot": {
                                    "mechanism_artifacts": [
                                        {"verbatim_verified": True}
                                    ]
                                },
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.receipt = self.root / "receipt.json"
        self.receipt.write_text(
            json.dumps(
                {
                    **build_subject(self.ledger, self.cards),
                    "verdict": "PASS",
                    "findings": [],
                    "summary": "review passed",
                    "reviewer": "subagent:test-reviewer",
                    "attestation": "agent-runtime-message",
                    "reviewed_at": "2026-08-28T08:00:00Z",
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_publish_and_check_bind_final_bytes(self):
        result = publish(
            self.ledger, self.cards, self.receipt, self.root, check_only=False
        )
        self.assertEqual(1, result["cards"])
        destination = self.root / "knowledge/ops/ascendc/runbooks/precision/card.md"
        self.assertEqual(self.staged.read_bytes(), destination.read_bytes())
        checked = publish(
            self.ledger, self.cards, self.receipt, self.root, check_only=True
        )
        self.assertEqual("check", checked["mode"])

    def test_staged_mutation_fails_before_write(self):
        self.staged.write_text("# Mutated\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "valid PASS receipt"):
            publish(self.ledger, self.cards, self.receipt, self.root)
        destination = self.root / "knowledge/ops/ascendc/runbooks/precision/card.md"
        self.assertFalse(destination.exists())

    def test_pending_audit_cannot_publish(self):
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        ledger["entries"][0]["evidence_audit"]["result"] = "pending"
        self.ledger.write_text(json.dumps(ledger), encoding="utf-8")
        self.receipt.write_text(
            json.dumps(
                {
                    **build_subject(self.ledger, self.cards),
                    "verdict": "PASS",
                    "findings": [],
                    "summary": "review passed",
                    "reviewer": "subagent:test-reviewer",
                    "attestation": "agent-runtime-message",
                    "reviewed_at": "2026-08-28T08:00:00Z",
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "audit is not approved"):
            publish(self.ledger, self.cards, self.receipt, self.root)

    def test_invalid_staged_frontmatter_cannot_publish(self):
        invalid = _card().replace(
            "platforms: [a3]\n", "platforms: [a3]\nreproduce_count: 2\n"
        )
        self.staged.write_text(invalid, encoding="utf-8")
        self.receipt.write_text(
            json.dumps(
                {
                    **build_subject(self.ledger, self.cards),
                    "verdict": "PASS",
                    "findings": [],
                    "summary": "review passed",
                    "reviewer": "subagent:test-reviewer",
                    "attestation": "agent-runtime-message",
                    "reviewed_at": "2026-08-28T08:00:00Z",
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "violates machine contract"):
            publish(self.ledger, self.cards, self.receipt, self.root)
        destination = self.root / "knowledge/ops/ascendc/runbooks/precision/card.md"
        self.assertFalse(destination.exists())

    def test_publish_uses_the_same_frozen_bytes_validated_by_receipt(self):
        reviewed_bytes = self.staged.read_bytes()
        replacement = _card().replace("审核发布卡", "校验后替换卡").encode("utf-8")
        real_validate = publisher.validate_receipt

        def mutate_after_validation(*args, **kwargs):
            result = real_validate(*args, **kwargs)
            self.staged.write_bytes(replacement)
            return result

        with patch.object(
            publisher, "validate_receipt", side_effect=mutate_after_validation
        ):
            publish(self.ledger, self.cards, self.receipt, self.root)

        destination = self.root / "knowledge/ops/ascendc/runbooks/precision/card.md"
        self.assertEqual(reviewed_bytes, destination.read_bytes())
        self.assertNotEqual(self.staged.read_bytes(), destination.read_bytes())


if __name__ == "__main__":
    unittest.main()
