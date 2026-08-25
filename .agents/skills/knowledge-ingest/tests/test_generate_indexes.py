from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts/knowledge_ingest.py"
REPOSITORY_ROOT = SKILL_ROOT.parents[2]


def load_module():
    spec = importlib.util.spec_from_file_location("knowledge_ingest_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerateIndexesTests(unittest.TestCase):
    def make_root(self, base: Path) -> Path:
        root = base / "repository"
        section = root / "knowledge/section"
        section.mkdir(parents=True)
        (root / "knowledge/index.md").write_text(
            "# Hand-authored root\n\nKeep this prose.\n\n"
            "- [人工 section 标题](section/index.md)：本文件为文档发布时所需的索引文件。\n",
            encoding="utf-8",
        )
        (section / "card.md").write_text(
            """---
title: Example card
description: A complete example description.
---

# Example card
""",
            encoding="utf-8",
        )
        return root

    def run_script(self, root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--knowledge-root",
                str(root),
                "sync-indexes",
                *extra,
            ],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_default_updates_all_ancestors_and_preserves_prose(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            result = self.run_script(root)
            self.assertEqual(0, result.returncode, result.stderr)
            root_index = (root / "knowledge/index.md").read_text(encoding="utf-8")
            self.assertIn("# Hand-authored root", root_index)
            self.assertIn("Keep this prose.", root_index)
            self.assertIn("[人工 section 标题](section/index.md)", root_index)
            self.assertIn("A complete example description.", root_index)
            section_index = (root / "knowledge/section/index.md").read_text(encoding="utf-8")
            self.assertIn("[Example card](card.md)：A complete example description.", section_index)
            self.assertIn("Synchronized 2 indexes", result.stdout)

    def test_removes_stale_entry_without_rewriting_prose(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            (root / "knowledge/index.md").write_text(
                "# Hand-authored root\n\nKeep this prose.\n\n"
                "- [Removed](removed.md)：No longer present.\n",
                encoding="utf-8",
            )
            result = self.run_script(root)
            self.assertEqual(0, result.returncode, result.stderr)
            root_index = (root / "knowledge/index.md").read_text(encoding="utf-8")
            self.assertNotIn("removed.md", root_index)
            self.assertIn("Keep this prose.", root_index)
            self.assertIn("section/index.md", root_index)

    def test_check_fails_closed_then_passes_after_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            stale = self.run_script(root, "--check")
            self.assertEqual(1, stale.returncode)
            self.assertIn("stale index: knowledge/index.md", stale.stdout)
            self.assertIn("stale index: knowledge/section/index.md", stale.stdout)

            synchronized = self.run_script(root)
            self.assertEqual(0, synchronized.returncode, synchronized.stderr)
            clean = self.run_script(root, "--check")
            self.assertEqual(0, clean.returncode, clean.stderr)
            self.assertIn("stale 0", clean.stdout)

    def test_duplicate_frontmatter_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            card = root / "knowledge/section/card.md"
            card.write_text(
                "---\ntitle: First\ntitle: Second\n"
                "description: A complete example description.\n---\n\n# Card\n",
                encoding="utf-8",
            )
            result = self.run_script(root, "--check")
        self.assertEqual(2, result.returncode)
        self.assertIn("duplicate key", result.stderr)

    def test_reference_style_navigation_is_preserved_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            (root / "knowledge/index.md").write_text(
                "# Hand-authored root\n\nKeep this prose.\n\n"
                "- [人工 section 标题][section]：A complete section description.\n\n"
                "[section]: section/index.md\n",
                encoding="utf-8",
            )
            synchronized = self.run_script(root)
            self.assertEqual(0, synchronized.returncode, synchronized.stderr)
            index = (root / "knowledge/index.md").read_text(encoding="utf-8")
            self.assertIn("[人工 section 标题][section]", index)
            self.assertNotIn("[section](section/index.md)", index)
            self.assertEqual(index.count("section/index.md"), 1)
            clean = self.run_script(root, "--check")
        self.assertEqual(0, clean.returncode, clean.stderr)

    def test_atomic_create_never_replaces_an_existing_file(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "card.md"
            module.atomic_create(target, "first\n")
            with self.assertRaises(FileExistsError):
                module.atomic_create(target, "second\n")
            content = target.read_text(encoding="utf-8")
        self.assertEqual("first\n", content)


class BuildGraphTests(unittest.TestCase):
    def test_reference_style_link_uses_shared_contract_parser(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repository"
            shutil.copytree(REPOSITORY_ROOT / "governance", root / "governance")
            cards = root / "knowledge/common/glossaries"
            cards.mkdir(parents=True)
            common = (
                "type: Glossary\n"
                "description: A complete glossary description.\n"
                "tags: [task.lookup, topic.terminology]\n"
                "status: draft\n"
                "sources: []\n"
                "created_at: '2026-08-22T00:00:00Z'\n"
                "updated_at: '2026-08-22T00:00:00Z'\n"
            )
            (cards / "source.md").write_text(
                f"---\ntitle: Source\n{common}---\n\n# Source\n\n[Target][target]\n\n"
                "![Image](decoy.md)\n\n"
                "`[Inline code](decoy.md)`\n\n"
                "```markdown\n[Fenced](decoy.md)\n```\n\n"
                "[target]: target.md\n",
                encoding="utf-8",
            )
            (cards / "target.md").write_text(
                f"---\ntitle: Target\n{common}---\n\n# Target\n",
                encoding="utf-8",
            )
            (cards / "decoy.md").write_text(
                f"---\ntitle: Decoy\n{common}---\n\n# Decoy\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--knowledge-root",
                    str(root),
                    "build-graph",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            graph = json.loads(
                (root / "artifacts/graphs/graph.json").read_text(encoding="utf-8")
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [
                {
                    "source": "common/glossaries/source",
                    "relation": "links_to",
                    "target": "common/glossaries/target",
                }
            ],
            graph["edges"],
        )

    def test_graph_data_accepts_an_aliased_repository_root(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "repository"
            shutil.copytree(REPOSITORY_ROOT / "governance", root / "governance")
            cards = root / "knowledge/common/glossaries"
            cards.mkdir(parents=True)
            (cards / "card.md").write_text(
                "---\n"
                "type: Glossary\n"
                "title: Card\n"
                "description: A complete glossary description.\n"
                "tags: [task.lookup, topic.terminology]\n"
                "status: draft\n"
                "sources: []\n"
                "created_at: '2026-08-22T00:00:00Z'\n"
                "updated_at: '2026-08-22T00:00:00Z'\n"
                "---\n\n# Card\n",
                encoding="utf-8",
            )
            alias = base / "repository-alias"
            alias.symlink_to(root, target_is_directory=True)
            nodes, edges = module.graph_data(alias)

        self.assertEqual(1, len(nodes))
        self.assertEqual("common/glossaries/card", nodes[0]["id"])
        self.assertEqual([], edges)


if __name__ == "__main__":
    unittest.main()
