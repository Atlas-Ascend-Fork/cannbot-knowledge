#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ValidateCuratedOutputTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.trace_dir = self.root / "normalized" / "trace1"
        self.trace_dir.mkdir(parents=True)
        self.trace = self.trace_dir / "normalized_trace.jsonl"
        self.trace.write_text(
            '{"sequence":1}\n{"sequence":2}\n', encoding="utf-8"
        )
        self.raw_sha = "a" * 64
        self.normalized_sha = hashlib.sha256(self.trace.read_bytes()).hexdigest()
        (self.trace_dir / "session_manifest.json").write_text(
            json.dumps(
                {
                    "source": {"sha256": self.raw_sha},
                    "coverage": {"normalized_events": 2},
                }
            ),
            encoding="utf-8",
        )

        self.mine = self.root / "trace1"
        self.mine.mkdir()
        self.draft = self.mine / "DRAFT-card.md"
        self.draft.write_text("# Draft\n", encoding="utf-8")
        (self.mine / "reconstruction.json").write_text(
            json.dumps(
                {
                    "trace_id": "trace1",
                    "normalized_trace_path": str(self.trace.resolve()),
                    "raw_source_sha256": self.raw_sha,
                    "normalized_trace_sha256": self.normalized_sha,
                    "coverage": {
                        "first_sequence": 1,
                        "last_sequence": 2,
                        "sequence_count": 2,
                        "sequence_contiguous": True,
                        "normalized_events": 2,
                    },
                }
            ),
            encoding="utf-8",
        )
        self.clusters = self.root / "clusters.json"
        self.clusters.write_text(
            json.dumps(
                {
                    "clusters": [
                        {"id": "cluster-1", "members": [{"draft": str(self.draft)}]}
                    ]
                }
            ),
            encoding="utf-8",
        )
        prefix = self.normalized_sha[:12]
        self.ledger_data = {
            "entries": [
                {
                    "cluster": "cluster-1",
                    "operation": "new",
                    "status": "published",
                    "reason": "novel validated pattern",
                    "target_slug": "card",
                    "target_path": "card.md",
                    "source_drafts": [str(self.draft)],
                    "knowledge_form": "validated_pattern",
                    "tier": "single_run",
                    "reproduce_count": 1,
                    "evidence_audit": {
                        "mode": "trace_snapshot",
                        "result": "pending",
                        "trace_snapshot": {
                            "normalized_trace_path": [str(self.trace.resolve())],
                            "raw_source_sha256": [self.raw_sha],
                            "normalized_trace_sha256": [self.normalized_sha],
                            "coverage_verified": True,
                            "evidence_roles": {
                                "implementation": [f"{prefix}#1"],
                                "validation": [f"{prefix}#2"],
                            },
                            "mechanism_artifacts": [
                                {
                                    "role": "implementation",
                                    "kind": "code",
                                    "path": "kernel.cpp",
                                    "symbol_or_target": "Kernel",
                                    "reconstruction_method": "full_snapshot",
                                    "anchors": [f"{prefix}#1"],
                                    "verbatim_verified": False,
                                }
                            ],
                        },
                    },
                }
            ]
        }
        self.ledger = self.root / "ledger.json"
        self._write_ledger()
        self.script = Path(__file__).with_name("validate_curated_output.py")

    def tearDown(self):
        self.temporary.cleanup()

    def _write_ledger(self):
        self.ledger.write_text(json.dumps(self.ledger_data), encoding="utf-8")

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(self.script), str(self.clusters), str(self.ledger), *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_pending_and_approved_phases_are_distinct(self):
        pending = self._run("--pre-review")
        self.assertEqual(0, pending.returncode, pending.stderr)
        premature = self._run()
        self.assertNotEqual(0, premature.returncode)
        self.assertIn("evidence audit must be 'pass'", premature.stderr)

        audit = self.ledger_data["entries"][0]["evidence_audit"]
        audit["result"] = "pass"
        audit["trace_snapshot"]["mechanism_artifacts"][0][
            "verbatim_verified"
        ] = True
        self._write_ledger()
        approved = self._run()
        self.assertEqual(0, approved.returncode, approved.stderr)

    def test_tier_and_reproduce_count_are_required(self):
        entry = self.ledger_data["entries"][0]
        del entry["tier"]
        self._write_ledger()
        missing = self._run("--pre-review")
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("has invalid tier None", missing.stderr)

        entry["tier"] = "verified"
        entry["reproduce_count"] = 1
        self._write_ledger()
        under_reproduced = self._run("--pre-review")
        self.assertNotEqual(0, under_reproduced.returncode)
        self.assertIn(
            "verified tier requires reproduce_count >= 2",
            under_reproduced.stderr,
        )

    def _add_trace(self, raw_sha):
        directory = self.root / "normalized" / "trace2"
        directory.mkdir()
        trace = directory / "normalized_trace.jsonl"
        trace.write_text('{"sequence":1,"run":2}\n{"sequence":2,"run":2}\n')
        normalized_sha = hashlib.sha256(trace.read_bytes()).hexdigest()
        (directory / "session_manifest.json").write_text(json.dumps({
            "source": {"sha256": raw_sha}, "coverage": {"normalized_events": 2},
        }))
        entry = self.ledger_data["entries"][0]
        snapshot = entry["evidence_audit"]["trace_snapshot"]
        snapshot["normalized_trace_path"].append(str(trace.resolve()))
        snapshot["raw_source_sha256"].append(raw_sha)
        snapshot["normalized_trace_sha256"].append(normalized_sha)
        for role, sequence in (("implementation", 1), ("validation", 2)):
            snapshot["evidence_roles"][role].append(f"{normalized_sha[:12]}#{sequence}")
        snapshot["mechanism_artifacts"][0]["anchors"].append(f"{normalized_sha[:12]}#1")
        self._write_ledger()

    def test_one_trace_cannot_claim_multiple_reproductions(self):
        entry = self.ledger_data["entries"][0]
        entry["reproduce_count"] = 2
        for tier in ("single_run", "verified"):
            with self.subTest(tier=tier):
                entry["tier"] = tier
                self._write_ledger()
                result = self._run("--pre-review")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("exceeds distinct raw sources", result.stderr)

    def test_normalizing_one_raw_source_twice_does_not_add_reproductions(self):
        self._add_trace(self.raw_sha)
        entry = self.ledger_data["entries"][0]
        entry.update(tier="verified", reproduce_count=2)
        self._write_ledger()
        result = self._run("--pre-review")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("exceeds distinct raw sources", result.stderr)

    def test_distinct_raw_sources_allow_review_of_reproduced_claim(self):
        self._add_trace("b" * 64)
        entry = self.ledger_data["entries"][0]
        entry.update(tier="verified", reproduce_count=2)
        self._write_ledger()
        result = self._run("--pre-review")
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
