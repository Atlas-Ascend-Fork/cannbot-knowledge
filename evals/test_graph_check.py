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

import argparse
import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / ".gitcode/scripts/graph_check.py"
INGEST = ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
GRAPH = INGEST.with_name("knowledge_graph.py")
MISSING = object()


def load_entrypoint():
    spec = importlib.util.spec_from_file_location("graph_check_test", ENTRYPOINT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ENTRYPOINT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def builder_graph():
    return {
        "schema_version": 2,
        "nodes": [{"id": "source"}, {"id": "target"}],
        "edges": [{"source": "source", "relation": "links_to", "target": "target"}],
    }


class GraphCheckAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entrypoint = load_entrypoint()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.output = self.root / "result/graph.json"
        self.generated = self.root / self.entrypoint.GENERATED_GRAPH

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_adapter(self, *, returncode=0, output="", artifact=MISSING):
        def run_builder(command, **_kwargs):
            self.assertEqual(
                [
                    self.entrypoint.sys.executable,
                    ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py",
                    "--knowledge-root",
                    str(self.root),
                    "build-graph",
                ],
                command,
            )
            if artifact is not MISSING:
                self.generated.parent.mkdir(parents=True, exist_ok=True)
                content = (
                    artifact if isinstance(artifact, str) else json.dumps(artifact)
                )
                self.generated.write_text(content, encoding="utf-8")
            return subprocess.CompletedProcess([], returncode, output)

        args = argparse.Namespace(repo_root=self.root, output=self.output)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(self.entrypoint, "parse_args", return_value=args),
            mock.patch.object(
                self.entrypoint.subprocess,
                "run",
                side_effect=run_builder,
            ),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            result = self.entrypoint.main()
        return result, stdout.getvalue(), stderr.getvalue()

    def test_loader_only_requires_countable_nodes_and_edges(self) -> None:
        graph = {
            "future_metadata": True,
            "nodes": [None],
            "edges": ["opaque"],
        }
        path = self.root / "graph.json"
        path.write_text(json.dumps(graph), encoding="utf-8")
        self.assertEqual(graph, self.entrypoint.load_graph(path))

    def test_success_copies_the_builder_artifact_and_reports_counts(self) -> None:
        graph = builder_graph()
        graph["future_metadata"] = {"compatible": True}
        returncode, summary, log = self.run_adapter(
            artifact=graph,
            output="builder completed\n",
        )

        self.assertEqual(0, returncode)
        published = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertNotIn("generated_from", published)
        self.assertEqual(graph, published)
        self.assertFalse(self.generated.exists())
        self.assertIn("节点：`2`", summary)
        self.assertIn("边：`1`", summary)
        self.assertNotIn("图范围", summary)
        self.assertNotIn("index.md", summary)
        self.assertNotIn("结果文件", summary)
        self.assertNotIn("OBS", summary)
        self.assertEqual("", log)

    def test_builder_failure_returns_two_and_preserves_the_full_log(self) -> None:
        builder_output = (
            "preparing graph\n"
            "error: first detail\n"
            "additional context\n"
            "error: <script>[final failure](https://example.com)\n"
        )
        returncode, summary, log = self.run_adapter(
            returncode=2,
            output=builder_output,
        )

        self.assertEqual(2, returncode)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.generated.exists())
        self.assertEqual(builder_output, log)
        self.assertIn(
            "失败原因：&lt;script&gt;&#91;final failure&#93;(https://example.com)",
            summary,
        )
        self.assertNotIn("<script>", summary)
        self.assertNotIn("[final failure]", summary)
        self.assertNotIn("图产物", summary)

    def test_success_without_a_readable_artifact_returns_two(self) -> None:
        for label, artifact in (("missing", MISSING), ("invalid JSON", "not json")):
            with self.subTest(label):
                returncode, summary, _ = self.run_adapter(artifact=artifact)
                self.assertEqual(2, returncode)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.generated.exists())
                self.assertIn("构图器未生成有效图数据", summary)

    def test_builder_failure_without_details_hides_the_exit_code(self) -> None:
        returncode, summary, log = self.run_adapter(
            returncode=17,
            output="builder stopped\n",
        )
        self.assertEqual(2, returncode)
        self.assertEqual("builder stopped\n", log)
        self.assertIn("构图失败，未提供具体原因", summary)
        self.assertNotIn("17", summary)


class GraphBuildCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "knowledge root"
        (self.root / "knowledge").mkdir(parents=True)

    def run_ingest(self, *arguments):
        return subprocess.run(
            [sys.executable, str(INGEST), "--knowledge-root", str(self.root), *arguments],
            cwd=self.temporary.name,
            capture_output=True,
            text=True,
            check=False,
        )

    def prepare_corpus(self) -> Path:
        for name in ("contracts", "schemas"):
            shutil.copytree(
                ROOT / "governance" / name,
                self.root / "governance" / name,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        card = self.root / "knowledge/runtime/concepts/probe.md"
        card.parent.mkdir(parents=True)
        card.write_text(
            "---\ntype: Concept\ntitle: Probe\ndescription: Graph compatibility fixture.\n"
            "tags: [task.lookup, topic.compilation]\nstatus: draft\nsources: []\n"
            "created_at: '2026-09-11T00:00:00Z'\nupdated_at: '2026-09-11T00:00:00Z'\n"
            "platforms: [a2]\n---\n\n# Probe\n\nSynthetic fixture only.\n",
            encoding="utf-8",
        )
        result = self.run_ingest("sync-indexes")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return card

    def test_compatibility_build_matches_shared_builder_without_running_target_code(self) -> None:
        card = self.prepare_corpus()
        before = card.read_bytes()
        target_builder = self.root / ".agents/skills/knowledge-ingest/scripts/knowledge_graph.py"
        target_builder.parent.mkdir(parents=True)
        target_builder.write_text("raise RuntimeError('target code must not run')\n", encoding="utf-8")
        result = self.run_ingest("build-graph")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        output = self.root / "artifacts/graphs/graph.json"
        compatible = json.loads(output.read_text(encoding="utf-8"))
        result = subprocess.run(
            [sys.executable, str(GRAPH), "--knowledge-root", str(self.root), "build"],
            cwd=self.temporary.name,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(compatible, json.loads(output.read_text(encoding="utf-8")))
        self.assertIn("runtime/concepts/probe", {node["id"] for node in compatible["nodes"]})
        self.assertTrue(any(edge["relation"] == "part_of" for edge in compatible["edges"]))
        self.assertEqual(before, card.read_bytes())

    def test_compatibility_build_preserves_child_exit_code_and_output_streams(self) -> None:
        spec = importlib.util.spec_from_file_location("graph_compat_ingest_test", INGEST)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module.subprocess, "run", return_value=mock.Mock(returncode=17)) as run:
            result = module.build_graph(argparse.Namespace(knowledge_root=str(self.root)))
        self.assertEqual(17, result)
        run.assert_called_once_with(
            [sys.executable, str(GRAPH), "--knowledge-root", str(self.root), "build"],
            check=False,
        )

    def test_compatibility_build_rejects_mismatched_contract_without_artifacts(self) -> None:
        self.prepare_corpus()
        target_contract = self.root / "governance/contracts/knowledge.py"
        target_contract.write_text("raise RuntimeError('target contract must not run')\n", encoding="utf-8")
        result = self.run_ingest("build-graph")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("target governance contract does not match", result.stderr)
        self.assertFalse((self.root / "artifacts").exists())

    def test_compatibility_build_rejects_missing_root(self) -> None:
        self.root = self.root / "missing"
        result = self.run_ingest("build-graph")
        self.assertEqual(2, result.returncode)
        self.assertIn("not a cannbot-knowledge root", result.stderr)
        self.assertFalse(self.root.exists())

    def test_compatibility_build_does_not_accept_new_modes_or_output_paths(self) -> None:
        for extra in (("--output", "outside.json"), ("--reset",), ("finalize",)):
            with self.subTest(extra=extra):
                result = self.run_ingest("build-graph", *extra)
                self.assertEqual(2, result.returncode)
                self.assertIn("unrecognized arguments", result.stderr)
        self.assertFalse((self.root / "artifacts").exists())
        self.assertFalse((Path(self.temporary.name) / "outside.json").exists())


if __name__ == "__main__":
    unittest.main()
