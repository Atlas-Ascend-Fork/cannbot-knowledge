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


PREFIXED_CREDENTIAL_NAMES = (
    "GITCODE_TOKEN", "HF_TOKEN", "CI_JOB_TOKEN", "client_secret",
    "provider-token", "service_api_key", "service_password", "service-secret-key",
)


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

    def test_quoted_credentials_are_removed_from_normalized_output(self) -> None:
        for value in (
            'password="review fake secret"',
            "token='review_fake_secret'",
            '{"api_key": "review_fake_secret"}',
            '{"authorization": "Bearer review_fake_secret"}',
            'export AUTH_TOKEN="review_fake_secret"',
            'password="escaped\\\"review_fake_secret"',
        ):
            with self.subTest(value=value):
                result = _normalize_text("user: inspect config\nconfig: " + value + "\nassistant: done\n")
                joined = "\n".join(result["serialized"])
                self.assertNotIn("review_fake_secret", joined)
                self.assertNotIn("review fake secret", joined)
                self.assertGreater(result["redactions"], 0)

    def test_structured_credentials_preserve_non_secret_metadata(self) -> None:
        value = {"password": "fake secret", "nested": [{"api_key": "another fake secret"}],
                 "token_count": 12, "session_id": "keep", "secretary": "keep"}
        cleaned, count = tn._redact(value)
        self.assertEqual(2, count)
        self.assertEqual("<redacted>", cleaned["password"])
        self.assertEqual("<redacted>", cleaned["nested"][0]["api_key"])
        self.assertEqual(12, cleaned["token_count"])
        self.assertEqual("keep", cleaned["session_id"])
        self.assertEqual("keep", cleaned["secretary"])
        repeated, additional = tn._redact(cleaned)
        self.assertEqual(cleaned, repeated)
        self.assertEqual(0, additional)

    def test_prefixed_assignments_are_redacted_from_normalized_output(self) -> None:
        for name in PREFIXED_CREDENTIAL_NAMES:
            for quote in ("", "'", '"'):
                with self.subTest(name=name, quote=quote):
                    secret = "review_fake_opaque_credential"
                    assignment = f"{name}={quote}{secret}{quote}"
                    result = _normalize_text(
                        "user: inspect config\nconfig: " + assignment + "\nassistant: done\n"
                    )
                    joined = "\n".join(result["serialized"])
                    self.assertEqual([], result["failures"])
                    self.assertGreater(result["redactions"], 0)
                    self.assertNotIn(secret, joined)
                    self.assertIn(name, joined)
                    self.assertIn("<redacted>", joined)
                    cleaned, additional = tn._redact(result["events"])
                    self.assertEqual(result["events"], cleaned)
                    self.assertEqual(0, additional)

    def test_prefixed_json_keys_match_text_redaction_in_normalized_output(self) -> None:
        secrets = {name: f"review_fake_credential_{index}"
                   for index, name in enumerate(PREFIXED_CREDENTIAL_NAMES)}
        ordinary = {"token_count": 12, "secretary": "keep", "service_token_count": 24,
                    "client_secretary": "keep", "password_hint": "keep"}
        payload = {"nested": [{**secrets, **ordinary}]}
        cleaned, count = tn._redact(payload)
        self.assertEqual(len(secrets), count)
        self.assertEqual(
            {"nested": [{**{name: "<redacted>" for name in secrets}, **ordinary}]},
            cleaned,
        )
        repeated, additional = tn._redact(cleaned)
        self.assertEqual(cleaned, repeated)
        self.assertEqual(0, additional)

        result = _normalize_text(json.dumps({"role": "user", "content": payload}))
        joined = "\n".join(result["serialized"])
        self.assertEqual([], result["failures"])
        self.assertGreaterEqual(result["redactions"], len(secrets))
        for name, secret in secrets.items():
            self.assertIn(name, joined)
            self.assertNotIn(secret, joined)
        self.assertIn("keep", joined)
        for name in ordinary:
            self.assertIn(name, joined)

    def test_ordinary_prefixed_fields_survive_full_normalization(self) -> None:
        text = ("token_count=12 secretary=keep service_token_count=24 "
                "client_secretary=keep password_hint=keep secret_key_id=keep "
                "GITCODE_TOKEN=<redacted>")
        result = _normalize_text("user: inspect config\nconfig: " + text + "\nassistant: done\n")
        self.assertEqual(0, result["redactions"])
        joined = "\n".join(result["serialized"])
        self.assertIn(text, joined)

    def test_redaction_does_not_match_suffixes_or_repeat_markers(self) -> None:
        value = 'token_count=12 secretary=keep password=<redacted>'
        cleaned, count = tn._redact_string(value)
        self.assertEqual(value, cleaned)
        self.assertEqual(0, count)


if __name__ == "__main__":
    unittest.main()
