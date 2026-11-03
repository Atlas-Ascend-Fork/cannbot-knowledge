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
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "mcp-server/analyze_logs.py"

sys.path.insert(0, str(ANALYZER.parent))
import analyze_logs  # noqa: E402


def call_row(
    ts: str,
    principal: str | None,
    tool: str,
    args: dict,
    *,
    ok: bool = True,
    count: int | None = None,
    sha: str | None = None,
    hits: list | None = None,
    total_lines: int | None = None,
    returned_lines: int | None = None,
    truncated: bool | None = None,
    response_sha256: str | None = None,
    boot_id: str | None = None,
    error_kind: str | None = None,
    call_id: str | None = None,
) -> dict:
    row = {
        "ts": ts,
        "transport": "http",
        "boot_id": boot_id,
        "principal": principal,
        "tool": tool,
        "args": args,
        "ok": ok,
        "count": count,
        "latency_ms": 12.5,
        "request_sha256": sha,
        "index": None,
        "hits": hits,
        "total_lines": total_lines,
        "returned_lines": returned_lines,
        "truncated": truncated,
        "response_sha256": response_sha256,
        "error": None,
        "error_kind": error_kind,
    }
    if call_id is not None:
        row["call_id"] = call_id
    return row


def write_log(directory: Path, name: str, rows: list) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


class CallKeyTests(unittest.TestCase):
    """Dedup keys: call_id rows keyed by identity, legacy rows keep their key."""

    def test_call_key_uses_disjoint_sentinel_families(self) -> None:
        modern = call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                          {"query": "q", "platform": ["a2"]},
                          sha="s1", call_id="a1b2c3d4e5f60718")
        legacy_sha = call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                              {"query": "q", "platform": ["a2"]}, sha="s1")
        legacy_args = call_row("2026-10-10T08:00:00Z", None, "read_card",
                               {"path": "ops/x.md", "offset": 0, "limit": 200})
        self.assertEqual(
            ("call_id", "a1b2c3d4e5f60718"), analyze_logs.call_key(modern)
        )
        self.assertEqual(
            ("legacy", "2026-10-10T08:00:00Z", "search", "zhangsan", "s1"),
            analyze_logs.call_key(legacy_sha),
        )
        self.assertEqual(
            ("legacy", "2026-10-10T08:00:00Z", "read_card", None,
             json.dumps({"path": "ops/x.md", "offset": 0, "limit": 200},
                        ensure_ascii=False, sort_keys=True)),
            analyze_logs.call_key(legacy_args),
        )

    def test_same_instant_distinct_call_ids_are_distinct_events(self) -> None:
        # two instances answer the same query in the same millisecond for the
        # same principal: without call_id they collapse into one "duplicate"
        # and the divergence signal loses a group.
        first = call_row("2026-10-10T08:00:00.250Z", "zhangsan", "search",
                         {"query": "q", "platform": ["a2"]},
                         count=0, sha="shared", hits=[], call_id="a1b2c3d4e5f60718")
        second = call_row("2026-10-10T08:00:00.250Z", "zhangsan", "search",
                          {"query": "q", "platform": ["a2"]},
                          count=0, sha="shared", hits=[], call_id="1122334455667788")
        unique, duplicates = analyze_logs.deduplicate([first, second])
        self.assertEqual(2, len(unique))
        self.assertEqual(0, duplicates)

    def test_verbatim_union_copies_share_the_call_id_and_deduplicate(self) -> None:
        row = call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                       {"query": "q", "platform": ["a2"]},
                       count=0, sha="s1", hits=[], call_id="a1b2c3d4e5f60718")
        unique, duplicates = analyze_logs.deduplicate([dict(row), dict(row)])
        self.assertEqual(1, len(unique))
        self.assertEqual(1, duplicates)

    def test_legacy_and_modern_rows_never_share_keys(self) -> None:
        legacy = call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                          {"query": "q", "platform": ["a2"]},
                          count=0, sha="s1", hits=[])
        modern = call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                          {"query": "q", "platform": ["a2"]},
                          count=0, sha="s1", hits=[], call_id="a1b2c3d4e5f60718")
        unique, duplicates = analyze_logs.deduplicate([legacy, modern])
        self.assertEqual(2, len(unique))
        self.assertEqual(0, duplicates)
        # legacy rows still dedup among themselves on the legacy key
        unique, duplicates = analyze_logs.deduplicate([legacy, dict(legacy)])
        self.assertEqual(1, len(unique))
        self.assertEqual(1, duplicates)


class AnalyzerTests(unittest.TestCase):
    def run_analyzer(self, *arguments: str) -> tuple[int, str, str, dict | None]:
        completed = subprocess.run(
            [sys.executable, str(ANALYZER), *arguments],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        report = None
        if completed.returncode == 0 and "--output" in arguments:
            output = Path(arguments[arguments.index("--output") + 1])
            if output.is_file():
                report = json.loads(output.read_text(encoding="utf-8"))
        return completed.returncode, completed.stdout, completed.stderr, report

    def test_three_dimensions_with_multi_principal_zero_hit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls-2026-10-10.jsonl",
                [
                    call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                             {"query": "TileLang sink", "technology": "triton",
                              "platform": ["a2"], "match": "literal", "limit": 5},
                             count=0, sha="s1", hits=[]),
                    call_row("2026-10-10T08:05:00Z", "zhangsan", "search",
                             {"query": "TileLang sink", "technology": "triton",
                              "platform": ["a2"], "match": "literal", "limit": 5},
                             count=0, sha="s1", hits=[]),
                    call_row("2026-10-10T09:00:00Z", "lisi", "search",
                             {"query": "TileLang sink", "technology": "triton",
                              "platform": ["a2"], "match": "literal", "limit": 5},
                             count=0, sha="s1", hits=[]),
                    call_row("2026-10-10T09:30:00Z", "lisi", "search",
                             {"query": "DataCopyPad", "platform": ["a2"], "limit": 3},
                             count=2, sha="s2", hits=["ops/x.md", "ops/y.md"]),
                    call_row("2026-10-10T10:00:00Z", None, "search",
                             {"query": "broken", "platform": ["a2"]},
                             ok=False, count=None, sha=None, hits=None),
                    call_row("2026-10-10T11:00:00Z", "lisi", "read_card",
                             {"path": "ops/ascendc/apis/foo.md", "offset": 0, "limit": 200}),
                ],
            )
            output = Path(temporary) / "report.json"
            code, out, err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code, err)
            self.assertFalse(report["anonymous_mode"])
            zero = report["zero_hit"]
            self.assertEqual(1, len(zero))
            self.assertEqual("TileLang sink", zero[0]["query"])
            self.assertEqual(3, zero[0]["occurrences"])
            self.assertEqual(2, zero[0]["distinct_principals"])
            self.assertEqual(["lisi", "zhangsan"], zero[0]["principals"])
            self.assertIn("3 次，2 人独立尝试", zero[0]["issue_text"])
            self.assertIn("命中数：0", zero[0]["issue_text"])
            popularity = {
                item["query"]: item for item in report["query_popularity"]
            }
            self.assertEqual(3, popularity["TileLang sink"]["occurrences"])
            self.assertEqual(
                [{"path": "ops/x.md", "count": 1}, {"path": "ops/y.md", "count": 1}],
                popularity["DataCopyPad"]["top_hits"],
            )
            self.assertEqual(
                [
                    {
                        "path": "ops/ascendc/apis/foo.md",
                        "domain": "ops",
                        "technology": "ascendc",
                        "occurrences": 1,
                        "distinct_principals": 1,
                    }
                ],
                report["read_popularity"],
            )
            self.assertIn("匿名模式", out) if report["anonymous_mode"] else None

    def test_anonymous_mode_is_flagged_and_counts_repeats(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls-2026-10-10.jsonl",
                [
                    call_row("2026-10-10T08:00:00Z", None, "search",
                             {"query": "gap", "platform": ["a2"]},
                             count=0, sha="s1", hits=[]),
                    call_row("2026-10-10T08:01:00Z", None, "search",
                             {"query": "gap", "platform": ["a2"]},
                             count=0, sha="s1", hits=[]),
                ],
            )
            output = Path(temporary) / "report.json"
            code, out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertTrue(report["anonymous_mode"])
            self.assertEqual(2, report["zero_hit"][0]["occurrences"])
            self.assertIsNone(report["zero_hit"][0]["distinct_principals"])
            self.assertIn("人数未知（匿名模式）", report["zero_hit"][0]["issue_text"])
            self.assertIn("匿名模式：频次含重复", out)

    def test_multi_directory_merge_deduplicates_copies_not_distinct_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "a"
            second = Path(temporary) / "b"
            row_same = call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                                {"query": "q", "platform": ["a2"]},
                                count=0, sha="s1", hits=[])
            row_later = call_row("2026-10-10T08:30:00Z", "zhangsan", "search",
                                 {"query": "q", "platform": ["a2"]},
                                 count=0, sha="s1", hits=[])
            write_log(first, "calls-2026-10-10.jsonl", [row_same, row_later])
            write_log(second, "calls-2026-10-10.jsonl", [row_same])
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", f"{first},{second}", "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertEqual(1, report["stats"]["duplicates_dropped"])
            self.assertEqual(2, report["zero_hit"][0]["occurrences"])

    def test_multi_directory_merge_keeps_same_millisecond_distinct_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "a"
            second = Path(temporary) / "b"
            row_one = call_row(
                "2026-10-10T08:00:00.250Z", "zhangsan", "search",
                {"query": "q", "platform": ["a2"]},
                count=0, sha="shared", hits=[], call_id="a1b2c3d4e5f60718",
                response_sha256="resp-a",
            )
            row_two = call_row(
                "2026-10-10T08:00:00.250Z", "zhangsan", "search",
                {"query": "q", "platform": ["a2"]},
                count=0, sha="shared", hits=[], call_id="1122334455667788",
                response_sha256="resp-b",
            )
            write_log(first, "calls-2026-10-10.jsonl", [row_one, row_two])
            write_log(second, "calls-2026-10-10.jsonl", [row_one])
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", f"{first},{second}", "--output", str(output)
            )
            self.assertEqual(0, code)
            # only the verbatim union copy is dropped; the same-millisecond
            # sibling call survives as its own event
            self.assertEqual(1, report["stats"]["duplicates_dropped"])
            self.assertEqual(2, report["zero_hit"][0]["occurrences"])
            # the drift signal survives: two instances answered the same
            # request differently in the same millisecond
            self.assertEqual(1, report["stats"]["request_response_divergence"])

    def test_days_window_filters_old_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            recent = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            old = (
                datetime.now(timezone.utc) - timedelta(days=10)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row(old, "zhangsan", "search",
                             {"query": "old", "platform": ["a2"]},
                             count=0, sha="old", hits=[]),
                    call_row(recent, "zhangsan", "search",
                             {"query": "new", "platform": ["a2"]},
                             count=0, sha="new", hits=[]),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--days", "5", "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertEqual(["new"], [item["query"] for item in report["zero_hit"]])
            self.assertEqual(1, report["stats"]["lines_read"])

    def test_malformed_lines_are_counted_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            logs.mkdir()
            (logs / "calls.jsonl").write_text(
                "not json\n"
                + json.dumps(call_row("2026-10-10T08:00:00Z", "a", "search",
                                       {"query": "ok", "platform": ["a2"]},
                                       count=0, sha="s", hits=[]))
                + "\n"
                + json.dumps({"tool": "search", "no_ts": True})
                + "\n",
                encoding="utf-8",
            )
            output = Path(temporary) / "report.json"
            code, out, err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code, err)
            self.assertEqual(2, report["stats"]["skipped_malformed"])
            self.assertEqual(1, report["stats"]["lines_read"])
            self.assertEqual(1, len(report["zero_hit"]))

    def test_default_report_path_stays_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [call_row("2026-10-10T08:00:00Z", "a", "search",
                          {"query": "q", "platform": ["a2"]}, count=0, sha="s", hits=[])],
            )
            environment = dict(os.environ)
            environment["HOME"] = str(home)
            completed = subprocess.run(
                [sys.executable, str(ANALYZER), "--log-dir", str(logs)],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                env=environment,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            expected_root = home / ".local/state/cannbot-knowledge/mcp/reports"
            reports = list(expected_root.glob("*.json"))
            self.assertEqual(1, len(reports))
            self.assertFalse(
                str(reports[0]).startswith(str(ROOT)),
                "default report path must stay outside the repository",
            )

    def test_missing_directory_fails_closed(self) -> None:
        code, _out, err, _report = self.run_analyzer(
            "--log-dir", "/nonexistent-cannbot-dir"
        )
        self.assertEqual(2, code)
        self.assertIn("does not exist", err)

    def test_platform_demand_aggregates_array_groups_and_unset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "a", "platform": ["a2", "910"]},
                             count=1, sha="p1", hits=["ops/x.md"],
                             response_sha256="same-resp"),
                    call_row("2026-10-12T08:05:00Z", "lisi", "search",
                             {"query": "b", "platform": ["910", "a2"]},
                             count=1, sha="p2", hits=["ops/x.md"],
                             response_sha256="same-resp"),
                    call_row("2026-10-12T08:10:00Z", "wangwu", "search",
                             {"query": "c", "platform": ["a2"]},
                             count=0, sha="p3", hits=[]),
                    call_row("2026-10-12T08:15:00Z", "zhangsan", "search",
                             {"query": "d", "platform": None},
                             count=1, sha="p4", hits=["ops/x.md"]),
                    call_row("2026-10-12T08:20:00Z", "lisi", "search",
                             {"query": "e"},
                             count=1, sha="p5", hits=["ops/x.md"]),
                    call_row("2026-10-12T08:25:00Z", "lisi", "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200}),
                    call_row("2026-10-12T08:30:00Z", "zhangsan", "search",
                             {"query": "f", "platform": ["a2"]},
                             ok=False, count=None, sha=None, hits=None),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            demand = report["platform_demand"]
            self.assertEqual(
                [
                    {
                        "platform": "(unset)",
                        "occurrences": 2,
                        "distinct_principals": 2,
                    },
                    {
                        "platform": "910+a2",
                        "occurrences": 2,
                        "distinct_principals": 2,
                    },
                    {
                        "platform": "a2",
                        "occurrences": 1,
                        "distinct_principals": 1,
                    },
                ],
                demand,
            )

    def test_read_depth_uses_session_coverage_union(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    # paginated full read within one session: 0..200 + 200..400 of 400
                    # coverage union = 400/400 -> max_depth_read = 1.0
                    call_row("2026-10-12T08:00:00Z", "lisi", "read_card",
                             {"path": "ops/long.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b1"),
                    call_row("2026-10-12T08:01:00Z", "lisi", "read_card",
                             {"path": "ops/long.md", "offset": 200, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=False,
                             boot_id="b1"),
                    # same principal, >15 min later -> new session: first page
                    # only, never resumed -> single visit
                    call_row("2026-10-12T09:30:00Z", "lisi", "read_card",
                             {"path": "ops/long.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b1"),
                    # another card, first page only: single visit, no page turn
                    call_row("2026-10-12T08:15:00Z", "wangwu", "read_card",
                             {"path": "ops/short.md", "offset": 0, "limit": 200},
                             total_lines=1000, returned_lines=200, truncated=True,
                             boot_id="b2"),
                    # legacy row without pagination evidence - no coverage contribution
                    call_row("2026-10-12T08:20:00Z", "zhangsan", "read_card",
                             {"path": "ops/legacy.md", "offset": 0, "limit": 200},
                             boot_id="b3"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            depth = {item["path"]: item for item in report["read_depth"]}
            self.assertEqual(3, len(depth))
            long_card = depth["ops/long.md"]
            self.assertEqual(3, long_card["occurrences"])
            self.assertEqual(1, long_card["distinct_principals"])
            self.assertEqual(2, long_card["sessions"])
            # union of [0,200) + [200,400) = 400 of 400 lines, not the old
            # per-row average 0.5
            self.assertEqual(1.0, long_card["max_depth_read"])
            # session 1 turned the page, session 2 stopped after the truncated
            # first page
            self.assertEqual(0.5, long_card["single_visit_rate"])
            self.assertEqual(0.5, long_card["page_turn_rate"])
            short_card = depth["ops/short.md"]
            self.assertEqual(1, short_card["sessions"])
            self.assertEqual(0.2, short_card["max_depth_read"])
            self.assertEqual(1.0, short_card["single_visit_rate"])
            self.assertEqual(0.0, short_card["page_turn_rate"])
            legacy_card = depth["ops/legacy.md"]
            self.assertEqual(1, legacy_card["sessions"])
            self.assertIsNone(legacy_card["max_depth_read"])
            self.assertEqual(0.0, legacy_card["single_visit_rate"])
            self.assertEqual(0.0, legacy_card["page_turn_rate"])

    def test_max_depth_read_takes_the_deepest_session_not_the_union(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    # 400-line card, two readers: A saw 0..200, B saw 200..400.
                    # Unioning across sessions would fake a 100% read; each
                    # session is 50%, so the reported depth is 50%.
                    call_row("2026-10-12T08:00:00Z", "lisi", "read_card",
                             {"path": "ops/long.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b1"),
                    call_row("2026-10-12T08:01:00Z", "wangwu", "read_card",
                             {"path": "ops/long.md", "offset": 200, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=False,
                             boot_id="b2"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            long_card = report["read_depth"][0]
            self.assertEqual(2, long_card["sessions"])
            self.assertEqual(0.5, long_card["max_depth_read"])

    def test_read_depth_groups_by_principal_fallback_boot_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    # anonymous rows: same boot_id b1, <15 min apart -> one session
                    call_row("2026-10-12T08:00:00Z", None, "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b1"),
                    call_row("2026-10-12T08:10:00Z", None, "read_card",
                             {"path": "ops/x.md", "offset": 200, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=False,
                             boot_id="b1"),
                    # same boot_id but >15 min later -> separate session
                    call_row("2026-10-12T08:40:00Z", None, "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b1"),
                    # different boot_id inside the same 15-minute span -> separate
                    # session (another concurrent stdio client)
                    call_row("2026-10-12T08:45:00Z", None, "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b2"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            depth = report["read_depth"][0]
            self.assertEqual(3, depth["sessions"])
            self.assertEqual(1.0, depth["max_depth_read"])
            # two of the three sessions stopped after the first truncated page
            self.assertEqual(0.667, depth["single_visit_rate"])
            self.assertEqual(0.333, depth["page_turn_rate"])

    def test_weekly_trend_buckets_by_iso_week(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    # 2026-10-05~10-11 (2026-10-10): one zero-hit search by zhangsan, one read
                    call_row("2026-10-10T08:00:00Z", "zhangsan", "search",
                             {"query": "gap", "platform": ["a2"]},
                             count=0, sha="w1", hits=[]),
                    call_row("2026-10-10T09:00:00Z", "zhangsan", "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200}),
                    # 2026-10-12~10-18 (2026-10-13): zero-hit by lisi, hit by zhangsan, read by both
                    call_row("2026-10-13T08:00:00Z", "lisi", "search",
                             {"query": "gap", "platform": ["a2"]},
                             count=0, sha="w2", hits=[]),
                    call_row("2026-10-13T09:00:00Z", "zhangsan", "search",
                             {"query": "hit", "platform": ["a2"]},
                             count=1, sha="w3", hits=["ops/y.md"]),
                    call_row("2026-10-13T10:00:00Z", "zhangsan", "read_card",
                             {"path": "ops/y.md", "offset": 0, "limit": 200}),
                    call_row("2026-10-13T11:00:00Z", "lisi", "read_card",
                             {"path": "ops/y.md", "offset": 0, "limit": 200}),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            trend = report["weekly_trend"]
            self.assertEqual(
                [
                    {
                        "week": "2026-10-05~10-11",
                        "searches": 1,
                        "zero_hits": 1,
                        "zero_hit_rate": 1.0,
                        "reads": 1,
                        "distinct_principals": 1,
                    },
                    {
                        "week": "2026-10-12~10-18",
                        "searches": 2,
                        "zero_hits": 1,
                        "zero_hit_rate": 0.5,
                        "reads": 2,
                        "distinct_principals": 2,
                    },
                ],
                trend,
            )

    def test_request_response_divergence_counts_sha_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    # same request sha, two different responses -> divergent
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "q", "platform": ["a2"]},
                             count=1, sha="shared", hits=["ops/x.md"],
                             response_sha256="resp-a"),
                    call_row("2026-10-12T08:01:00Z", "lisi", "search",
                             {"query": "q", "platform": ["a2"]},
                             count=1, sha="shared", hits=["ops/x.md"],
                             response_sha256="resp-b"),
                    # same request sha, same response everywhere -> stable
                    call_row("2026-10-12T09:00:00Z", "zhangsan", "search",
                             {"query": "q", "platform": ["a2"]},
                             count=1, sha="stable", hits=["ops/x.md"],
                             response_sha256="resp-c"),
                    call_row("2026-10-12T09:05:00Z", "lisi", "search",
                             {"query": "q", "platform": ["a2"]},
                             count=1, sha="stable", hits=["ops/x.md"],
                             response_sha256="resp-c"),
                    # read_card has no request_sha256 and must not break grouping
                    call_row("2026-10-12T10:00:00Z", "lisi", "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200},
                             response_sha256="resp-d"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertEqual(1, report["stats"]["request_response_divergence"])
            self.assertIn("WARNING", out)

    def test_request_response_divergence_zero_without_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "q", "platform": ["a2"]},
                             count=1, sha="s", hits=["ops/x.md"],
                             response_sha256="resp-a"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertEqual(0, report["stats"]["request_response_divergence"])
            self.assertNotIn("WARNING", out)

    def test_render_markdown_covers_all_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "TileLang sink", "platform": ["a2", "910"]},
                             count=0, sha="s1", hits=[], response_sha256="r1"),
                    call_row("2026-10-12T09:00:00Z", "zhangsan", "search",
                             {"query": "DataCopyPad", "platform": ["a2"]},
                             count=1, sha="s2", hits=["ops/ascendc/apis/dcp.md"],
                             response_sha256="r2"),
                    call_row("2026-10-12T10:00:00Z", "lisi", "read_card",
                             {"path": "ops/ascendc/apis/dcp.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             response_sha256="r3"),
                    call_row("2026-10-12T11:00:00Z", "lisi", "read_card",
                             {"path": "ops/ascendc/apis/dcp.md", "offset": 200, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=False,
                             response_sha256="r4"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, _report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            markdown_path = output.with_suffix(".md")
            self.assertTrue(markdown_path.is_file())
            text = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# cannbot-knowledge MCP 调用分析 ", text)
            for section in (
                "## 漏斗总览",
                "## 零命中 TOP",
                "## 查询词热度 TOP",
                "## 平台需求分布",
                "## 卡片阅读热度与消费深度",
                "## 周趋势",
            ):
                self.assertIn(section, text)
            # zero-hit issue text is paste-ready inside a fenced code block
            self.assertIn("```\n- 查询词：`TileLang sink`", text)
            self.assertIn("命中数：0", text)
            # query popularity table carries the sample query
            self.assertIn("DataCopyPad", text)
            # platform demand table carries the array-group key
            self.assertIn("910+a2", text)
            # read board joins popularity with depth per path
            self.assertIn("ops/ascendc/apis/dcp.md", text)
            self.assertIn("2", text)
            # weekly trend table carries the ISO week bucket
            self.assertIn("2026-10-12~10-18", text)

    def test_funnel_totals_count_beyond_the_truncated_boards(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "alpha", "platform": ["a2"]},
                             count=0, sha="s1", hits=[]),
                    call_row("2026-10-12T08:01:00Z", "zhangsan", "search",
                             {"query": "alpha", "platform": ["a2"]},
                             count=0, sha="s1", hits=[]),
                    call_row("2026-10-12T08:02:00Z", "lisi", "search",
                             {"query": "beta", "platform": ["a2"]},
                             count=0, sha="s2", hits=[]),
                    call_row("2026-10-12T08:03:00Z", "lisi", "search",
                             {"query": "gamma", "platform": ["a2"]},
                             count=1, sha="s3", hits=["ops/x.md"]),
                    call_row("2026-10-12T08:04:00Z", "wangwu", "search",
                             {"query": "gamma", "platform": ["a2"]},
                             count=1, sha="s3", hits=["ops/x.md"]),
                    call_row("2026-10-12T08:05:00Z", "zhangsan", "search",
                             {"query": "gamma", "platform": ["a2"]},
                             count=1, sha="s3", hits=["ops/x.md"]),
                    call_row("2026-10-12T08:06:00Z", "lisi", "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200}),
                    call_row("2026-10-12T08:07:00Z", "zhangsan", "read_card",
                             {"path": "ops/x.md", "offset": 0, "limit": 200}),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--top", "2", "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertEqual(2, len(report["query_popularity"]))
            self.assertEqual(
                {"search": 6, "zero_hit": 3, "read_card": 2},
                report["funnel_totals"],
            )
            text = output.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn(
                "窗口内共 6 次 search（其中 3 次零命中，零命中率 50.0%）、2 次 read_card。",
                text,
            )

    def test_render_markdown_flags_anonymous_mode_and_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", None, "search",
                             {"query": "gap", "platform": ["a2"]},
                             count=0, sha="shared", hits=[], response_sha256="r1"),
                    call_row("2026-10-12T08:30:00Z", None, "search",
                             {"query": "gap", "platform": ["a2"]},
                             count=0, sha="shared", hits=[], response_sha256="r2"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, _report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            text = output.with_suffix(".md").read_text(encoding="utf-8")
            self.assertIn("匿名模式", text)
            self.assertIn("WARNING", text)

    def test_failure_kinds_aggregate_counts_and_top_queries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "a2 DataCopy", "platform": ["910"]},
                             ok=False, sha=None, hits=None, error_kind="platform_missing"),
                    call_row("2026-10-12T08:05:00Z", "lisi", "search",
                             {"query": "a2 DataCopy", "platform": ["910"]},
                             ok=False, sha=None, hits=None, error_kind="platform_missing"),
                    call_row("2026-10-12T08:10:00Z", "wangwu", "search",
                             {"query": "a2 DataCopy", "platform": ["310"]},
                             ok=False, sha=None, hits=None, error_kind="platform_missing"),
                    call_row("2026-10-12T08:15:00Z", "zhangsan", "search",
                             {"query": "tilelang 调优"},
                             ok=False, sha=None, hits=None, error_kind="subprocess_timeout"),
                    # read_card failure: path evidence instead of query words
                    call_row("2026-10-12T08:20:00Z", "lisi", "read_card",
                             {"path": "ops/ascendc/apis/gone.md", "offset": 0, "limit": 200},
                             ok=False, sha=None, hits=None, error_kind="path_not_indexed"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            kinds = {item["kind"]: item for item in report["failure_kinds"]}
            self.assertEqual(
                {"platform_missing", "subprocess_timeout", "path_not_indexed"},
                set(kinds),
            )
            self.assertEqual(3, kinds["platform_missing"]["count"])
            self.assertEqual(
                [{"query": "a2 DataCopy", "count": 3}],
                kinds["platform_missing"]["top_queries"],
            )
            self.assertEqual(1, kinds["subprocess_timeout"]["count"])
            self.assertEqual(
                [{"query": "tilelang 调优", "count": 1}],
                kinds["subprocess_timeout"]["top_queries"],
            )
            self.assertEqual(1, kinds["path_not_indexed"]["count"])
            self.assertEqual(
                [{"query": "ops/ascendc/apis/gone.md", "count": 1}],
                kinds["path_not_indexed"]["top_queries"],
            )

    def test_failure_kinds_empty_when_no_failed_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "zhangsan", "search",
                             {"query": "fine", "platform": ["a2"]},
                             count=1, sha="s1", hits=["ops/x.md"]),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            self.assertEqual([], report["failure_kinds"])

    def test_render_markdown_covers_read_depth_and_failure_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            logs = Path(temporary) / "logs"
            write_log(
                logs,
                "calls.jsonl",
                [
                    call_row("2026-10-12T08:00:00Z", "lisi", "read_card",
                             {"path": "ops/ascendc/apis/dcp.md", "offset": 0, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=True,
                             boot_id="b1"),
                    call_row("2026-10-12T08:01:00Z", "lisi", "read_card",
                             {"path": "ops/ascendc/apis/dcp.md", "offset": 200, "limit": 200},
                             total_lines=400, returned_lines=200, truncated=False,
                             boot_id="b1"),
                    call_row("2026-10-12T08:30:00Z", "zhangsan", "search",
                             {"query": "a2 DataCopy", "platform": ["910"]},
                             ok=False, sha=None, hits=None, error_kind="platform_missing"),
                ],
            )
            output = Path(temporary) / "report.json"
            code, _out, _err, _report = self.run_analyzer(
                "--log-dir", str(logs), "--output", str(output)
            )
            self.assertEqual(0, code)
            text = output.with_suffix(".md").read_text(encoding="utf-8")
            # Chinese read-depth column headers with the renamed metrics
            self.assertIn("阅读深度", text)
            self.assertIn("单次阅读占比", text)
            self.assertIn("翻页续读占比", text)
            # failure-kind board with the top query signal
            self.assertIn("错误类别", text)
            self.assertIn("platform_missing", text)
            self.assertIn("a2 DataCopy", text)


if __name__ == "__main__":
    unittest.main()
