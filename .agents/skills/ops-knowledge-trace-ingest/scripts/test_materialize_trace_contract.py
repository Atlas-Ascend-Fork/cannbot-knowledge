#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from materialize_trace_contract import augment_ledger
from validate_review_receipt import build_subject, validate_receipt


class MaterializeTraceContractTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.mine = self.root / "trace1"
        self.mine.mkdir()
        self.draft = self.mine / "DRAFT-card.md"
        self.draft.write_text("# Draft\n", encoding="utf-8")
        snapshot = {
            "DRAFT-card.md": {
                "normalized_trace_path": ["/tmp/normalized_trace.jsonl"],
                "raw_source_sha256": ["a" * 64],
                "normalized_trace_sha256": ["b" * 64],
                "coverage_verified": True,
                "evidence_roles": {"implementation": ["bbbbbbbbbbbb#1"], "validation": ["bbbbbbbbbbbb#2"]},
                "mechanism_artifacts": [
                    {
                        "role": "implementation",
                        "kind": "code",
                        "path": "kernel.cpp",
                        "symbol_or_target": "Kernel",
                        "reconstruction_method": "full_snapshot",
                        "anchors": ["bbbbbbbbbbbb#1"],
                        "verbatim_verified": False,
                    }
                ],
            }
        }
        (self.mine / "trace_snapshots.json").write_text(
            json.dumps(snapshot), encoding="utf-8"
        )
        self.ledger = self.root / "ledger.json"
        self.ledger.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "draft": str(self.draft),
                            "source_drafts": [str(self.draft)],
                            "operation": "new",
                            "status": "published",
                            "target_slug": "card",
                            "target_path": "card.md",
                            "evidence_audit": {
                                "mode": "trace_snapshot",
                                "result": "pending",
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.cards = self.root / "staged-cards"
        self.cards.mkdir()
        (self.cards / "card.md").write_text("# Card\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def _fresh_fixture(self, trace_id: str):
        mine = self.root / trace_id
        mine.mkdir()
        draft = mine / "DRAFT-fresh.md"
        draft.write_text("# Fresh draft\n", encoding="utf-8")
        (mine / "manifest.json").write_text(
            json.dumps(
                {
                    "trace_id": trace_id,
                    "candidates": [
                        {
                            "draft_path": str(draft),
                            "knowledge_form": "validated_pattern",
                            "fixed_signal_refs": [2],
                            "code_evidence": [
                                {
                                    "path": "kernel.cpp",
                                    "symbol": "Kernel",
                                    "after_event_refs": [1],
                                    "supports_claims": ["validated kernel"],
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (mine / "reconstruction.json").write_text("{}", encoding="utf-8")
        normalized_root = self.root / f"normalized-{trace_id}"
        normalized = normalized_root / trace_id
        normalized.mkdir(parents=True)
        (normalized / "normalized_trace.jsonl").write_text(
            '{"sequence":1,"event_type":"tool_call"}\n'
            '{"sequence":2,"event_type":"tool_result"}\n',
            encoding="utf-8",
        )
        (normalized / "session_manifest.json").write_text(
            json.dumps({"source": {"sha256": "c" * 64}}),
            encoding="utf-8",
        )
        ledger = self.root / f"ledger-{trace_id}.json"
        ledger.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "draft": str(draft),
                            "source_drafts": [str(draft)],
                            "operation": "new",
                            "status": "published",
                            "target_slug": "fresh",
                            "target_path": "precision/fresh.md",
                            "evidence_audit": {
                                "mode": "trace_snapshot",
                                "result": "pending",
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return mine, normalized_root, ledger

    def test_pass_receipt_can_apply_only_reviewer_owned_flags(self):
        augment_ledger(self.ledger, [self.mine], verified=False)
        pending = json.loads(self.ledger.read_text(encoding="utf-8"))
        audit = pending["entries"][0]["evidence_audit"]
        self.assertEqual("pending", audit["result"])
        self.assertFalse(
            audit["trace_snapshot"]["mechanism_artifacts"][0]["verbatim_verified"]
        )

        receipt = {
            **build_subject(self.ledger, self.cards),
            "verdict": "PASS",
            "findings": [],
            "summary": "review passed",
            "reviewer": "subagent:test-reviewer",
            "attestation": "agent-runtime-message",
            "reviewed_at": "2026-08-28T08:00:00Z",
        }
        receipt_path = self.root / "receipt.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        augment_ledger(self.ledger, [self.mine], verified=True)
        approved = json.loads(self.ledger.read_text(encoding="utf-8"))
        audit = approved["entries"][0]["evidence_audit"]
        self.assertEqual("pass", audit["result"])
        self.assertTrue(
            audit["trace_snapshot"]["mechanism_artifacts"][0]["verbatim_verified"]
        )
        self.assertTrue(
            validate_receipt(self.ledger, self.cards, receipt_path)["ok"]
        )

    def test_verified_cli_requires_receipt_and_staged_cards(self):
        script = Path(__file__).with_name("materialize_trace_contract.py")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(self.mine),
                "--normalized-root",
                str(self.root),
                "--ledger",
                str(self.ledger),
                "--verified",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn(
            "--verified requires --ledger, --receipt, and --cards-root",
            result.stderr,
        )

    def test_fresh_cli_materializes_and_augments_in_one_call(self):
        mine, normalized_root, ledger = self._fresh_fixture("fresh-trace")
        script = Path(__file__).with_name("materialize_trace_contract.py")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(mine),
                "--normalized-root",
                str(normalized_root),
                "--ledger",
                str(ledger),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue((mine / "trace_snapshots.json").is_file())
        reconstruction = json.loads(
            (mine / "reconstruction.json").read_text(encoding="utf-8")
        )
        self.assertEqual("fresh-trace", reconstruction["trace_id"])
        audit = json.loads(ledger.read_text(encoding="utf-8"))["entries"][0][
            "evidence_audit"
        ]
        self.assertEqual("pending", audit["result"])
        self.assertFalse(
            audit["trace_snapshot"]["mechanism_artifacts"][0][
                "verbatim_verified"
            ]
        )

    def test_multi_dir_failure_leaves_ledger_unchanged(self):
        mine, normalized_root, ledger = self._fresh_fixture("good-trace")
        bad_mine = self.root / "bad-trace"
        bad_mine.mkdir()
        before = ledger.read_bytes()
        script = Path(__file__).with_name("materialize_trace_contract.py")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(mine),
                str(bad_mine),
                "--normalized-root",
                str(normalized_root),
                "--ledger",
                str(ledger),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, ledger.read_bytes())


if __name__ == "__main__":
    unittest.main()
