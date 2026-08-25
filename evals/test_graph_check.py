from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / ".gitcode/scripts/graph_check.py"
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
        "schema_version": 1,
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
        def run_builder(*_args, **_kwargs):
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


if __name__ == "__main__":
    unittest.main()
