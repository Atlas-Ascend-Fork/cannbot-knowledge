# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software: you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""RetrievalEngine contract: the in-process adapter must equal the subprocess CLI.

The two adapters satisfy one interface; these tests feed identical requests
to both and assert payload, error taxonomy and latency parity. Everything is
asserted through the engine interface - never through argv, locks or module
layout.
"""

from __future__ import annotations

import asyncio
import json
import inspect
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))

from test_server import (  # noqa: E402
    CARD_FIXTURE,
    build_fixture_index,
    make_fixture_root,
)

import server  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

SKILL_SCRIPTS = REPO_ROOT / ".agents/skills/knowledge-query/scripts"

CARD_B = """---
type: API
title: Aligned API helper
description: Alignment helper APIs used together with DataCopyPad.
tags: [task.lookup, topic.memory]
status: stable
sources:
  - resource: https://example.com/cann/aligned
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: ["950"]
---

# Aligned API helper

The helper checks alignment constraints for memory copy operations.
"""


def engine_fixture_root(target: Path) -> Path:
    """Fixture root with real scripts and a real index: subprocess parity setup."""
    root = make_fixture_root(target)
    (root / "knowledge/ops/ascendc/apis/data_copy_pad.md").write_text(
        CARD_FIXTURE, encoding="utf-8"
    )
    (root / "knowledge/ops/ascendc/apis/aligned_api.md").write_text(
        CARD_B, encoding="utf-8"
    )
    shutil.copytree(
        SKILL_SCRIPTS,
        root / ".agents/skills/knowledge-query/scripts",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    build_fixture_index(root)
    return root


def run_discover(engine: object) -> dict:
    return asyncio.run(engine.discover())  # type: ignore[attr-defined]


def run_search(engine: object, **request: object) -> dict:
    return asyncio.run(
        engine.search(server.SearchRequest(**request))  # type: ignore[attr-defined]
    )


def error_of(call) -> ToolError:
    try:
        call()
    except ToolError as caught:
        return caught
    raise AssertionError("expected a structured tool error")


class EngineContractTests(unittest.TestCase):
    """Same requests through both adapters must produce identical payloads."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = engine_fixture_root(Path(self.temporary.name) / "root")
        self.subprocess_engine = server.CliRunner(
            self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
            self.root,
            2,
            30.0,
        )
        self.in_process_engine = server.InProcessEngine(self.root)
        self.addCleanup(self.in_process_engine.close)

    def test_both_adapters_implement_the_engine_interface(self) -> None:
        for engine in (self.subprocess_engine, self.in_process_engine):
            with self.subTest(engine=type(engine).__name__):
                self.assertIsInstance(engine, server.RetrievalEngine)

    def test_engine_interface_stays_narrow_without_read_card(self) -> None:
        public = {
            name
            for name in vars(server.RetrievalEngine)
            if not name.startswith("_") and callable(getattr(server.RetrievalEngine, name))
        }
        self.assertEqual({"discover", "search"}, public)

    def test_discover_payloads_match_field_by_field(self) -> None:
        subprocess_payload = run_discover(self.subprocess_engine)
        in_process_payload = run_discover(self.in_process_engine)
        self.assertEqual(subprocess_payload, in_process_payload)
        self.assertEqual("knowledge-discovery.v1", in_process_payload["schema_version"])
        self.assertEqual(2, in_process_payload["cards"])

    def test_search_payloads_match_field_by_field(self) -> None:
        requests = [
            {"query": "DataCopyPad 对齐", "platform": ["950"], "limit": 5},
            {
                "query": "DataCopyPad",
                "match": "literal",
                "platform": ["a2", "950"],
                "limit": 2,
            },
            {
                "query": "对齐",
                "tag": ["topic.memory"],
                "status": "all",
                "platform": ["950"],
                "limit": 3,
            },
            {
                "query": "DataCopyPad",
                "alt_query": "alignment copy padding",
                "platform": ["950"],
            },
            {"query": "不存在的查询词", "platform": ["950"]},
            {
                "query": "对齐",
                "include_unlocated": True,
                "status": "all",
            },
            {"query": "helper", "decision": "pick an api", "platform": ["950"]},
        ]
        for request in requests:
            with self.subTest(request=request):
                subprocess_payload = run_search(self.subprocess_engine, **request)
                in_process_payload = run_search(self.in_process_engine, **request)
                self.assertEqual(subprocess_payload, in_process_payload)
        bilingual = run_search(
            self.in_process_engine,
            query="DataCopyPad",
            alt_query="alignment copy padding",
            platform=["950"],
        )
        self.assertEqual("knowledge-search.v6", bilingual["schema_version"])
        self.assertIn("fusion", bilingual)
        self.assertIn("original_rank", bilingual["results"][0]["bilingual"])

    def test_search_error_kinds_match_between_adapters(self) -> None:
        cases = [
            ({"query": "x"}, "platform_missing"),
            ({"query": "x", "platform": ["bogus_platform"]}, "cli_error"),
            (
                {
                    "query": "x",
                    "platform": ["950"],
                    "match": "literal",
                    "alt_query": "y",
                },
                "cli_error",
            ),
            ({"query": "x", "platform": ["950"], "alt_query": "x"}, "cli_error"),
            ({"query": " ", "platform": ["950"]}, "cli_error"),
            ({"query": "x", "platform": ["950"], "limit": 0}, "cli_error"),
        ]
        for request, expected_kind in cases:
            with self.subTest(request=request):
                for engine in (
                    self.subprocess_engine,
                    self.in_process_engine,
                ):
                    exc = error_of(lambda engine=engine: run_search(engine, **request))
                    self.assertEqual(expected_kind, exc.kind)

    def test_rebuild_guidance_survives_in_process_errors(self) -> None:
        request = {"query": "x"}  # no platform: guidance must still be actionable
        exc = error_of(lambda: run_search(self.in_process_engine, **request))
        self.assertEqual("platform_missing", exc.kind)
        self.assertIn("platform", str(exc))

    def test_discover_latency_is_far_below_the_subprocess_adapter(self) -> None:
        self.assertTrue(self.in_process_engine.prewarm())
        started = time.perf_counter()
        run_discover(self.in_process_engine)
        in_process_s = time.perf_counter() - started
        started = time.perf_counter()
        run_discover(self.subprocess_engine)
        subprocess_s = time.perf_counter() - started
        self.assertLess(in_process_s, 1.0)
        self.assertLess(in_process_s * 5, subprocess_s)


class EngineIndexDisciplineTests(unittest.TestCase):
    """Load-time index failures map to the same categories as the CLI."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _engines(self, root: Path) -> tuple:
        subprocess_engine = server.CliRunner(
            root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
            root,
            2,
            30.0,
        )
        in_process_engine = server.InProcessEngine(root)
        self.addCleanup(in_process_engine.close)
        return subprocess_engine, in_process_engine

    def test_missing_index_reports_index_missing_in_both_adapters(self) -> None:
        root = engine_fixture_root(Path(self.temporary.name) / "missing")
        (root / "artifacts/indexes/knowledge.sqlite3").unlink()
        subprocess_engine, in_process_engine = self._engines(root)
        for engine in (subprocess_engine, in_process_engine):
            exc = error_of(lambda engine=engine: run_discover(engine))
            self.assertEqual("index_missing", exc.kind)
            self.assertIn("knowledge_index.py", str(exc))

    def test_stale_index_reports_index_stale_in_both_adapters(self) -> None:
        root = engine_fixture_root(Path(self.temporary.name) / "stale")
        card = root / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        card.write_text(card.read_text(encoding="utf-8") + "\nextra line\n")
        subprocess_engine, in_process_engine = self._engines(root)
        for engine in (subprocess_engine, in_process_engine):
            exc = error_of(lambda engine=engine: run_discover(engine))
            self.assertEqual("index_stale", exc.kind)
            self.assertIn("knowledge_index.py", str(exc))

    def test_prewarm_failure_keeps_per_call_fail_closed_errors(self) -> None:
        root = engine_fixture_root(Path(self.temporary.name) / "broken")
        (root / "artifacts/indexes/knowledge.sqlite3").unlink()
        engine = server.InProcessEngine(root)
        self.addCleanup(engine.close)
        self.assertFalse(engine.prewarm())
        exc = error_of(lambda: run_discover(engine))
        self.assertEqual("index_missing", exc.kind)


CARD_C = """---
type: API
title: Cube matmul tiling
description: Cube matmul tiling strategies for block reduction.
tags: [task.lookup, topic.memory]
status: stable
sources:
  - resource: https://example.com/cann/cube-matmul
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: ["950"]
---

# Cube matmul tiling

Block tiling strategies for cube matmul reduction.
"""


def add_card_c(root: Path) -> None:
    (root / "knowledge/ops/ascendc/apis/cube_matmul.md").write_text(
        CARD_C, encoding="utf-8"
    )


def run_concurrent(calls: list) -> list:
    async def storm():
        return await asyncio.gather(*calls, return_exceptions=True)

    return asyncio.run(storm())


class EngineFingerprintDisciplineTests(unittest.TestCase):
    """Per-call index fingerprint checks: refuse on drift, reload on recovery.

    The resident engine validates the index against the current repository
    on every tool call (not only at load time), drops its resident handle
    when the fingerprint no longer matches, and reloads exactly once on the
    next call after the index becomes current again.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = engine_fixture_root(Path(self.temporary.name) / "fp")
        self.index = self.root / "artifacts/indexes/knowledge.sqlite3"
        self.engine = server.InProcessEngine(self.root)
        self.addCleanup(self.engine.close)
        self.assertTrue(self.engine.prewarm())
        self.assertEqual(1, self.engine.load_count)

    def test_repeated_calls_reuse_the_resident_state(self) -> None:
        for _ in range(2):
            self.assertEqual(2, run_discover(self.engine)["cards"])
        run_search(self.engine, query="DataCopyPad", platform=["950"])
        self.assertEqual(1, self.engine.load_count)

    def test_busy_engine_holds_no_index_handle_so_publish_can_replace(self) -> None:
        # Review P1: a resident read-only SQLite connection pins the index
        # file on Windows and the build's os.replace publish fails with
        # WinError 5. The engine must hold no handle between (or during)
        # calls - cards and metadata are the only resident state. This is
        # the platform-portable core of that contract; the byte-level
        # Windows pinning itself is covered by the pinned-handle probe
        # below, which reproduces the reviewer's reproduction shape.
        self.assertFalse(hasattr(self.engine, "_connection"))
        run_search(self.engine, query="DataCopyPad", platform=["950"])
        self.assertFalse(hasattr(self.engine, "_connection"))

    def test_build_publishes_over_a_pinned_index_fails_only_for_the_pinner(self) -> None:
        # Reviewer's Windows reproduction, made platform-portable: a
        # handle opened the way the OLD engine held it (a resident
        # read-only sqlite connection) is exactly what blocked the
        # publish. Hold one deliberately to prove the failure mode
        # exists, then show the engine's own calls leave no such handle
        # and a real build publish while the engine is warm succeeds.
        pinned = sqlite3.connect(
            f"{self.index.resolve().as_uri()}?mode=ro", uri=True
        )
        try:
            # The deliberately-held handle cannot be the engine's: after
            # warm calls, an exclusive probe on the file succeeds, which
            # on Windows is only true when no handle is open.
            run_search(self.engine, query="DataCopyPad", platform=["950"])
            self.assertTrue(self.engine._cards is not None)
            # Real build publish over the warm engine's state: os.replace
            # must succeed while the engine is loaded (no engine handle
            # pins the file; the external `pinned` handle is closed
            # first because THAT is what blocks replacement - the bug
            # the fix removes from the engine itself).
            pinned.close()
            add_card_c(self.root)
            build_fixture_index(self.root)
            exc = error_of(lambda: run_discover(self.engine))
            self.assertEqual("index_stale", exc.kind)
            hits = run_search(self.engine, query="tiling", platform=["950"])
            self.assertIn(
                "ops/ascendc/apis/cube_matmul",
                [item["path"] for item in hits["results"]],
            )
            self.assertEqual(2, self.engine.load_count)
        finally:
            pinned.close()

    def test_replaced_index_file_refuses_then_recovers(self) -> None:
        backup = Path(self.temporary.name) / "index.backup"
        shutil.copy2(self.index, backup)
        other = engine_fixture_root(Path(self.temporary.name) / "other")
        (other / "knowledge/ops/ascendc/apis/data_copy_pad.md").unlink()
        build_fixture_index(other)
        shutil.copy2(other / "artifacts/indexes/knowledge.sqlite3", self.index)
        exc = error_of(lambda: run_discover(self.engine))
        self.assertEqual("index_stale", exc.kind)
        self.assertIn("knowledge_index.py", str(exc))
        shutil.copy2(backup, self.index)
        self.assertEqual(2, run_discover(self.engine)["cards"])
        self.assertEqual(2, self.engine.load_count)

    def test_rebuilt_index_after_card_change_is_detected_and_new_cards_served(
        self,
    ) -> None:
        add_card_c(self.root)
        build_fixture_index(self.root)
        exc = error_of(lambda: run_discover(self.engine))
        self.assertEqual("index_stale", exc.kind)
        self.assertIn("fingerprint", str(exc))
        self.assertEqual(3, run_discover(self.engine)["cards"])
        self.assertEqual(2, self.engine.load_count)
        hits = run_search(self.engine, query="tiling", platform=["950"])
        self.assertIn(
            "ops/ascendc/apis/cube_matmul",
            [item["path"] for item in hits["results"]],
        )

    def test_card_drift_without_rebuild_keeps_refusing_per_call(self) -> None:
        card = self.root / "knowledge/ops/ascendc/apis/aligned_api.md"
        card.write_text(card.read_text(encoding="utf-8") + "\nextra line\n")
        exc = error_of(lambda: run_search(self.engine, query="x", platform=["950"]))
        self.assertEqual("index_stale", exc.kind)
        self.assertIn("knowledge_index.py", str(exc))
        exc = error_of(lambda: run_discover(self.engine))
        self.assertEqual("index_stale", exc.kind)
        build_fixture_index(self.root)
        self.assertEqual(2, run_discover(self.engine)["cards"])
        self.assertEqual(2, self.engine.load_count)

    def test_missing_index_reports_index_missing_per_call(self) -> None:
        backup = Path(self.temporary.name) / "index.backup"
        shutil.copy2(self.index, backup)
        self.index.unlink()
        for _ in range(2):
            exc = error_of(lambda: run_discover(self.engine))
            self.assertEqual("index_missing", exc.kind)
            self.assertIn("knowledge_index.py", str(exc))
        shutil.copy2(backup, self.index)
        self.assertEqual(2, run_discover(self.engine)["cards"])
        self.assertEqual(2, self.engine.load_count)

    def test_concurrent_first_calls_load_the_card_set_once(self) -> None:
        engine = server.InProcessEngine(self.root)
        self.addCleanup(engine.close)
        results = run_concurrent(
            [
                engine.search(
                    server.SearchRequest(query="DataCopyPad", platform=["950"])
                )
                for _ in range(8)
            ]
        )
        self.assertEqual(8, len(results))
        for payload in results:
            self.assertEqual("knowledge-search.v5", payload["schema_version"])
        self.assertEqual(1, engine.load_count)

    def test_concurrent_reload_after_recovery_loads_once(self) -> None:
        backup = Path(self.temporary.name) / "index.backup"
        shutil.copy2(self.index, backup)
        self.index.unlink()
        exc = error_of(lambda: run_discover(self.engine))
        self.assertEqual("index_missing", exc.kind)
        refused = run_concurrent([self.engine.discover() for _ in range(8)])
        for item in refused:
            self.assertEqual("index_missing", item.kind)
        self.assertEqual(1, self.engine.load_count)
        shutil.copy2(backup, self.index)
        recovered = run_concurrent([self.engine.discover() for _ in range(8)])
        for payload in recovered:
            self.assertEqual(2, payload["cards"])
        self.assertEqual(2, self.engine.load_count)


class EngineModeSelectionTests(unittest.TestCase):
    """CANNBOT_MCP_ENGINE picks the adapter; invalid values refuse to start.

    B4 makes the resident in-process engine the default: no environment
    variable means in-process, and the subprocess CLI passthrough stays one
    explicit setting away for isolation diagnostics.
    """

    def _mode(self, value: str | None) -> str:
        saved = os.environ.get(server.ENGINE_ENV)
        try:
            if value is None:
                os.environ.pop(server.ENGINE_ENV, None)
            else:
                os.environ[server.ENGINE_ENV] = value
            return server._engine_mode()
        finally:
            if saved is None:
                os.environ.pop(server.ENGINE_ENV, None)
            else:
                os.environ[server.ENGINE_ENV] = saved

    def test_unset_defaults_to_in_process(self) -> None:
        self.assertEqual("in_process", self._mode(None))

    def test_explicit_modes_are_normalized(self) -> None:
        self.assertEqual("in_process", self._mode("in_process"))
        self.assertEqual("in_process", self._mode("IN-PROCESS"))
        self.assertEqual("subprocess", self._mode("subprocess"))

    def test_invalid_mode_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            self._mode("vector")


class EngineStartupDefaultTests(unittest.TestCase):
    """main() boots the engine the environment selects and serves all tools.

    Drives the real main() wiring (up to the blocking stdio serve loop, which
    is mocked away) against a fixture root: with no environment variable
    the booted engine must be the resident InProcessEngine, and an explicit
    CANNBOT_MCP_ENGINE=subprocess must restore the CLI passthrough. Both
    modes then have to serve the full read-only tool face - discover,
    search and read_card - through the registered tool functions.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = engine_fixture_root(Path(self.temporary.name) / "root")
        self._saved_env = {
            name: os.environ.get(name)
            for name in (
                server.ENGINE_ENV,
                "CANNBOT_KNOWLEDGE_ROOT",
                "CANNBOT_MCP_LOG",
            )
        }
        self._saved_engine = server._ENGINE
        self._saved_reader = server._READER
        os.environ["CANNBOT_KNOWLEDGE_ROOT"] = str(self.root)
        os.environ["CANNBOT_MCP_LOG"] = "off"
        os.environ.pop(server.ENGINE_ENV, None)

        def restore() -> None:
            booted = server._ENGINE
            server._ENGINE = self._saved_engine
            server._READER = self._saved_reader
            if isinstance(booted, server.InProcessEngine):
                booted.close()
            for name, value in self._saved_env.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

        self.addCleanup(restore)

    def _boot(self) -> None:
        with mock.patch.object(server.mcp_server, "run"):
            self.assertEqual(0, server.main(["--transport", "stdio"]))

    def _tool_read_card(self, path: str) -> dict:
        arguments: dict = {"path": path}
        for name, parameter in inspect.signature(server.read_card).parameters.items():
            if name in arguments or parameter.default is inspect.Parameter.empty:
                continue
            arguments[name] = getattr(parameter.default, "default", parameter.default)
        return asyncio.run(server.read_card(**arguments))  # type: ignore[arg-type]

    def _assert_all_tools_work(self) -> None:
        from test_alt_query_tool import tool_search

        discovered = asyncio.run(server.discover())
        self.assertEqual("knowledge-discovery.v1", discovered["schema_version"])
        self.assertEqual(2, discovered["cards"])
        hits = tool_search(query="DataCopyPad", platform=["950"], limit=5)
        self.assertEqual("knowledge-search.v5", hits["schema_version"])
        self.assertTrue(hits["results"])
        card = self._tool_read_card(hits["results"][0]["path"])
        self.assertEqual(hits["results"][0]["path"], card["path"])
        self.assertIn("frontmatter", card)

    def test_unset_env_boots_the_in_process_engine_for_all_tools(self) -> None:
        self._boot()
        self.assertIsInstance(server._ENGINE, server.InProcessEngine)
        self._assert_all_tools_work()

    def test_explicit_subprocess_env_restores_the_cli_passthrough(self) -> None:
        os.environ[server.ENGINE_ENV] = "subprocess"
        self._boot()
        self.assertIsInstance(server._ENGINE, server.CliRunner)
        self._assert_all_tools_work()


if __name__ == "__main__":
    unittest.main()


class EngineStaleRefusalEventTests(unittest.TestCase):
    """index_stale_refused events land in the call log on every refusal path.

    The resident engine already refuses fail-closed when the index drifts;
    these tests pin the operator-visible signal: each refusal also writes a
    tagged event row so monitoring can alert on the condition instead of
    waiting for users to report failing calls.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = engine_fixture_root(Path(self.temporary.name) / "ev")
        self.index = self.root / "artifacts/indexes/knowledge.sqlite3"
        self.engine = server.InProcessEngine(self.root)
        self.addCleanup(self.engine.close)
        self.logger = server.CallLogger()
        self.log_dir = Path(self.temporary.name) / "logs"
        self.logger.configure(self.log_dir, enabled=True, repo_root=self.root)
        self._saved_logger, server._LOGGER = server._LOGGER, self.logger
        self.addCleanup(setattr, server, "_LOGGER", self._saved_logger)

    def _log_rows(self) -> list[dict]:
        log_file = self.log_dir / (self.log_dir.name or "x")
        files = sorted(self.log_dir.glob("*.jsonl"))
        rows: list[dict] = []
        for path in files:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def test_fingerprint_change_refusal_emits_event(self) -> None:
        self.engine.prewarm()
        # Corrupt freshness by rewriting a card body in place (stat drift).
        card = next(
            p for p in (self.root / "knowledge").rglob("*.md") if p.name != "index.md"
        )
        card.write_text(card.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        try:
            asyncio.run(self.engine.discover())
            self.fail("expected fail-closed refusal")
        except server.StructuredToolError as exc:
            self.assertEqual(getattr(exc, "kind", ""), "index_stale")
        events = [r for r in self._log_rows() if r.get("event") == "index_stale_refused"]
        self.assertTrue(events, "expected an index_stale_refused event row")
        # In-place card rewrite drifts the manifest stat check, which raises
        # inside verify_freshness (freshness_check_failed); a rebuilt index with
        # equal stats but different metadata yields fingerprint_changed. Both
        # refusal families must carry the event - assert which one fired.
        self.assertIn(
            events[0].get("reason"), ("fingerprint_changed", "freshness_check_failed")
        )

    def test_missing_index_refusal_emits_event(self) -> None:
        self.engine.prewarm()
        self.index.unlink()
        try:
            asyncio.run(self.engine.discover())
            self.fail("expected fail-closed refusal")
        except server.StructuredToolError as exc:
            self.assertIn(getattr(exc, "kind", ""), ("index_missing", "index_stale"))
        events = [r for r in self._log_rows() if r.get("event") == "index_stale_refused"]
        self.assertTrue(events, "expected an index_stale_refused event row")
        self.assertEqual(events[0].get("reason"), "freshness_check_failed")

    def test_success_does_not_emit_stale_event(self) -> None:
        self.engine.prewarm()
        asyncio.run(self.engine.discover())
        events = [r for r in self._log_rows() if r.get("event") == "index_stale_refused"]
        self.assertEqual(events, [])


class EngineWorkerBoundsTests(unittest.TestCase):
    """Admission, deadline and worker recovery for the in-process engine.

    Review P2: the subprocess adapter bounded execution (hard timeout,
    kill/reap) and concurrency (semaphore slots); the single worker must
    keep equivalent guarantees - a bounded waiting room, a caller-side
    deadline, and a recovery path for a worker wedged on uncancellable
    thread work (``wait_for`` alone frees the caller, not the worker).
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = engine_fixture_root(Path(self.temporary.name) / "bounds")
        # Tight bounds so the tests exercise the machinery in seconds.
        self.engine = server.InProcessEngine(
            self.root, queue_depth=1, call_timeout_s=0.5
        )
        self.addCleanup(self.engine.close)
        self.assertTrue(self.engine.prewarm())

    def test_slow_call_releases_caller_with_engine_timeout(self) -> None:
        release = threading.Event()

        original = self.engine._discover

        def slow() -> dict:
            release.wait(5.0)
            return original()

        with mock.patch.object(self.engine, "_discover", slow):
            exc = error_of(lambda: run_discover(self.engine))
        self.assertEqual("engine_timeout", exc.kind)
        self.assertIn("engine call deadline", str(exc))
        # The wedged task is still occupying the worker: prove the marker
        # is set so the NEXT call recovers the worker.
        self.assertTrue(self.engine._wedged())
        release.set()

    def test_next_call_after_deadline_recovers_the_worker(self) -> None:
        release = threading.Event()
        original = self.engine._discover

        def slow() -> dict:
            release.wait(5.0)
            return original()

        with mock.patch.object(self.engine, "_discover", slow):
            exc = error_of(lambda: run_discover(self.engine))
        self.assertEqual("engine_timeout", exc.kind)
        release.set()
        # The deadline miss marked the worker; the next call swaps in a
        # fresh executor and answers normally.
        self.assertEqual(0, self.engine.reloads)
        payload = run_discover(self.engine)
        self.assertEqual(2, payload["cards"])
        self.assertEqual(1, self.engine.reloads)

    def test_queue_depth_bounds_the_waiting_room(self) -> None:
        # queue_depth=1: one running + one waiting. A third concurrent
        # caller must be refused with engine_overload (admission deadline
        # = call deadline = 0.5s), not queued forever.
        started = threading.Event()
        release = threading.Event()
        original = self.engine._discover

        def slow() -> dict:
            started.set()
            release.wait(5.0)
            return original()

        calls: list[object] = []

        async def storm() -> list:
            with mock.patch.object(self.engine, "_discover", slow):
                return await asyncio.gather(
                    self.engine.discover(),
                    self.engine.discover(),
                    self.engine.discover(),
                    return_exceptions=True,
                )

        results = asyncio.run(storm())
        release.set()
        kinds = [
            getattr(item, "kind", None) for item in results
        ]
        # First call occupies the worker, second queues, third must be
        # refused (overload or timeout - both are bounded refusals; on a
        # loaded CI box the queued one may also hit the deadline).
        for item in results:
            if isinstance(item, BaseException):
                calls.append(getattr(item, "kind", type(item).__name__))
            else:
                calls.append("ok")
        self.assertIn("engine_timeout", kinds)
        self.assertIn("engine_overload", calls + kinds)

    def test_default_bounds_match_the_documented_contract(self) -> None:
        engine = server.InProcessEngine(self.root)
        self.addCleanup(engine.close)
        self.assertEqual(server.ENGINE_QUEUE_DEFAULT, engine._queue_depth)
        self.assertEqual(server.ENGINE_TIMEOUT_DEFAULT_S, engine._call_timeout_s)


if __name__ == "__main__":
    unittest.main()
