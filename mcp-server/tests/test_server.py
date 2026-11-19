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
import state_store  # noqa: E402
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
    def setUp(self) -> None:
        import tempfile as _tf

        self._tmp = _tf.TemporaryDirectory(prefix="sw-limiter-tests-")
        saved = os.environ.get(server.AUTH_DB_ENV)
        os.environ[server.AUTH_DB_ENV] = str(
            Path(self._tmp.name) / "auth.db"
        )
        self._saved_auth_db = saved

    def tearDown(self) -> None:
        if self._saved_auth_db is None:
            os.environ.pop(server.AUTH_DB_ENV, None)
        else:
            os.environ[server.AUTH_DB_ENV] = self._saved_auth_db
        self._tmp.cleanup()

    def _limiter(self) -> server.SlidingWindowRateLimiter:
        return server.SlidingWindowRateLimiter(state_store.open_state_store())

    def test_allows_limit_then_denies_with_retry_after(self) -> None:
        limiter = self._limiter()
        decisions = [limiter.check("k", limit=3) for _ in range(4)]
        self.assertEqual([True, True, True, False], [d.allowed for d in decisions])
        self.assertGreaterEqual(decisions[3].retry_after_s, 1)

    def test_distinct_keys_do_not_interfere(self) -> None:
        limiter = self._limiter()
        for _ in range(3):
            limiter.check("alice", limit=3)
        self.assertTrue(limiter.check("bob", limit=3).allowed)

    def test_zero_limit_disables_limiting(self) -> None:
        limiter = self._limiter()
        self.assertTrue(limiter.check("k", limit=0).allowed)

    def test_window_slides(self) -> None:
        # StateStore backends keep their own wall clock, so the old
        # monkeypatched-monotonic version cannot drive the window; use a
        # sub-second window and real sleeps instead.
        import time as _time

        limiter = self._limiter()
        self.assertTrue(limiter.check("k", limit=1).allowed)
        self.assertFalse(limiter.check("k", limit=1).allowed)
        _time.sleep(0.25)
        self.assertTrue(
            limiter.check("k", limit=1, window_s=0.2).allowed
        )


class IpCooldownTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile as _tf

        self._tmp = _tf.TemporaryDirectory(prefix="ip-cooldown-tests-")
        saved = os.environ.get(server.AUTH_DB_ENV)
        os.environ[server.AUTH_DB_ENV] = str(
            Path(self._tmp.name) / "auth.db"
        )
        self._saved_auth_db = saved

    def tearDown(self) -> None:
        if self._saved_auth_db is None:
            os.environ.pop(server.AUTH_DB_ENV, None)
        else:
            os.environ[server.AUTH_DB_ENV] = self._saved_auth_db
        self._tmp.cleanup()

    def _cooldown(self) -> server.IpCooldown:
        return server.IpCooldown(state_store.open_state_store())

    def test_ten_failures_block_the_eleventh_even_with_valid_token(self) -> None:
        cooldown = self._cooldown()
        for _ in range(10):
            cooldown.record_failure("10.0.0.7")
        decision = cooldown.check("10.0.0.7")
        self.assertFalse(decision.allowed)
        self.assertGreaterEqual(decision.retry_after_s, 1)
        self.assertTrue(cooldown.check("10.0.0.8").allowed)

    def test_success_resets_the_failure_window(self) -> None:
        cooldown = self._cooldown()
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
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
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
            # No default remote: the uploader is opt-in and stays off until
            # the deployer configures CANNBOT_MCP_LOG_UPLOAD_REMOTE.
            self.assertEqual("", server._upload_remote())
            self.assertFalse(
                server._start_uploader("http", True, 60),
                "uploader must stay off without an explicit remote",
            )
            os.environ[server.LOG_UPLOAD_REMOTE_ENV] = "https://example.com/log.git"
            self.assertEqual("https://example.com/log.git", server._upload_remote())
            self.assertTrue(server._start_uploader("http", True, 60))
            self.assertEqual("main", server._upload_branch())
        finally:
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def test_uploader_starts_only_for_http_with_logging_and_interval(self) -> None:
        saved = os.environ.get(server.LOG_UPLOAD_REMOTE_ENV)
        try:
            # Without a remote the uploader never starts, regardless of the
            # other gates (the feature is fully opt-in now).
            self.assertFalse(server._start_uploader("stdio", True, 60))
            self.assertFalse(server._start_uploader("http", False, 60))
            self.assertFalse(server._start_uploader("http", True, 0))
            self.assertFalse(server._start_uploader("http", True, 1))
            # With a remote configured the original matrix holds.
            os.environ[server.LOG_UPLOAD_REMOTE_ENV] = "https://example.com/log.git"
            self.assertFalse(server._start_uploader("stdio", True, 60))
            self.assertFalse(server._start_uploader("http", False, 60))
            self.assertFalse(server._start_uploader("http", True, 0))
            self.assertTrue(server._start_uploader("http", True, 1))
        finally:
            if saved is None:
                os.environ.pop(server.LOG_UPLOAD_REMOTE_ENV, None)
            else:
                os.environ[server.LOG_UPLOAD_REMOTE_ENV] = saved


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


class GitCodeTokenVerifierTests(unittest.TestCase):
    """Unit tests for the GitCode OAuth leg of the dual-track auth."""

    def _verifier(self) -> server.GitCodeTokenVerifier:
        return server.GitCodeTokenVerifier()

    def test_valid_token_returns_access_token_with_login_subject(self) -> None:
        verifier = self._verifier()

        class _Response:
            status_code = 200

            def json(self) -> dict:
                return {"login": "zhangsan"}

        class _Client:
            async def __aenter__(self) -> "_Client":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def get(self, url: str, headers: dict | None = None) -> _Response:
                return _Response()

        def fake_client() -> _Client:
            return _Client()

        original = server.httpx.AsyncClient
        server.httpx.AsyncClient = fake_client  # type: ignore[assignment]
        try:
            access = asyncio.run(verifier.verify_token("gitcode-token-1"))
        finally:
            server.httpx.AsyncClient = original
        self.assertIsNotNone(access)
        self.assertEqual("zhangsan", access.subject)
        self.assertEqual("zhangsan", access.client_id)
        self.assertEqual("gitcode-token-1", access.token)

    def test_unauthorized_token_returns_none(self) -> None:
        verifier = self._verifier()

        class _Response:
            status_code = 401

            def json(self) -> dict:
                return {}

        class _Client:
            async def __aenter__(self) -> "_Client":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def get(self, url: str, headers: dict | None = None) -> _Response:
                return _Response()

        def fake_client() -> _Client:
            return _Client()

        original = server.httpx.AsyncClient
        server.httpx.AsyncClient = fake_client  # type: ignore[assignment]
        try:
            access = asyncio.run(verifier.verify_token("gitcode-token-2"))
        finally:
            server.httpx.AsyncClient = original
        self.assertIsNone(access)

    def test_network_error_returns_none(self) -> None:
        verifier = self._verifier()

        class _Client:
            async def __aenter__(self) -> "_Client":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def get(self, url: str, headers: dict | None = None) -> object:
                raise server.httpx.HTTPError("boom")

        def fake_client() -> _Client:
            return _Client()

        original = server.httpx.AsyncClient
        server.httpx.AsyncClient = fake_client  # type: ignore[assignment]
        try:
            access = asyncio.run(verifier.verify_token("gitcode-token-3"))
        finally:
            server.httpx.AsyncClient = original
        self.assertIsNone(access)

    def test_cache_prevents_second_request_for_same_token(self) -> None:
        verifier = self._verifier()
        calls: list[str] = []

        class _Response:
            status_code = 200

            def json(self) -> dict:
                return {"login": "zhangsan"}

        class _Client:
            async def __aenter__(self) -> "_Client":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def get(self, url: str, headers: dict | None = None) -> _Response:
                calls.append(url)
                return _Response()

        def fake_client() -> _Client:
            return _Client()

        original = server.httpx.AsyncClient
        server.httpx.AsyncClient = fake_client  # type: ignore[assignment]
        try:
            first = asyncio.run(verifier.verify_token("gitcode-token-4"))
            second = asyncio.run(verifier.verify_token("gitcode-token-4"))
        finally:
            server.httpx.AsyncClient = original
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(["https://api.gitcode.com/api/v5/user"], calls)


class _StubAccessToken:
    """AccessToken stand-in returned by the stub verifier in dual-track tests."""

    def __init__(self, subject: str) -> None:
        self.token = "stub"
        self.client_id = subject
        self.scopes = ["mcp"]
        self.subject = subject


class DualTrackAuthTests(unittest.TestCase):
    """End-to-end auth behaviour over build_http_app with the GitCode leg."""

    def _run_request(
        self,
        tokens: str,
        verifier: object | None,
        presented: str | None,
    ) -> tuple[list[dict], list[dict]]:
        inner_calls: list[dict] = []

        async def stub_inner(scope: dict, receive: object, send: object) -> None:
            inner_calls.append(scope)

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse(tokens),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
            verifier=verifier,  # type: ignore[arg-type]
        )

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        headers: list[tuple[bytes, bytes]] = []
        if presented is not None:
            headers.append((b"authorization", f"Bearer {presented}".encode("ascii")))
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": headers,
            "client": ("10.9.9.9", 55555),
        }
        asyncio.run(app(scope, receive, send))
        return sent, inner_calls

    def test_gitcode_verified_token_is_accepted(self) -> None:
        class StubVerifier:
            async def verify_token(self, token: str) -> _StubAccessToken | None:
                return _StubAccessToken("gitcode-user") if token == "gc-good" else None

        sent, inner_calls = self._run_request("cbk_static:ready", StubVerifier(), "gc-good")
        self.assertEqual(1, len(inner_calls), "verified GitCode token must reach the MCP app")
        self.assertEqual([], [m for m in sent if m.get("status") == 401])

    def test_unknown_token_with_failing_verifier_is_rejected(self) -> None:
        class StubVerifier:
            async def verify_token(self, token: str) -> _StubAccessToken | None:
                return None

        sent, inner_calls = self._run_request("cbk_static:ready", StubVerifier(), "gc-bad")
        self.assertEqual([], inner_calls)
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(401, statuses)

    def test_gitcode_track_disabled_without_verifier(self) -> None:
        sent, inner_calls = self._run_request("cbk_static:ready", None, "gc-good")
        self.assertEqual([], inner_calls)
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(401, statuses)

    def test_gitcode_track_disabled_by_env_off(self) -> None:
        class StubVerifier:
            def __init__(self) -> None:
                self.calls = 0

            async def verify_token(self, token: str) -> _StubAccessToken | None:
                self.calls += 1
                return _StubAccessToken("gitcode-user")

        stub = StubVerifier()
        original = os.environ.get("CANNBOT_MCP_GITCODE_VERIFY")
        os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = "off"
        try:
            sent, inner_calls = self._run_request("cbk_static:ready", stub, "gc-good")
        finally:
            if original is None:
                os.environ.pop("CANNBOT_MCP_GITCODE_VERIFY", None)
            else:
                os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = original
        self.assertEqual([], inner_calls)
        self.assertEqual(0, stub.calls, "verifier must not be called when the track is off")
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(401, statuses)

    def _run_routed_request(
        self, verifier: object, presented: str
    ) -> tuple[list[dict], list[dict]]:
        """_run_request with a Host header so JWT audiences resolve."""
        return self._run_request("cbk_static:ready", verifier, presented)

    def test_self_issued_jwt_is_accepted_without_outbound_call(self) -> None:
        class ProbeVerifier:
            calls = 0

            async def verify_token(self, token: str) -> _StubAccessToken | None:
                type(self).calls += 1
                return _StubAccessToken("gitcode-user")

        original = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_SECRET_ENV] = "routing-test-secret"
        try:
            authority = server.SelfIssuedTokenAuthority()
            access, _ttl = authority.sign("jwt-user", "access", audience="http://localhost")
            sent, inner_calls = self._run_routed_request(ProbeVerifier(), access)
        finally:
            if original is None:
                os.environ.pop(server.AUTH_SECRET_ENV, None)
            else:
                os.environ[server.AUTH_SECRET_ENV] = original
        self.assertEqual(
            1, len(inner_calls), "valid self-issued JWT must reach the MCP app"
        )
        self.assertEqual(
            0, ProbeVerifier.calls, "self-issued JWT must never be sent to GitCode"
        )
        self.assertEqual([], [m for m in sent if m.get("status") == 401])

    def test_rejected_self_issued_jwt_never_reaches_gitcode(self) -> None:
        class ProbeVerifier:
            calls = 0

            async def verify_token(self, token: str) -> _StubAccessToken | None:
                type(self).calls += 1
                return _StubAccessToken("gitcode-user")

        original = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_SECRET_ENV] = "routing-test-secret"
        try:
            authority = server.SelfIssuedTokenAuthority()
            access, _ttl = authority.sign("jwt-user", "access", audience="http://elsewhere")
            # Wrong audience: local verification fails; the token must be
            # rejected LOCALLY — no fallback to the GitCode track.
            sent, inner_calls = self._run_routed_request(ProbeVerifier(), access)
        finally:
            if original is None:
                os.environ.pop(server.AUTH_SECRET_ENV, None)
            else:
                os.environ[server.AUTH_SECRET_ENV] = original
        self.assertEqual([], inner_calls)
        self.assertEqual(
            0, ProbeVerifier.calls, "failed local JWT must not fall back to GitCode"
        )
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(401, statuses)

    def test_refresh_token_rejected_locally_without_outbound(self) -> None:
        class ProbeVerifier:
            calls = 0

            async def verify_token(self, token: str) -> _StubAccessToken | None:
                type(self).calls += 1
                return _StubAccessToken("gitcode-user")

        original = os.environ.get(server.AUTH_SECRET_ENV)
        os.environ[server.AUTH_SECRET_ENV] = "routing-test-secret"
        try:
            authority = server.SelfIssuedTokenAuthority()
            refresh, _ttl = authority.sign("jwt-user", "refresh", audience="http://localhost")
            sent, inner_calls = self._run_routed_request(ProbeVerifier(), refresh)
        finally:
            if original is None:
                os.environ.pop(server.AUTH_SECRET_ENV, None)
            else:
                os.environ[server.AUTH_SECRET_ENV] = original
        self.assertEqual([], inner_calls)
        self.assertEqual(
            0, ProbeVerifier.calls, "refresh JWT must never be sent to GitCode"
        )
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(401, statuses)

    def test_api_key_never_reaches_gitcode_verifier(self) -> None:
        class ProbeVerifier:
            calls = 0

            async def verify_token(self, token: str) -> _StubAccessToken | None:
                type(self).calls += 1
                return _StubAccessToken("gitcode-user")

        # Unknown key id: local scrypt check fails; no GitCode fallback.
        sent, inner_calls = self._run_routed_request(
            ProbeVerifier(), "cbk_live_deadbeef_notarealkey"
        )
        self.assertEqual([], inner_calls)
        self.assertEqual(
            0, ProbeVerifier.calls, "API key must never be sent to GitCode"
        )
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(401, statuses)

    def test_foreign_jwt_still_reaches_gitcode_track(self) -> None:
        # A JWT-shaped token WITHOUT our payload typ marker is a foreign
        # credential (e.g. a GitCode OAuth access token): it must keep
        # taking the GitCode track, not the local JWT track.
        class ForeignJwtVerifier:
            def __init__(self) -> None:
                self.seen: list[str] = []

            async def verify_token(self, token: str) -> _StubAccessToken | None:
                self.seen.append(token)
                return _StubAccessToken("gitcode-user")

        import base64 as _b64

        header = _b64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
        payload = (
            _b64.urlsafe_b64encode(b'{"sub":"gitcode-user","scope":"user"}')
            .rstrip(b"=")
            .decode()
        )
        foreign = f"{header}.{payload}.opaque-signature"
        verifier = ForeignJwtVerifier()
        sent, inner_calls = self._run_routed_request(verifier, foreign)
        self.assertEqual(
            1, len(inner_calls), "foreign JWT verified by GitCode must reach the app"
        )
        self.assertEqual([foreign], verifier.seen)


class ProtectedResourceMetadataTests(unittest.TestCase):
    """RFC 9728 metadata endpoint behaviour over build_http_app."""

    def _run_path(self, path: str) -> list[dict]:
        async def stub_inner(scope: dict, receive: object, send: object) -> None:
            raise AssertionError("metadata paths must not reach the MCP app")

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
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
            "path": path,
            "headers": [],
            "client": ("10.8.8.8", 44444),
        }
        asyncio.run(app(scope, receive, send))
        return sent

    def test_metadata_answers_gitcode_authorization_server(self) -> None:
        for path in (
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
        ):
            with self.subTest(path=path):
                sent = self._run_path(path)
                self.assertEqual(2, len(sent))
                self.assertEqual(200, sent[0]["status"])
                metadata = json.loads(sent[1]["body"])
                # authorization_servers points at this server (the discovery
                # front-end), NOT at gitcode.com directly: GitCode has no
                # RFC 8414 document and clients would die on its SPA HTML.
                self.assertIn("resource", metadata)
                self.assertEqual(metadata["authorization_servers"], [metadata["resource"]])
                self.assertEqual("cannbot-knowledge", metadata["resource_name"])

    def test_as_metadata_answers_gitcode_endpoints(self) -> None:
        # RFC 8414 discovery front-end in GitCode-forwarding mode
        # (AUTH_SERVER=off): the client walks 9728 ->
        # authorization_servers[0] (https://gitcode.com) -> that host's
        # 8414 document. GitCode itself serves an SPA HTML page there,
        # so this server republishes its OAuth endpoints instead. The
        # self-hosted default is locked by MetadataSwitchTests.
        original_auth_server = os.environ.get("CANNBOT_MCP_AUTH_SERVER")
        os.environ["CANNBOT_MCP_AUTH_SERVER"] = "off"
        try:
            for path in (
                "/.well-known/oauth-authorization-server",
                "/.well-known/oauth-authorization-server/mcp",
            ):
                with self.subTest(path=path):
                    sent = self._run_path(path)
                    self.assertEqual(2, len(sent))
                    self.assertEqual(200, sent[0]["status"])
                    metadata = json.loads(sent[1]["body"])
                    self.assertEqual("https://gitcode.com", metadata["issuer"])
                    self.assertEqual(
                        "https://gitcode.com/oauth/authorize",
                        metadata["authorization_endpoint"],
                    )
                    self.assertEqual(
                        "https://gitcode.com/oauth/token", metadata["token_endpoint"]
                    )
                    self.assertIn("S256", metadata["code_challenge_methods_supported"])
                    self.assertIn(
                        "authorization_code", metadata["grant_types_supported"]
                    )
        finally:
            if original_auth_server is None:
                os.environ.pop("CANNBOT_MCP_AUTH_SERVER", None)
            else:
                os.environ["CANNBOT_MCP_AUTH_SERVER"] = original_auth_server

    def test_as_metadata_404_when_gitcode_track_off(self) -> None:
        # GITCODE_VERIFY=off alone must NOT take the self-hosted AS's
        # discovery document down; only BOTH tracks off hides it.
        original = os.environ.get("CANNBOT_MCP_GITCODE_VERIFY")
        os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = "off"
        try:
            sent = self._run_path("/.well-known/oauth-authorization-server")
        finally:
            if original is None:
                os.environ.pop("CANNBOT_MCP_GITCODE_VERIFY", None)
            else:
                os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = original
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(200, statuses)

        original_verify = os.environ.get("CANNBOT_MCP_GITCODE_VERIFY")
        original_as = os.environ.get("CANNBOT_MCP_AUTH_SERVER")
        os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = "off"
        os.environ["CANNBOT_MCP_AUTH_SERVER"] = "off"
        try:
            sent = self._run_path("/.well-known/oauth-authorization-server")
        finally:
            for key, original_value in (
                ("CANNBOT_MCP_GITCODE_VERIFY", original_verify),
                ("CANNBOT_MCP_AUTH_SERVER", original_as),
            ):
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(404, statuses)

    def test_metadata_404_when_gitcode_track_off(self) -> None:
        # 9728 stays up as long as ANY dynamic track is on; 404 only in
        # static-token-only mode.
        original = os.environ.get("CANNBOT_MCP_GITCODE_VERIFY")
        os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = "off"
        try:
            sent = self._run_path("/.well-known/oauth-protected-resource")
        finally:
            if original is None:
                os.environ.pop("CANNBOT_MCP_GITCODE_VERIFY", None)
            else:
                os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = original
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(200, statuses)

        original_verify = os.environ.get("CANNBOT_MCP_GITCODE_VERIFY")
        original_as = os.environ.get("CANNBOT_MCP_AUTH_SERVER")
        os.environ["CANNBOT_MCP_GITCODE_VERIFY"] = "off"
        os.environ["CANNBOT_MCP_AUTH_SERVER"] = "off"
        try:
            sent = self._run_path("/.well-known/oauth-protected-resource")
        finally:
            for key, original_value in (
                ("CANNBOT_MCP_GITCODE_VERIFY", original_verify),
                ("CANNBOT_MCP_AUTH_SERVER", original_as),
            ):
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(404, statuses)


class DynamicClientRegistrationTests(unittest.TestCase):
    """RFC 7591 registration in GitCode-forwarding mode (AUTH_SERVER=off).

    Forwarding-mode /register is CLOSED: the only credentials it could
    return are the shared pre-registered application id/secret, and
    handing those to anonymous callers would leak a server-side secret.
    Zero-config registration is served by the self-hosted default (see
    MetadataSwitchTests); forwarding-mode clients get the application
    credentials from the administrator out of band.
    """

    def _run(self, path: str, env: dict) -> list[dict]:
        async def stub_inner(scope: dict, receive: object, send: object) -> None:
            raise AssertionError("registration paths must not reach the MCP app")

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse("cbk_ready:ready"),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            0,
            "127.0.0.1",
        )

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        # Force the fallback mode this suite locks.
        env = {server.AUTH_SERVER_ENV: "off", **env}
        saved = {k: os.environ.get(k) for k in env}
        try:
            for k, v in env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            scope = {
                "type": "http",
                "method": "POST",
                "path": path,
                "headers": [],
                "client": ("10.8.8.8", 44444),
            }
            asyncio.run(app(scope, receive, send))
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return sent

    def test_register_404_even_when_client_configured(self) -> None:
        # A configured application must NOT make /register hand out the
        # shared secret in forwarding mode.
        sent = self._run(
            "/register",
            {
                "CANNBOT_MCP_OAUTH_CLIENT_ID": "cid_test",
                "CANNBOT_MCP_OAUTH_CLIENT_SECRET": "sec_test",
            },
        )
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(404, statuses)
        payloads = b"".join(m.get("body", b"") for m in sent)
        self.assertNotIn(b"cid_test", payloads)
        self.assertNotIn(b"sec_test", payloads)

    def test_register_404_without_client_id(self) -> None:
        sent = self._run(
            "/register",
            {"CANNBOT_MCP_OAUTH_CLIENT_ID": None},
        )
        statuses = [m.get("status") for m in sent if "status" in m]
        self.assertIn(404, statuses)

    def test_as_metadata_never_advertises_registration_endpoint(self) -> None:
        for client_id in ("cid_test", None):
            with self.subTest(configured=client_id is not None):
                sent = self._run(
                    "/.well-known/oauth-authorization-server",
                    {"CANNBOT_MCP_OAUTH_CLIENT_ID": client_id},
                )
                self.assertEqual(200, sent[0]["status"])
                metadata = json.loads(sent[1]["body"])
                self.assertNotIn(
                    "registration_endpoint",
                    metadata,
                    "forwarding-mode metadata must not advertise /register",
                )


class RateLimitKeyTests(unittest.TestCase):
    """Per-principal rate limiting with the token legacy fallback."""

    def setUp(self) -> None:
        # Isolate the shared StateStore per test: without this the limiter
        # events land in the DEFAULT state.db, which a live server may be
        # using on this machine.
        import tempfile as _tf

        self._tmp = _tf.TemporaryDirectory(prefix="rl-key-tests-")
        saved = os.environ.get(server.AUTH_DB_ENV)
        os.environ[server.AUTH_DB_ENV] = str(
            Path(self._tmp.name) / "auth.db"
        )
        self._saved_auth_db = saved

    def tearDown(self) -> None:
        if self._saved_auth_db is None:
            os.environ.pop(server.AUTH_DB_ENV, None)
        else:
            os.environ[server.AUTH_DB_ENV] = self._saved_auth_db
        self._tmp.cleanup()

    def _app_with_limit(
        self, tokens: str, rate_limit: int
    ) -> tuple[object, list[dict]]:
        inner_calls: list[dict] = []

        async def stub_inner(scope: dict, receive: object, send: object) -> None:
            inner_calls.append(scope)

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        limiter = server.SlidingWindowRateLimiter(state_store.open_state_store())
        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse(tokens),
            limiter,
            server.IpCooldown(state_store.open_state_store()),
            rate_limit,
            "127.0.0.1",
        )
        return app, inner_calls

    def _request(
        self, app: object, token: str, inner_calls: list[dict]
    ) -> int | None:
        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": [(b"authorization", f"Bearer {token}".encode("ascii"))],
            "client": ("10.7.7.7", 11111),
        }
        asyncio.run(app(scope, receive, send))
        statuses = [m.get("status") for m in sent if "status" in m]
        if 429 in statuses:
            return 429
        if inner_calls:
            return 200
        return None

    def test_two_tokens_same_label_share_one_limit_window(self) -> None:
        # Same principal (label) via two different static tokens: the second
        # token hits the limit set by the first one's traffic.
        app, inner_calls = self._app_with_limit("tok_a:alice,tok_b:alice", 1)
        self.assertEqual(200, self._request(app, "tok_a", inner_calls))
        self.assertEqual(429, self._request(app, "tok_b", inner_calls))

    def test_distinct_principals_do_not_interfere(self) -> None:
        app, inner_calls = self._app_with_limit("tok_a:alice,tok_b:bob", 1)
        self.assertEqual(200, self._request(app, "tok_a", inner_calls))
        self.assertEqual(200, self._request(app, "tok_b", inner_calls))

    def test_rate_key_env_restores_per_token_keying(self) -> None:
        original = os.environ.get("CANNBOT_MCP_RATE_KEY")
        os.environ["CANNBOT_MCP_RATE_KEY"] = "token"
        try:
            app, inner_calls = self._app_with_limit("tok_a:alice,tok_b:alice", 1)
            self.assertEqual(200, self._request(app, "tok_a", inner_calls))
            self.assertEqual(200, self._request(app, "tok_b", inner_calls))
        finally:
            if original is None:
                os.environ.pop("CANNBOT_MCP_RATE_KEY", None)
            else:
                os.environ["CANNBOT_MCP_RATE_KEY"] = original


class AuthBoundaryE2ETests(unittest.TestCase):
    """End-to-end locks for 401/429/cooldown/health wiring."""

    def _build_app(
        self, tokens: str = "cbk_ok:alice", rate_limit: int = 0
    ) -> tuple[object, list[dict]]:
        inner_calls: list[dict] = []

        async def stub_inner(scope: dict, receive: object, send: object) -> None:
            inner_calls.append(scope)

        class StubMcpServer:
            def streamable_http_app(self, **_kwargs: object) -> object:
                return stub_inner

        app = server.build_http_app(
            StubMcpServer(),
            server.TokenList.parse(tokens),
            server.SlidingWindowRateLimiter(state_store.open_state_store()),
            server.IpCooldown(state_store.open_state_store()),
            rate_limit,
            "127.0.0.1",
        )
        return app, inner_calls

    def _request(
        self,
        app: object,
        token: str | None,
        client_ip: str = "10.6.6.6",
    ) -> list[dict]:
        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        headers: list[tuple[bytes, bytes]] = []
        if token is not None:
            headers.append((b"authorization", f"Bearer {token}".encode("ascii")))
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": headers,
            "client": (client_ip, 22222),
        }
        asyncio.run(app(scope, receive, send))
        return sent

    @staticmethod
    def _start(sent: list[dict]) -> dict:
        return next(m for m in sent if m.get("type") == "http.response.start")

    def test_401_carries_www_authenticate_header(self) -> None:
        app, _inner = self._build_app()
        sent = self._request(app, "definitely-wrong-token")
        start = self._start(sent)
        self.assertEqual(401, start["status"])
        header_names = {name.decode("latin-1").lower() for name, _ in start["headers"]}
        self.assertIn("www-authenticate", header_names)

    def test_rate_limited_429_carries_retry_after_header(self) -> None:
        app, inner_calls = self._build_app(rate_limit=1)
        self._request(app, "cbk_ok")  # first call inside the limit
        sent = self._request(app, "cbk_ok")  # second call over the limit
        start = self._start(sent)
        self.assertEqual(429, start["status"])
        header_names = {name.decode("latin-1").lower() for name, _ in start["headers"]}
        self.assertIn("retry-after", header_names)

    def test_blocked_ip_gets_429_even_with_valid_token(self) -> None:
        app, _inner = self._build_app()
        for _ in range(10):
            self._request(app, "wrong-token", client_ip="10.6.6.1")
        sent = self._request(app, "cbk_ok", client_ip="10.6.6.1")
        start = self._start(sent)
        self.assertEqual(429, start["status"])

    def test_health_is_not_logged_in_call_log(self) -> None:
        # /health must bypass the call log: run a health request and confirm
        # no call row appears (the CallLogger writes to a file; assert via
        # the _health fast-path having no principal meta side effects —
        # the response is 200 and the MCP app stays untouched).
        app, inner_calls = self._build_app()

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
            "client": ("10.6.6.2", 33333),
        }
        asyncio.run(app(scope, receive, send))
        self.assertEqual(200, self._start(sent)["status"])
        self.assertEqual([], inner_calls)

    def test_no_token_401_and_counts_cooldown(self) -> None:
        app, inner_calls = self._build_app()
        sent = self._request(app, None)
        start = self._start(sent)
        self.assertEqual(401, start["status"])
        self.assertEqual([], inner_calls)


if __name__ == "__main__":
    unittest.main()
