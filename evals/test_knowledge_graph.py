# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / ".agents/skills/knowledge-ingest"
GRAPH_SCRIPT = SKILL_ROOT / "scripts/knowledge_graph.py"
INGEST_SCRIPT = SKILL_ROOT / "scripts/knowledge_ingest.py"
API = "ops/ascendc/apis/interface"
OPERATOR = "ops/ascendc/operators/direct/cv/objdetect/implementation"
UNLINKED = "ops/ascendc/apis/similar"


def card(title: str, kind: str, body: str = "SharedContract interface boundary.") -> str:
    return (
        "---\n"
        f"type: {kind}\ntitle: {title}\n"
        "description: SharedContract interface boundary.\n"
        "tags: [task.lookup, topic.data_movement]\n"
        "status: draft\nsources: []\nplatforms: []\n"
        "created_at: '2026-08-22T00:00:00Z'\n"
        "updated_at: '2026-08-22T00:00:00Z'\n"
        f"---\n\n# {title}\n\n{body}\n"
    )


class KnowledgeGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository"
        shutil.copytree(REPOSITORY_ROOT / "governance", self.root / "governance")
        for doc_id, kind in ((API, "API"), (OPERATOR, "Operator"), (UNLINKED, "API")):
            path = self.root / "knowledge" / f"{doc_id}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(card("SharedContract", kind), encoding="utf-8")
        result = self.run_script(INGEST_SCRIPT, "sync-indexes")
        self.assertEqual(0, result.returncode, result.stderr)

    def run_script(self, script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), "--knowledge-root", str(self.root), *arguments],
            check=False, text=True, capture_output=True,
        )

    def run_graph(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self.run_script(GRAPH_SCRIPT, *arguments)

    def append(self, doc_id: str, body: str) -> None:
        path = self.root / "knowledge" / f"{doc_id}.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n" + body + "\n", encoding="utf-8")

    def graph(self) -> dict:
        return json.loads((self.root / "artifacts/graphs/graph.json").read_text(encoding="utf-8"))

    def test_only_existing_links_form_edges_including_api_operator(self) -> None:
        self.append(API, f"相关算子：[implementation](/{OPERATOR}.md#contract)。")
        self.append(API, f"[duplicate][op]\n\n[op]: /{OPERATOR}.md")
        self.append(API, "[index](index.md) [self](interface.md#section)")
        self.append(API, "`[inline](similar.md)`\n\n```md\n[fenced](similar.md)\n```")
        self.append(API, "[external](https://example.com/interface.md)")
        self.append(OPERATOR, "相关 API：[interface](../../../../apis/%69nterface.md)。")
        before = {p: p.read_bytes() for p in (self.root / "knowledge").rglob("*.md")}
        result = self.run_graph("build")
        self.assertEqual(0, result.returncode, result.stderr)
        graph = self.graph()
        self.assertEqual({API, OPERATOR, UNLINKED}, {node["id"] for node in graph["nodes"]})
        self.assertEqual(
            [
                {"source": API, "relation": "links_to", "target": OPERATOR},
                {"source": OPERATOR, "relation": "links_to", "target": API},
            ], graph["edges"],
        )
        first = (self.root / "artifacts/graphs/graph.json").read_bytes()
        result = self.run_script(INGEST_SCRIPT, "build-graph")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(first, (self.root / "artifacts/graphs/graph.json").read_bytes())
        for command in ("viz", "verify"):
            result = self.run_graph(command)
            self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in (self.root / "knowledge").rglob("*.md")})
        self.assertEqual(
            {"artifacts/graphs/graph.json", "artifacts/graphs/graph.html"},
            {p.relative_to(self.root).as_posix() for p in (self.root / "artifacts").rglob("*") if p.is_file()},
        )
        shutil.copyfile(REPOSITORY_ROOT / ".gitignore", self.root / ".gitignore")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        ignored = subprocess.run(
            ["git", "check-ignore", "artifacts/graphs/graph.json", "artifacts/graphs/graph.html"],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, ignored.returncode, ignored.stderr)
        self.assertEqual(2, len(ignored.stdout.splitlines()))

    def test_unlinked_cards_build_without_judgments_and_ignore_old_cache(self) -> None:
        output = self.root / "artifacts/graphs"
        output.mkdir(parents=True)
        (output / "edge_judgments.json").write_text("invalid legacy cache", encoding="utf-8")
        result = self.run_graph("build")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.graph()["edges"])
        self.assertEqual(3, len(self.graph()["nodes"]))
        result = self.run_graph("verify")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_graph_keeps_all_explicit_links_and_excludes_offline_source_targets(self) -> None:
        import os
        import yaml

        for index in range(12):
            doc_id = OPERATOR + f"_{index}"
            path = self.root / "knowledge" / f"{doc_id}.md"
            path.write_text(card("Implementation", "Operator"), encoding="utf-8")
            self.append(API, f"[implementation](/{doc_id}.md)")
        registry = yaml.safe_load((self.root / "governance/schemas/registries.yaml").read_text())
        source = next(item for item in registry["local_sources"].values() if item.get("kind") == "git")
        target = self.root / source["root"] / source["revisions"][0] / "kernel.h"
        href = os.path.relpath(target, (self.root / "knowledge" / f"{API}.md").parent)
        self.append(API, f"[source]({href})")
        result = self.run_graph("build")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(12, len(self.graph()["edges"]))
        self.assertFalse(any(source["root"] in node["id"] for node in self.graph()["nodes"]))
        self.assertFalse(target.exists())

    def test_invalid_links_and_mismatched_target_contract_fail(self) -> None:
        path = self.root / "knowledge" / f"{API}.md"
        original = path.read_text(encoding="utf-8")
        outside = self.root / "outside.md"
        outside.write_text("# Outside", encoding="utf-8")
        for link in ("missing.md", "../../../../outside.md"):
            with self.subTest(link=link):
                path.write_text(original + f"\n[invalid]({link})\n", encoding="utf-8")
                result = self.run_graph("build")
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("link.", result.stderr)
                self.assertFalse((self.root / "artifacts/graphs/graph.json").exists())
        path.write_text(original, encoding="utf-8")
        contract = self.root / "governance/contracts/knowledge.py"
        contract.write_text("raise RuntimeError('must not execute target code')\n", encoding="utf-8")
        result = self.run_graph("build")
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("RuntimeError", result.stderr)

    def test_explicit_verification_detects_changed_links_and_html(self) -> None:
        self.assertEqual(2, self.run_graph("verify").returncode)
        self.assertEqual(0, self.run_graph("build").returncode)
        self.append(API, f"[operator](/{OPERATOR}.md)")
        for command in ("verify", "viz"):
            result = self.run_graph(command)
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("stale", result.stderr)
        self.assertEqual(0, self.run_graph("build").returncode)
        self.assertEqual(0, self.run_graph("viz").returncode)
        page = self.root / "artifacts/graphs/graph.html"
        page.write_text("stale HTML", encoding="utf-8")
        result = self.run_graph("verify")
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("visualization is stale", result.stderr)
        self.assertEqual(0, self.run_graph("viz").returncode)
        self.assertEqual(0, self.run_graph("verify").returncode)
        path = self.root / "knowledge" / f"{API}.md"
        path.write_text(card("SharedContract", "API"), encoding="utf-8")
        (self.root / "knowledge" / f"{OPERATOR}.md").unlink()
        self.assertEqual(0, self.run_graph("build").returncode)
        self.assertEqual([], self.graph()["edges"])
        self.assertNotIn(OPERATOR, {node["id"] for node in self.graph()["nodes"]})


if __name__ == "__main__":
    unittest.main()
