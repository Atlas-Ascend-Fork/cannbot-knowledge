from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / ".gitcode/scripts/format_check.py"


def load_entrypoint():
    spec = importlib.util.spec_from_file_location("format_check_test", ENTRYPOINT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ENTRYPOINT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FormatCheckSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entrypoint = load_entrypoint()

    def test_summary_omits_ci_meta_context(self) -> None:
        findings = [
            {
                "check": "format",
                "tier": "P1",
                "path": f"knowledge/example_{index}.md",
                "line": index + 1,
                "code": "format.example",
                "message": "Example finding.",
                "details": None,
            }
            for index in range(21)
        ]
        summary = self.entrypoint.render_summary(
            {"checked": 21, "findings": findings}, 0, "", ""
        )
        for text in ("format-check.json", "结果文件", "OBS", "Summary", "下载"):
            self.assertNotIn(text, summary)
        self.assertNotIn("检查范围", summary)
        self.assertEqual(21, summary.count("| P1 |"))
        self.assertIn("knowledge/example_20.md:21", summary)
        self.assertEqual(
            "FormatCheck 未生成有效结果。",
            self.entrypoint.runtime_result(ROOT)["findings"][0]["message"],
        )

    def test_public_artifact_hides_the_runner_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "format.json"
            self.entrypoint.write_result(
                output,
                {"root": "/runner/private/repository", "checked": 1, "findings": []},
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(".", result["root"])
        self.assertNotIn("/runner", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
