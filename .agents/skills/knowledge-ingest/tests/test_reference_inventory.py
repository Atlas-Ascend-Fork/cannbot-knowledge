from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/reference_inventory.py"
REPO_ROOT = SCRIPT.parents[4]


def load_module():
    spec = importlib.util.spec_from_file_location("reference_inventory_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        check=False,
        text=True,
        capture_output=True,
    )


class ReferenceInventoryTests(unittest.TestCase):
    def test_classification(self) -> None:
        module = load_module()
        self.assertEqual(module.classify("docs/api.md"), "technical_doc")
        self.assertEqual(module.classify("include/api.h"), "header")
        self.assertEqual(module.classify("src/api.cpp"), "implementation")
        self.assertEqual(module.classify("tests/test_api.py"), "test")

    def test_inventory_ledger_and_produced_card_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source_root = work / "source"
            source_root.mkdir()
            subprocess.run(["git", "init", "-q", str(source_root)], check=True)
            subprocess.run(
                ["git", "-C", str(source_root), "config", "user.email", "test@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(source_root), "config", "user.name", "Test"],
                check=True,
            )
            (source_root / "docs").mkdir()
            (source_root / "docs/api.md").write_text("# API\n", encoding="utf-8")
            (source_root / "build.txt").write_text("build\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(source_root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(source_root), "commit", "-qm", "fixture"], check=True)

            inventory = work / "inventory.json"
            ledger = work / "ledger.json"
            created = run_script(
                "inventory",
                "--source-root",
                str(source_root),
                "--scope",
                "docs",
                "--repo",
                "https://example.com/source",
                "--ref",
                "main",
                "--output",
                str(inventory),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            scaffolded = run_script(
                "scaffold-ledger",
                "--inventory",
                str(inventory),
                "--output",
                str(ledger),
            )
            self.assertEqual(scaffolded.returncode, 0, scaffolded.stderr)

            knowledge_root = work / "knowledge-repository"
            shutil.copytree(REPO_ROOT / "governance", knowledge_root / "governance")
            (knowledge_root / "knowledge").mkdir()
            incomplete = run_script(
                "verify",
                "--inventory",
                str(inventory),
                "--ledger",
                str(ledger),
                "--source-root",
                str(source_root),
                "--knowledge-root",
                str(knowledge_root),
            )
            self.assertEqual(incomplete.returncode, 1)

            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
            for decision in ledger_data["decisions"]:
                if decision["path"] == "docs/api.md":
                    decision.update(
                        action="ingest",
                        target_card="knowledge/runtime/apis/example.md",
                        role="primary",
                        reason="",
                    )
            ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
            missing_card = run_script(
                "verify",
                "--inventory",
                str(inventory),
                "--ledger",
                str(ledger),
                "--source-root",
                str(source_root),
                "--knowledge-root",
                str(knowledge_root),
            )
            self.assertEqual(missing_card.returncode, 1)
            self.assertIn("produced target card does not exist", missing_card.stdout)

            inventory_data = json.loads(inventory.read_text(encoding="utf-8"))
            commit = inventory_data["source"]["commit"]
            card = knowledge_root / "knowledge/runtime/apis/example.md"
            card.parent.mkdir(parents=True)
            card.write_text(
                f"""---
type: API
title: Example API
description: Synthetic reference ingest fixture.
tags: [task.lookup, topic.compilation]
status: stable
sources:
  - resource: https://example.com/source/blob/{commit}/docs/api.md
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: [a2]
---

# Example API

This card binds a ledger decision to a fixed source file.
""",
                encoding="utf-8",
            )
            receipt = work / "reference-verification.json"
            complete = run_script(
                "verify",
                "--inventory",
                str(inventory),
                "--ledger",
                str(ledger),
                "--source-root",
                str(source_root),
                "--knowledge-root",
                str(knowledge_root),
                "--receipt",
                str(receipt),
            )
            self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)
            verification = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                verification["schema_version"],
                "cannbot-reference-verification.v1",
            )
            self.assertEqual(
                verification["produced"][0]["target_card"],
                "knowledge/runtime/apis/example.md",
            )
            self.assertEqual(
                verification["produced"][0]["sources"][0]["path"],
                "docs/api.md",
            )
            duplicate_receipt = run_script(
                "verify",
                "--inventory",
                str(inventory),
                "--ledger",
                str(ledger),
                "--knowledge-root",
                str(knowledge_root),
                "--receipt",
                str(receipt),
            )
            self.assertEqual(duplicate_receipt.returncode, 2)
            self.assertIn("refusing to overwrite verification receipt", duplicate_receipt.stderr)

            card.write_text(
                card.read_text(encoding="utf-8").replace("/blob/", "/tree/"),
                encoding="utf-8",
            )
            broad_tree = run_script(
                "verify",
                "--inventory",
                str(inventory),
                "--ledger",
                str(ledger),
                "--knowledge-root",
                str(knowledge_root),
            )
            self.assertEqual(broad_tree.returncode, 1)
            self.assertIn("no card source binds docs/api.md", broad_tree.stdout)

            card.write_text(
                card.read_text(encoding="utf-8")
                .replace("/tree/", "/blob/")
                .replace("docs/api.md", "docs/other.md"),
                encoding="utf-8",
            )
            source_mismatch = run_script(
                "verify",
                "--inventory",
                str(inventory),
                "--ledger",
                str(ledger),
                "--knowledge-root",
                str(knowledge_root),
            )
            self.assertEqual(source_mismatch.returncode, 1)
            self.assertIn("no card source binds docs/api.md", source_mismatch.stdout)


if __name__ == "__main__":
    unittest.main()
