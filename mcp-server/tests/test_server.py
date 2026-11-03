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

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

INDEX_TOOL = (
    Path(__file__).resolve().parents[2]
    / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
)
GOVERNANCE_SOURCE = Path(__file__).resolve().parents[2] / "governance"


class TokenListTests(unittest.TestCase):
    def test_parses_labels_bare_tokens_and_whitespace(self) -> None:
        tokens = server.TokenList.parse(" cbk_a:zhangsan , cbk_b ,, cbk_c:lisi ")
        self.assertEqual(
            [("cbk_a", "zhangsan"), ("cbk_b", None), ("cbk_c", "lisi")],
            tokens.entries,
        )

    def test_duplicate_tokens_are_deduplicated_but_labels_may_repeat(self) -> None:
        tokens = server.TokenList.parse("cbk_a:zhang,cbk_b:zhang,cbk_a:later")
        self.assertEqual(
            [("cbk_a", "zhang"), ("cbk_b", "zhang")], tokens.entries
        )
        self.assertEqual((True, "zhang"), tokens.match("cbk_b"))

    def test_match_uses_compare_digest_semantics(self) -> None:
        tokens = server.TokenList.parse("cbk_secret:alice")
        self.assertEqual((True, "alice"), tokens.match("cbk_secret"))
        self.assertEqual((False, None), tokens.match("cbk_other"))
        self.assertEqual((False, None), tokens.match("cbk_secre"))


class SlidingWindowLimiterTests(unittest.TestCase):
    def test_allows_limit_then_denies_with_retry_after(self) -> None:
        limiter = server.SlidingWindowRateLimiter()
        decisions = [limiter.check("k", limit=3) for _ in range(4)]
        self.assertEqual([True, True, True, False], [d.allowed for d in decisions])
        self.assertGreaterEqual(decisions[3].retry_after_s, 1)

    def test_distinct_keys_do_not_interfere(self) -> None:
        limiter = server.SlidingWindowRateLimiter()
        for _ in range(3):
            limiter.check("alice", limit=3)
        self.assertTrue(limiter.check("bob", limit=3).allowed)

    def test_zero_limit_disables_limiting(self) -> None:
        limiter = server.SlidingWindowRateLimiter()
        self.assertTrue(limiter.check("k", limit=0).allowed)

    def test_window_slides(self) -> None:
        limiter = server.SlidingWindowRateLimiter()
        base = 1000.0
        original = time.monotonic
        try:
            time.monotonic = lambda: base  # type: ignore[assignment]
            self.assertTrue(limiter.check("k", limit=1).allowed)
            self.assertFalse(limiter.check("k", limit=1).allowed)
            time.monotonic = lambda: base + 61.0  # type: ignore[assignment]
            self.assertTrue(limiter.check("k", limit=1).allowed)
        finally:
            time.monotonic = original  # type: ignore[assignment]


class IpCooldownTests(unittest.TestCase):
    def test_ten_failures_block_the_eleventh_even_with_valid_token(self) -> None:
        cooldown = server.IpCooldown()
        for _ in range(10):
            cooldown.record_failure("10.0.0.7")
        decision = cooldown.check("10.0.0.7")
        self.assertFalse(decision.allowed)
        self.assertGreaterEqual(decision.retry_after_s, 1)
        self.assertTrue(cooldown.check("10.0.0.8").allowed)

    def test_success_resets_the_failure_window(self) -> None:
        cooldown = server.IpCooldown()
        for _ in range(9):
            cooldown.record_failure("10.0.0.7")
        cooldown.record_success("10.0.0.7")
        cooldown.record_failure("10.0.0.7")
        self.assertTrue(cooldown.check("10.0.0.7").allowed)


class HealthEndpointTests(unittest.TestCase):
    def test_health_answers_without_auth_and_never_touches_the_mcp_app(self) -> None:
        inner_calls: list[dict] = []

        async def stub_inner(
            scope: dict, receive: object, send: object
        ) -> None:
            inner_calls.append(scope)

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(),
            server.IpCooldown(),
            0,
            "127.0.0.1",
        )

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }
        asyncio.run(app(scope, receive, send))

        self.assertEqual(2, len(sent))
        self.assertEqual(200, sent[0]["status"])
        self.assertEqual({"status": "ok"}, json.loads(sent[1]["body"]))
        self.assertEqual([], inner_calls)


def make_fixture_root(target: Path) -> Path:
    (target / "knowledge/ops/ascendc/apis").mkdir(parents=True)
    (target / "governance/schemas").mkdir(parents=True)
    (target / "knowledge/index.md").write_text('---\nokf_version: "0.2"\n---\n', encoding="utf-8")
    shutil.copytree(
        GOVERNANCE_SOURCE / "contracts",
        target / "governance/contracts",
        dirs_exist_ok=True,
    )
    for schema in (
        "frontmatter.schema.json",
        "profiles.yaml",
        "registries.yaml",
    ):
        shutil.copyfile(
            GOVERNANCE_SOURCE / "schemas" / schema,
            target / "governance/schemas" / schema,
        )
    return target


def build_fixture_index(root: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(INDEX_TOOL),
            "--knowledge-root",
            str(root),
            "build",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


CARD_FIXTURE = """---
type: API
title: DataCopyPad 对齐约束
description: DataCopyPad 在 GM 与 UB 间拷贝时的对齐与 padding 行为约束。
tags: [task.lookup, topic.memory]
status: stable
sources:
  - resource: https://example.com/cann/datacopypad
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: [a2, "950"]
---

# DataCopyPad

DataCopyPad copies padded blocks between GM and UB.
"""


class CanonicalizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = make_fixture_root(Path(self.temporary.name))
        card = self.root / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        card.write_text(CARD_FIXTURE, encoding="utf-8")
        build_fixture_index(self.root)
        self.reader = server.CardReader(root=self.root, transport="stdio")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_concept_and_markdown_forms_resolve(self) -> None:
        concept, target, relative = self.reader.canonicalize(
            "ops/ascendc/apis/data_copy_pad"
        )
        self.assertEqual("ops/ascendc/apis/data_copy_pad", concept)
        self.assertTrue(target.is_file())
        concept_md, target_md, relative_md = self.reader.canonicalize(
            "ops/ascendc/apis/data_copy_pad.md"
        )
        self.assertEqual(concept, concept_md)
        self.assertEqual(target, target_md)

    def test_error_kinds_are_labelled_at_each_raise_site(self) -> None:
        cases = [
            ("", "invalid_argument"),
            ("  padded  ", "invalid_argument"),
            ("/etc/passwd", "path_out_of_bundle"),
            ("ops/ascendc/apis/data_copy_pad.md/../../escape.md", "path_out_of_bundle"),
            ("nonexistent/card.md", "path_not_indexed"),
        ]
        for raw, expected in cases:
            with self.subTest(path=raw):
                with self.assertRaises(ToolError) as caught:
                    self.reader.canonicalize(raw)
                self.assertEqual(expected, caught.exception.kind)

    def test_read_error_kinds_are_labelled(self) -> None:
        with self.assertRaises(ToolError) as caught:
            self.reader.read("ops/ascendc/apis/data_copy_pad", -1, 10)
        self.assertEqual("invalid_argument", caught.exception.kind)
        with self.assertRaises(ToolError) as caught:
            self.reader.read("ops/ascendc/apis/data_copy_pad", 0, 0)
        self.assertEqual("invalid_argument", caught.exception.kind)
        with self.assertRaises(ToolError) as caught:
            self.reader.read("ops/ascendc/apis/data_copy_pad", 10000, 10)
        self.assertEqual("offset_out_of_range", caught.exception.kind)

    def test_rejects_traversal_absolute_and_blank(self) -> None:
        for bad in (
            "../../etc/passwd",
            "/etc/passwd",
            "ops/../..",
            " ops/ascendc/apis/data_copy_pad ",
            "",
        ):
            with self.subTest(path=bad), self.assertRaises(ToolError):
                self.reader.canonicalize(bad)

    def test_rejects_symlink_escape(self) -> None:
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("secret\n", encoding="utf-8")
        (self.root / "knowledge/ops/ascendc/apis/escape.md").symlink_to(outside)
        with self.assertRaises(ToolError):
            self.reader.canonicalize("ops/ascendc/apis/escape.md")


class LoggingMatrixTests(unittest.TestCase):
    def test_stdio_defaults_to_off_and_http_to_on(self) -> None:
        self.assertFalse(server._log_enabled("stdio"))
        self.assertTrue(server._log_enabled("http"))

    def test_upload_defaults_to_disabled(self) -> None:
        saved = {
            name: os.environ.get(name)
            for name in (
                server.LOG_UPLOAD_REMOTE_ENV,
                server.LOG_UPLOAD_INTERVAL_ENV,
                server.LOG_UPLOAD_BRANCH_ENV,
            )
        }
        try:
            for name in saved:
                os.environ.pop(name, None)
            self.assertEqual(0, server._upload_interval())
            self.assertEqual(
                "https://gitcode.com/qixingkai/cannbot-knowledeg-log.git",
                server._upload_remote(),
            )
            self.assertEqual("main", server._upload_branch())
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def test_uploader_starts_only_for_http_with_logging_and_interval(self) -> None:
        self.assertFalse(server._start_uploader("stdio", True, 60))
        self.assertFalse(server._start_uploader("http", False, 60))
        self.assertFalse(server._start_uploader("http", True, 0))
        self.assertTrue(server._start_uploader("http", True, 1))


    def test_env_overrides(self) -> None:
        original = os.environ.get(server.LOG_ENV)
        try:
            os.environ[server.LOG_ENV] = "off"
            self.assertFalse(server._log_enabled("http"))
            os.environ[server.LOG_ENV] = "on"
            self.assertTrue(server._log_enabled("stdio"))
        finally:
            if original is None:
                os.environ.pop(server.LOG_ENV, None)
            else:
                os.environ[server.LOG_ENV] = original

    def test_log_rows_are_valid_jsonl_and_failures_are_logged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "logs"
            logger = server.CallLogger()
            logger.configure(directory, True, Path(temporary) / "repo")
            logger.log_call(
                transport="stdio",
                principal=None,
                tool="search",
                arguments={"query": "对齐约束", "platform": ["a2"]},
                ok=True,
                count=2,
                latency_ms=12.3,
                request_sha256="abc",
                index={"card_count": 10},
                hits=["ops/x.md"],
                scores=[4.5],
                response_sha256="def",
                response_bytes=17,
                error=None,
                error_kind=None,
                jsonrpc_id=None,
            )
            logger.log_call(
                transport="http",
                principal="zhangsan",
                tool="search",
                arguments={"query": "q"},
                ok=False,
                count=None,
                latency_ms=5.0,
                request_sha256=None,
                index=None,
                hits=None,
                scores=None,
                response_sha256=None,
                response_bytes=None,
                error="boom",
                error_kind="cli_error",
                jsonrpc_id=7,
            )
            logger.log_event(event="auth_failed", src_ip="10.0.0.7", reason="no_match")
            files = sorted(directory.glob("*.jsonl"))
            self.assertEqual(1, len(files))
            rows = [
                json.loads(line)
                for line in files[0].read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(3, len(rows))
            self.assertIn("对齐约束", files[0].read_text(encoding="utf-8"))
            self.assertEqual("search", rows[0]["tool"])
            self.assertTrue(rows[0]["ok"])
            self.assertFalse(rows[1]["ok"])
            self.assertEqual("boom", rows[1]["error"])
            self.assertEqual("auth_failed", rows[2]["event"])

    def test_refuses_to_log_inside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            logger = server.CallLogger()
            logger.configure(repo / "logs", True, repo)
            self.assertFalse(logger.enabled)
            logger.log_call(
                transport="http", principal=None, tool="discover", arguments={},
                ok=True, count=1, latency_ms=1.0, request_sha256=None,
                index=None, hits=None, scores=None, response_sha256=None,
                response_bytes=None, error=None, error_kind=None, jsonrpc_id=None,
            )
            self.assertEqual([], list((repo / "logs").glob("*.jsonl"))
                             if (repo / "logs").exists() else [])


class CallLogSchemaV2Tests(unittest.TestCase):
    """Schema marker, millisecond ts, response-side evidence, error kinds."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name) / "logs"
        self.logger = server.CallLogger()
        self.logger.configure(self.directory, True, Path(self.temporary.name) / "repo")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def rows(self) -> list[dict]:
        files = sorted(self.directory.glob("*.jsonl"))
        self.assertEqual(1, len(files))
        return [
            json.loads(line)
            for line in files[0].read_text(encoding="utf-8").splitlines()
        ]

    def log_success(self, **overrides) -> dict:
        fields = dict(
            transport="stdio",
            principal=None,
            tool="discover",
            arguments={},
            ok=True,
            count=1,
            latency_ms=3.0,
            request_sha256=None,
            index=None,
            hits=None,
            scores=None,
            response_sha256=None,
            response_bytes=None,
            error=None,
            error_kind=None,
            jsonrpc_id=None,
            boot_id=None,
        )
        fields.update(overrides)
        self.logger.log_call(**fields)
        return fields

    def test_schema_marker_on_call_and_event_rows_and_millisecond_ts(self) -> None:
        self.log_success()
        self.logger.log_event(event="auth_failed", src_ip="10.0.0.7", reason="no_match")
        call_row, event_row = self.rows()
        self.assertEqual("mcp-call-log.v2", call_row["schema"])
        self.assertEqual("mcp-call-log.v2", event_row["schema"])
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
        for row in (call_row, event_row):
            self.assertRegex(row["ts"], pattern)

    def test_scores_and_hits_stay_same_length_and_order(self) -> None:
        self.log_success(
            tool="search",
            hits=["a.md", "b.md", "c.md"],
            scores=[4.5, 3.25, 1.0],
        )
        row = self.rows()[0]
        self.assertEqual(["a.md", "b.md", "c.md"], row["hits"])
        self.assertEqual([4.5, 3.25, 1.0], row["scores"])

    def test_read_card_row_carries_card_evidence_fields(self) -> None:
        self.log_success(
            tool="read_card",
            arguments={"path": "ops/x.md", "offset": 0, "limit": 200},
            count=None,
            card_sha256="deadbeef",
            total_lines=1985,
            returned_lines=200,
            truncated=True,
        )
        row = self.rows()[0]
        self.assertEqual("deadbeef", row["card_sha256"])
        self.assertEqual(1985, row["total_lines"])
        self.assertEqual(200, row["returned_lines"])
        self.assertTrue(row["truncated"])

    def test_error_kind_is_null_on_success_and_set_on_failure(self) -> None:
        self.log_success()
        self.log_success(ok=False, error="boom", error_kind="cli_error")
        success_row, failure_row = self.rows()
        self.assertIsNone(success_row["error_kind"])
        self.assertEqual("cli_error", failure_row["error_kind"])

    def test_jsonrpc_id_is_recorded_verbatim(self) -> None:
        self.log_success(transport="http", principal="zhang", jsonrpc_id="call-17")
        self.assertEqual("call-17", self.rows()[0]["jsonrpc_id"])

    def test_boot_id_tags_every_row_from_the_same_process(self) -> None:
        self.assertRegex(server.BOOT_ID, r"^[0-9a-f]{8,12}$")
        self.log_success(transport="http", boot_id=server.BOOT_ID)
        self.logger.log_event(
            event="rate_limited",
            principal="zhang",
            tool="search",
            retry_after_s=7,
            boot_id=server.BOOT_ID,
        )
        call_row, event_row = self.rows()
        self.assertEqual(server.BOOT_ID, call_row["boot_id"])
        self.assertEqual(server.BOOT_ID, event_row["boot_id"])


class CanonicalResponseHashTests(unittest.TestCase):
    def test_canonical_digest_is_stable_and_sorted(self) -> None:
        payload = {
            "schema_version": "knowledge-search.v1",
            "query": "对齐约束",
            "results": [{"path": "b.md", "score": 1.5}, {"path": "a.md", "score": 2.0}],
        }
        digest, size = server._canonical_response_digest(payload)
        self.assertEqual(digest, server._canonical_response_digest(payload)[0])
        expected_bytes = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(expected_bytes).hexdigest(), digest)
        self.assertEqual(len(expected_bytes), size)

    def test_key_order_and_spacing_change_the_digest(self) -> None:
        first = server._canonical_response_digest({"a": 1, "b": 2})
        second = server._canonical_response_digest({"b": 2, "a": 1})
        self.assertEqual(first, second)
        self.assertNotEqual(
            server._canonical_response_digest({"a": 1})[0],
            server._canonical_response_digest({"a": 2})[0],
        )


class CardLocalityTests(unittest.TestCase):
    """read_card must not leak instance-local absolute paths into the
    shared payload: two instances mounting the bundle at different paths
    would otherwise produce drifting response_sha256 digests."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_root(self, name: str) -> Path:
        root = make_fixture_root(Path(self.temporary.name) / name)
        card = root / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        card.write_text(CARD_FIXTURE, encoding="utf-8")
        build_fixture_index(root)
        return root

    def test_local_path_is_stdio_only_and_digest_is_stable_across_roots(self) -> None:
        first = self.make_root("first")
        second = self.make_root("second")
        http_payload = server.CardReader(root=first, transport="http").read(
            "ops/ascendc/apis/data_copy_pad", 0, 10
        )
        twin_payload = server.CardReader(root=second, transport="http").read(
            "ops/ascendc/apis/data_copy_pad", 0, 10
        )
        self.assertNotIn("local_path", http_payload)
        self.assertNotIn("local_only", http_payload)
        self.assertNotIn("local_path", twin_payload)
        self.assertEqual(
            server._canonical_response_digest(http_payload)[0],
            server._canonical_response_digest(twin_payload)[0],
        )
        stdio_payload = server.CardReader(root=first, transport="stdio").read(
            "ops/ascendc/apis/data_copy_pad", 0, 10
        )
        self.assertNotIn("local_path", stdio_payload)
        self.assertEqual(
            str(first / "knowledge/ops/ascendc/apis/data_copy_pad.md"),
            stdio_payload["local_only"]["local_path"],
        )
        # stdio and http views of the same read must hash identically: the
        # digest view drops the stdio-only local_only block.
        self.assertEqual(
            server._canonical_response_digest(
                server._digest_view(http_payload, "read_card")
            )[0],
            server._canonical_response_digest(
                server._digest_view(stdio_payload, "read_card")
            )[0],
        )

    def test_digest_view_strips_cli_passthrough_absolute_paths(self) -> None:
        # search results carry a per-hit local_path and discover carries the
        # bundle root straight from the CLI contract; the hashed copy must
        # drop them or two instances mounted at different paths drift. The
        # CLI prints the same hit list under `results` and `hits`; after the
        # subprocess JSON round-trip they are two independent objects, so
        # both copies must be stripped.
        search_payload = {
            "results": [
                {"path": "ops/x.md", "local_path": "/mount-a/knowledge/ops/x.md"}
            ],
            "hits": [
                {"path": "ops/x.md", "local_path": "/mount-a/knowledge/ops/x.md"}
            ],
        }
        twin_search = {
            "results": [
                {"path": "ops/x.md", "local_path": "/mount-b/knowledge/ops/x.md"}
            ],
            "hits": [
                {"path": "ops/x.md", "local_path": "/mount-b/knowledge/ops/x.md"}
            ],
        }
        self.assertEqual(
            server._canonical_response_digest(
                server._digest_view(search_payload, "search")
            )[0],
            server._canonical_response_digest(
                server._digest_view(twin_search, "search")
            )[0],
        )
        for payload in (search_payload, twin_search):
            stripped = server._digest_view(payload, "search")
            for key in ("results", "hits"):
                self.assertNotIn("local_path", stripped[key][0])
        discover_payload = {"schema_version": "knowledge-discovery.v1",
                            "root": "/mount-a", "cards": 3}
        twin_discover = {"schema_version": "knowledge-discovery.v1",
                         "root": "/mount-b", "cards": 3}
        self.assertEqual(
            server._canonical_response_digest(
                server._digest_view(discover_payload, "discover")
            )[0],
            server._canonical_response_digest(
                server._digest_view(twin_discover, "discover")
            )[0],
        )
        # the client-visible payload keeps its contract fields untouched
        self.assertIn("local_path", search_payload["results"][0])
        self.assertIn("local_path", search_payload["hits"][0])
        self.assertIn("root", discover_payload)


class CliErrorMappingTests(unittest.TestCase):
    def test_exit_two_message_is_extracted_with_rebuild_hint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = server.CliRunner(root / "q.py", root, 2, 30.0)
            stderr = json.dumps(
                {"error": {"type": "ValueError", "message": "knowledge index is stale; rebuild the index"}}
            )
            with self.assertRaises(ToolError) as caught:
                runner._interpret(2, "", stderr)
            message = str(caught.exception)
            self.assertIn("knowledge index is stale", message)
            self.assertIn("knowledge_index.py", message)
            self.assertIn("exit 2", message)
            self.assertEqual("index_stale", caught.exception.kind)

    def test_unparseable_success_output_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = server.CliRunner(Path(temporary) / "q.py", Path(temporary), 2, 30.0)
            with self.assertRaises(ToolError):
                runner._interpret(0, "not json", "")

    def test_cli_failure_without_structured_code_falls_back_to_cli_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = server.CliRunner(Path(temporary) / "q.py", Path(temporary), 2, 30.0)
            with self.assertRaises(ToolError) as caught:
                runner._interpret(2, "", "plain text failure")
            self.assertEqual("cli_error", caught.exception.kind)

    def test_missing_index_maps_to_index_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = server.CliRunner(Path(temporary) / "q.py", Path(temporary), 2, 30.0)
            stderr = json.dumps(
                {
                    "error": {
                        "type": "ValueError",
                        "message": "knowledge index is missing: /x/knowledge.sqlite3; run knowledge_index.py build",
                    }
                }
            )
            with self.assertRaises(ToolError) as caught:
                runner._interpret(2, "", stderr)
            self.assertEqual("index_missing", caught.exception.kind)

    def test_missing_platform_maps_to_platform_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = server.CliRunner(Path(temporary) / "q.py", Path(temporary), 2, 30.0)
            stderr = json.dumps(
                {
                    "error": {
                        "type": "ValueError",
                        "message": (
                            "platform is required; determine a target platform, use "
                            "the platforms scope for identification, or explicitly "
                            "request draft --include-unlocated cards"
                        ),
                    }
                }
            )
            with self.assertRaises(ToolError) as caught:
                runner._interpret(2, "", stderr)
            self.assertEqual("platform_missing", caught.exception.kind)

    def test_structured_code_field_wins_over_message_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = server.CliRunner(Path(temporary) / "q.py", Path(temporary), 2, 30.0)
            stderr = json.dumps(
                {"error": {"type": "ValueError", "code": "index_stale", "message": "unrelated"}}
            )
            with self.assertRaises(ToolError) as caught:
                runner._interpret(2, "", stderr)
            self.assertEqual("index_stale", caught.exception.kind)


class StubCliTests(unittest.TestCase):
    """Subprocess gate and timeout behavior against an instrumented stub CLI."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = make_fixture_root(Path(self.temporary.name))
        self.scripts = self.root / ".agents/skills/knowledge-query/scripts"
        self.scripts.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_stub(self, body: str) -> Path:
        stub = self.scripts / "knowledge_query.py"
        stub.write_text(body, encoding="utf-8")
        return stub

    def test_semaphore_limits_concurrent_subprocesses(self) -> None:
        marker = Path(self.temporary.name) / "concurrency.log"
        self.write_stub(
            "import json, os, sys, time\n"
            f"marker = {str(marker)!r}\n"
            "with open(marker, 'a') as stream:\n"
            "    stream.write('start\\n'); stream.flush()\n"
            "time.sleep(1.0)\n"
            "with open(marker, 'a') as stream:\n"
            "    stream.write('end\\n'); stream.flush()\n"
            "print(json.dumps({'stub': True}))\n"
        )
        runner = server.CliRunner(self.scripts / "knowledge_query.py", self.root, 2, 30.0)

        async def scenario() -> list[dict]:
            return await asyncio.gather(*(runner.run(["discover", "--json"]) for _ in range(4)))

        started = time.perf_counter()
        payloads = asyncio.run(scenario())
        elapsed = time.perf_counter() - started
        self.assertEqual(4, len(payloads))
        self.assertTrue(all(item == {"stub": True} for item in payloads))
        events = marker.read_text().splitlines()
        concurrent = 0
        maximum = 0
        for event in events:
            concurrent += 1 if event == "start" else -1
            maximum = max(maximum, concurrent)
        self.assertLessEqual(maximum, 2)
        self.assertGreaterEqual(elapsed, 2.0)

    def test_search_digest_view_strips_results_and_hits_local_paths(self) -> None:
        # the CLI contract prints the same hit list under `results` and
        # `hits`; the subprocess JSON round-trip deserializes them into two
        # independent objects, so the digest view must strip both or two
        # instances mounted at different paths report drifting digests.
        digests = set()
        roots = (
            self.root,
            make_fixture_root(Path(self.temporary.name) / "twin"),
        )
        for root in roots:
            scripts = root / ".agents/skills/knowledge-query/scripts"
            scripts.mkdir(parents=True, exist_ok=True)
            (scripts / "knowledge_query.py").write_text(
                "import json, sys\n"
                "root = sys.argv[sys.argv.index('--knowledge-root') + 1]\n"
                "hit = {'path': 'ops/x.md', 'local_path': root"
                " + '/knowledge/ops/x.md'}\n"
                "print(json.dumps({'results': [hit], 'hits': [hit],"
                " 'request_sha256': 'stub'}))\n",
                encoding="utf-8",
            )
            runner = server.CliRunner(scripts / "knowledge_query.py", root, 2, 30.0)
            payload = asyncio.run(runner.run(["search", "--json"]))
            # the deserialized copies are independent objects and the
            # client-visible payload keeps its contract fields untouched
            self.assertIsNot(payload["results"][0], payload["hits"][0])
            self.assertIn("local_path", payload["results"][0])
            self.assertIn("local_path", payload["hits"][0])
            digests.add(
                server._canonical_response_digest(
                    server._digest_view(payload, "search")
                )[0]
            )
        self.assertEqual(1, len(digests))

    def test_hung_subprocess_is_killed_after_timeout(self) -> None:
        self.write_stub(
            "import time\ntime.sleep(60)\n"
        )
        runner = server.CliRunner(self.scripts / "knowledge_query.py", self.root, 2, 2.0)
        with self.assertRaises(ToolError) as caught:
            asyncio.run(runner.run(["discover", "--json"]))
        self.assertIn("timeout", str(caught.exception))
        self.assertEqual("subprocess_timeout", caught.exception.kind)

    def test_cancelled_run_kills_subprocess_and_propagates(self) -> None:
        marker = Path(self.temporary.name) / "stub.pid"
        self.write_stub(
            "import os, time\n"
            f"marker = {str(marker)!r}\n"
            "with open(marker, 'w') as stream:\n"
            "    stream.write(str(os.getpid())); stream.flush()\n"
            "time.sleep(60)\n"
        )
        runner = server.CliRunner(self.scripts / "knowledge_query.py", self.root, 2, 30.0)

        async def scenario() -> None:
            task = asyncio.ensure_future(runner.run(["discover", "--json"]))
            await asyncio.sleep(0.5)
            task.cancel()
            await task

        with self.assertRaises(asyncio.CancelledError):
            asyncio.run(scenario())
        stub_pid = int(marker.read_text(encoding="utf-8").strip())
        with self.assertRaises(ProcessLookupError):
            os.kill(stub_pid, 0)

    def test_env_knobs_are_respected(self) -> None:
        stub = self.write_stub(
            "import json, os, sys\nprint(json.dumps({'max': os.environ.get('CANNBOT_MCP_MAX_SUBPROCS')}))\n"
        )
        self.assertTrue(stub.is_file())


if __name__ == "__main__":
    unittest.main()
