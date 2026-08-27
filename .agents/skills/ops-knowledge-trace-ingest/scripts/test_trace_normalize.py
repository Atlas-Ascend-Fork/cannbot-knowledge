#!/usr/bin/env python3

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import trace_normalize as tn  # noqa: E402


def _normalize_text(text: str) -> dict:
    """Run the full normalize pipeline in-memory for a single text blob."""
    collector = tn.SourceCollector()
    collector.blobs = [(f"input_{len(text)}.txt", text.encode("utf-8"))]
    collector.warnings = []
    records = tn.parse_records(collector.blobs, collector.warnings)
    if not records:
        raise AssertionError("no records parsed")
    selected, scores, events, failures = tn.normalize_source(
        collector, records, "auto"
    )
    redactions = 0
    for index, event in enumerate(events):
        events[index], found = tn._redact(event)
        redactions += found
    serialized = [json.dumps(e, ensure_ascii=False, sort_keys=True) for e in events]
    return {
        "selected": selected,
        "events": events,
        "serialized": serialized,
        "redactions": redactions,
        "failures": failures,
    }


class TraceNormalizeRegressionTest(unittest.TestCase):
    def test_plain_text_input_is_not_silently_dropped(self) -> None:
        result = _normalize_text(
            "这是一段普通对话文本\n没有 JSON 结构\n也没有 trace 语义\n"
        )
        self.assertGreater(len(result["events"]), 0)
        self.assertNotEqual(result["selected"], "trace_export")
        for event in result["events"]:
            self.assertIn("provenance", event)

    def test_secret_token_is_redacted_in_output(self) -> None:
        text = (
            "user: 帮我看看环境\n"
            'Authorization: Bearer xyz123secret456\n'
            "assistant: 已处理\n"
        )
        result = _normalize_text(text)
        self.assertGreater(result["redactions"], 0)
        joined = "\n".join(result["serialized"])
        self.assertNotIn("xyz123secret456", joined)
        self.assertIn("<redacted>", joined)


if __name__ == "__main__":
    unittest.main()