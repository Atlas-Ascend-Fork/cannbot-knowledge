#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Offline aggregation of cannbot-knowledge MCP call logs into maintainer reports.

Maintainer tool, not an MCP tool: reads JSONL call/event logs written by
mcp-server/server.py, merges directories, deduplicates repeated lines and
produces the zero-hit / query popularity / read popularity boards plus
platform demand, read depth (session coverage union), failure kinds,
weekly trend and multi-instance drift checks. Each run writes a
machine-readable JSON report and a human-readable Markdown summary next
to it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

LOG_DIR_ENV = "CANNBOT_MCP_LOG_DIR"
DEFAULT_STATE_DIR = Path.home() / ".local/state/cannbot-knowledge/mcp"
REPORT_SCHEMA = "cannbot-mcp-report.v1"
SEARCH_FILTER_KEYS = (
    "domain",
    "technology",
    "type",
    "task",
    "tag",
    "platform",
    "include_unlocated",
    "include_shared",
    "source_technology",
    "target_technology",
    "status",
    "match",
)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def default_log_dirs() -> list[Path]:
    value = os.environ.get(LOG_DIR_ENV, "").strip()
    return [Path(value) if value else DEFAULT_STATE_DIR]


def read_lines(directories: list[Path]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    skipped = 0
    for directory in directories:
        for path in sorted(directory.glob("*.jsonl")):
            try:
                content = path.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
                continue
            for number, line in enumerate(content.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    print(
                        f"warning: skipping malformed line {path}:{number}",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(record, dict) or parse_timestamp(record.get("ts")) is None:
                    skipped += 1
                    print(
                        f"warning: skipping line without valid ts {path}:{number}",
                        file=sys.stderr,
                    )
                    continue
                records.append(record)
    return records, {"skipped_malformed": skipped}


def call_key(record: dict[str, Any]) -> tuple[Any, ...]:
    # Rows written since call_id exists carry a per-call unique id: the union
    # merge can only duplicate a line verbatim (same call_id), so that id is
    # the idempotency key. Legacy rows keep the historical tuple; the leading
    # sentinel keeps the two key families from ever colliding.
    call_id = record.get("call_id")
    if call_id:
        return ("call_id", call_id)
    principal = record.get("principal")
    sha = record.get("request_sha256")
    if sha:
        return ("legacy", record["ts"], record.get("tool"), principal, sha)
    args = record.get("args") if isinstance(record.get("args"), dict) else {}
    return (
        "legacy",
        record["ts"],
        record.get("tool"),
        principal,
        json.dumps(args, ensure_ascii=False, sort_keys=True),
    )


def deduplicate(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    ordered = sorted(records, key=lambda item: item["ts"])
    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []
    call_records = 0
    unique_calls = 0
    for record in ordered:
        if record.get("event"):
            unique.append(record)
            continue
        call_records += 1
        key = call_key(record)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
        unique_calls += 1
    return unique, call_records - unique_calls


def within_days(record: dict[str, Any], days: int | None) -> bool:
    if days is None:
        return True
    parsed = parse_timestamp(record.get("ts"))
    if parsed is None:
        return False
    return parsed >= datetime.now(timezone.utc) - timedelta(days=days)


def principals_of(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(row["principal"])
            for row in rows
            if row.get("principal") is not None
        }
    )


def search_filters(arguments: dict[str, Any]) -> dict[str, Any]:
    return {key: arguments[key] for key in SEARCH_FILTER_KEYS if key in arguments}


def format_filters(filters: dict[str, Any]) -> str:
    parts = []
    for key, value in filters.items():
        if isinstance(value, list):
            rendered = "/".join(str(item) for item in value)
        else:
            rendered = str(value)
        parts.append(f"{key}={rendered}")
    return ", ".join(parts) if parts else "无"


def zero_hit_issue_text(
    query: str, filters: dict[str, Any], occurrences: int, distinct: int | None,
    first_ts: str, last_ts: str,
) -> str:
    attempts = (
        f"{occurrences} 次，{distinct} 人独立尝试"
        if distinct is not None
        else f"{occurrences} 次，人数未知（匿名模式）"
    )
    return (
        f"- 查询词：`{query}`\n"
        f"  - 过滤条件：{format_filters(filters)}\n"
        f"  - 命中数：0\n"
        f"  - 尝试：{attempts}\n"
        f"  - 时间范围：{first_ts} ~ {last_ts}"
    )


def platform_key(arguments: dict[str, Any]) -> str:
    value = arguments.get("platform")
    if isinstance(value, list) and value:
        return "+".join(sorted(str(item) for item in value))
    if isinstance(value, str) and value:
        return value
    return "(unset)"


SESSION_GAP = timedelta(minutes=15)


def session_key(record: dict[str, Any]) -> str:
    """Group key: the principal if known, else the boot_id.

    Anonymous (principal-less) rows from concurrent stdio clients share no
    principal, so boot_id is the only separator that keeps their reads apart.
    """
    principal = record.get("principal")
    if principal is not None:
        return f"principal:{principal}"
    return f"boot:{record.get('boot_id')}"


def split_sessions(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Split one principal/boot group into visits: a gap over 15 minutes
    between consecutive calls starts a new session (standard log-analysis
    habit; the gap is fixed here and not part of the config surface)."""
    def sort_key(row: dict[str, Any]) -> datetime:
        return parse_timestamp(row.get("ts")) or datetime.min.replace(tzinfo=timezone.utc)

    sessions: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    previous: datetime | None = None
    for row in sorted(rows, key=sort_key):
        parsed = parse_timestamp(row.get("ts"))
        if (
            current
            and parsed is not None
            and previous is not None
            and parsed - previous > SESSION_GAP
        ):
            sessions.append(current)
            current = []
        current.append(row)
        if parsed is not None:
            previous = parsed
    if current:
        sessions.append(current)
    return sessions


def coverage_union_depth(rows: list[dict[str, Any]]) -> float | None:
    """Deepest-read fraction of a card over the analysis window: the union
    of the [offset, offset + returned_lines) windows the calls actually
    covered, divided by the card size, capped at 100%.

    A paginated read to the end (0..200 + 200..400 of 400) is a complete
    read here; the previous per-row average scored it 0.5. Rows without
    pagination evidence (missing total_lines or returned_lines, or legacy
    rows) contribute no coverage. When rows disagree on total_lines (the
    card changed during the window), the most recent observation wins.
    """

    def sort_key(row: dict[str, Any]) -> datetime:
        return parse_timestamp(row.get("ts")) or datetime.min.replace(tzinfo=timezone.utc)

    intervals: list[tuple[int, int]] = []
    total_lines: int | None = None
    for row in sorted(rows, key=sort_key):
        arguments = row.get("args") if isinstance(row.get("args"), dict) else {}
        offset = arguments.get("offset")
        returned = row.get("returned_lines")
        total = row.get("total_lines")
        if (
            isinstance(offset, int)
            and offset >= 0
            and isinstance(returned, int)
            and returned > 0
        ):
            intervals.append((offset, offset + returned))
        if isinstance(total, int) and total > 0:
            total_lines = total
    if not intervals or total_lines is None:
        return None
    intervals.sort()
    covered = 0
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start > end:
            covered += end - start
            start, end = next_start, next_end
        else:
            end = max(end, next_end)
    covered += end - start
    return round(min(covered / total_lines, 1.0), 3)


def read_session_metrics(rows: list[dict[str, Any]]) -> dict[str, bool]:
    """Per-visit read behaviour for one card inside one session.

    A visit "turned the page" when any of its reads continued past the
    first page (offset > 0); it "stopped after the truncated page" when it
    saw truncation and never turned. A visit that read the whole card in
    one non-truncated call is neither - pagination never applied to it.
    """
    offsets: list[int] = []
    truncated_seen = False
    for row in rows:
        arguments = row.get("args") if isinstance(row.get("args"), dict) else {}
        offset = arguments.get("offset")
        if isinstance(offset, int) and offset >= 0:
            offsets.append(offset)
        if row.get("truncated") is True:
            truncated_seen = True
    resumed = any(offset > 0 for offset in offsets)
    return {
        "single_visit": truncated_seen and not resumed,
        "page_turn": resumed,
    }


def iso_week(record: dict[str, Any]) -> str | None:
    """Bucket key: the Monday-Sunday span of the record's ISO week.

    "2026-10-19~10-25" reads without mental calendar math; a bare W43 does
    not.
    """
    parsed = parse_timestamp(record.get("ts"))
    if parsed is None:
        return None
    monday = parsed.date() - timedelta(days=parsed.date().weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday:%Y-%m-%d}~{sunday:%m-%d}"


def aggregate(records: list[dict[str, Any]], top: int) -> dict[str, Any]:
    calls = [record for record in records if not record.get("event")]
    search_ok = [
        record
        for record in calls
        if record.get("tool") == "search" and record.get("ok") is True
    ]
    search_zero = [record for record in search_ok if record.get("count") == 0]
    reads_ok = [
        record
        for record in calls
        if record.get("tool") == "read_card" and record.get("ok") is True
    ]
    anonymous = all(
        record.get("principal") is None for record in search_ok + reads_ok
    ) and (search_ok or reads_ok)

    zero_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in search_zero:
        arguments = record.get("args") if isinstance(record.get("args"), dict) else {}
        query = str(arguments.get("query", ""))
        key = (query, json.dumps(search_filters(arguments), ensure_ascii=False, sort_keys=True))
        zero_groups[key].append(record)

    zero_hit: list[dict[str, Any]] = []
    for (query, filters_json), rows in zero_groups.items():
        principals = principals_of(rows)
        zero_hit.append(
            {
                "query": query,
                "filters": json.loads(filters_json),
                "occurrences": len(rows),
                "distinct_principals": len(principals) if principals else None,
                "principals": principals,
                "first_ts": min(row["ts"] for row in rows),
                "last_ts": max(row["ts"] for row in rows),
                "issue_text": zero_hit_issue_text(
                    query,
                    json.loads(filters_json),
                    len(rows),
                    len(principals) if principals else None,
                    min(row["ts"] for row in rows),
                    max(row["ts"] for row in rows),
                ),
            }
        )
    zero_hit.sort(key=lambda item: (-item["occurrences"], item["query"]))

    query_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in search_ok:
        arguments = record.get("args") if isinstance(record.get("args"), dict) else {}
        query_groups[str(arguments.get("query", ""))].append(record)
    query_popularity: list[dict[str, Any]] = []
    for query, rows in query_groups.items():
        hit_counter: Counter[str] = Counter()
        for row in rows:
            for path in row.get("hits") or []:
                hit_counter[str(path)] += 1
        principals = principals_of(rows)
        query_popularity.append(
            {
                "query": query,
                "occurrences": len(rows),
                "distinct_principals": len(principals) if principals else None,
                "top_hits": [
                    {"path": path, "count": count}
                    for path, count in hit_counter.most_common(10)
                ],
            }
        )
    query_popularity.sort(key=lambda item: (-item["occurrences"], item["query"]))

    read_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in reads_ok:
        arguments = record.get("args") if isinstance(record.get("args"), dict) else {}
        path = str(arguments.get("path", ""))
        if path:
            read_groups[path].append(record)
    read_popularity: list[dict[str, Any]] = []
    for path, rows in read_groups.items():
        parts = path.split("/")
        principals = principals_of(rows)
        read_popularity.append(
            {
                "path": path,
                "domain": parts[0] if parts else None,
                "technology": parts[1] if len(parts) > 2 else None,
                "occurrences": len(rows),
                "distinct_principals": len(principals) if principals else None,
            }
        )
    read_popularity.sort(key=lambda item: (-item["occurrences"], item["path"]))

    platform_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in search_ok:
        arguments = record.get("args") if isinstance(record.get("args"), dict) else {}
        platform_groups[platform_key(arguments)].append(record)
    platform_demand: list[dict[str, Any]] = []
    for platform, rows in platform_groups.items():
        principals = principals_of(rows)
        platform_demand.append(
            {
                "platform": platform,
                "occurrences": len(rows),
                "distinct_principals": len(principals) if principals else None,
            }
        )
    platform_demand.sort(key=lambda item: (-item["occurrences"], item["platform"]))

    depth_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in reads_ok:
        arguments = record.get("args") if isinstance(record.get("args"), dict) else {}
        path = str(arguments.get("path", ""))
        if path:
            depth_groups[path].append(record)
    read_depth: list[dict[str, Any]] = []
    for path, rows in depth_groups.items():
        # Sessions: same principal (boot_id when anonymous) with >15 min gaps
        # starting a new visit. Depth and page-turn behaviour are judged per
        # session, not per row, so a paginated read counts as one deep read.
        by_actor: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_actor[session_key(row)].append(row)
        sessions: list[dict[str, Any]] = []
        for actor_rows in by_actor.values():
            sessions.extend(split_sessions(actor_rows))
        single_visit = 0
        page_turn = 0
        for session_rows in sessions:
            metrics = read_session_metrics(session_rows)
            single_visit += metrics["single_visit"]
            page_turn += metrics["page_turn"]
        # Depth is judged per session and only the deepest one is reported:
        # unioning across sessions would let two readers that each saw half a
        # card fake a 100% read. A single paginated session still unions its
        # pages (0..200 + 200..400 of 400 = 100%).
        session_depths = [
            depth
            for depth in (
                coverage_union_depth(session_rows) for session_rows in sessions
            )
            if depth is not None
        ]
        max_depth = max(session_depths) if session_depths else None
        principals = principals_of(rows)
        occurrences = len(rows)
        read_depth.append(
            {
                "path": path,
                "occurrences": occurrences,
                "distinct_principals": len(principals) if principals else None,
                "sessions": len(sessions),
                "max_depth_read": max_depth,
                "single_visit_rate": round(single_visit / len(sessions), 3)
                if sessions
                else None,
                "page_turn_rate": round(page_turn / len(sessions), 3)
                if sessions
                else None,
            }
        )
    read_depth.sort(key=lambda item: (-item["occurrences"], item["path"]))

    failure_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in calls:
        if record.get("ok") is not False:
            continue
        kind = record.get("error_kind")
        if not isinstance(kind, str) or not kind:
            kind = "unknown"
        failure_groups[kind].append(record)
    failure_kinds: list[dict[str, Any]] = []
    for kind, rows in failure_groups.items():
        signal_counter: Counter[str] = Counter()
        for row in rows:
            arguments = row.get("args") if isinstance(row.get("args"), dict) else {}
            tool = row.get("tool")
            if tool == "read_card" and arguments.get("path"):
                signal = str(arguments["path"])
            else:
                signal = str(arguments.get("query", "")) or "(无查询词)"
            signal_counter[signal] += 1
        failure_kinds.append(
            {
                "kind": kind,
                "count": len(rows),
                "top_queries": [
                    {"query": signal, "count": count}
                    for signal, count in signal_counter.most_common(5)
                ],
            }
        )
    failure_kinds.sort(key=lambda item: (-item["count"], item["kind"]))

    week_buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "searches": 0,
            "zero_hits": 0,
            "reads": 0,
            "principals": set(),
        }
    )
    for record in calls:
        week = iso_week(record)
        if week is None:
            continue
        bucket = week_buckets[week]
        tool = record.get("tool")
        if tool == "search" and record.get("ok") is True:
            bucket["searches"] += 1
            if record.get("count") == 0:
                bucket["zero_hits"] += 1
        elif tool == "read_card" and record.get("ok") is True:
            bucket["reads"] += 1
        if record.get("principal") is not None:
            bucket["principals"].add(str(record["principal"]))
    weekly_trend: list[dict[str, Any]] = []
    for week in sorted(week_buckets):
        bucket = week_buckets[week]
        searches = bucket["searches"]
        weekly_trend.append(
            {
                "week": week,
                "searches": searches,
                "zero_hits": bucket["zero_hits"],
                "zero_hit_rate": round(bucket["zero_hits"] / searches, 3)
                if searches
                else 0.0,
                "reads": bucket["reads"],
                "distinct_principals": len(bucket["principals"]),
            }
        )

    response_by_request: dict[str, set[str]] = defaultdict(set)
    for record in calls:
        request_sha = record.get("request_sha256")
        response_sha = record.get("response_sha256")
        if request_sha and response_sha and record.get("tool") in ("search", "discover"):
            response_by_request[str(request_sha)].add(str(response_sha))
    divergence = sum(
        1 for responses in response_by_request.values() if len(responses) > 1
    )

    return {
        "anonymous_mode": bool(anonymous),
        "funnel_totals": {
            "search": len(search_ok),
            "zero_hit": len(search_zero),
            "read_card": len(reads_ok),
        },
        "zero_hit": zero_hit[:top],
        "query_popularity": query_popularity[:top],
        "read_popularity": read_popularity[:top],
        "platform_demand": platform_demand,
        "read_depth": read_depth[:top],
        "failure_kinds": failure_kinds[:top],
        "weekly_trend": weekly_trend,
        "request_response_divergence": divergence,
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = []
    if report["anonymous_mode"]:
        lines.append("匿名模式：频次含重复，无法区分独立人数")
    stats = report["stats"]
    divergence = stats.get("request_response_divergence")
    if divergence:
        lines.append(
            f"WARNING: 检测到 {divergence} 组同 request_sha256 不同 response_sha256"
            "（多实例漂移，建议核对各实例索引 commit）"
        )
    lines.append(
        f"读取 {stats['lines_read']} 行（去重 {stats['duplicates_dropped']} 行，"
        f"坏行 {stats['skipped_malformed']} 行）；事件：{stats['events'] or '无'}"
    )
    lines.append("")
    lines.append("== 零命中 TOP（缺什么）==")
    if report["zero_hit"]:
        for item in report["zero_hit"]:
            distinct = (
                f"{item['distinct_principals']} 人" if item["distinct_principals"] else "匿名"
            )
            lines.append(
                f"  {item['occurrences']:>4} 次 / {distinct:>6} | {item['query']} | "
                f"{format_filters(item['filters'])}"
            )
    else:
        lines.append("  （无零命中记录）")
    lines.append("")
    lines.append("== 查询词热度 TOP（在问什么）==")
    if report["query_popularity"]:
        for item in report["query_popularity"]:
            top_hit = (
                f" → {item['top_hits'][0]['path']}×{item['top_hits'][0]['count']}"
                if item["top_hits"]
                else ""
            )
            lines.append(f"  {item['occurrences']:>4} 次 | {item['query']}{top_hit}")
    else:
        lines.append("  （无检索记录）")
    lines.append("")
    lines.append("== 卡片阅读热度 TOP（什么被消费）==")
    if report["read_popularity"]:
        for item in report["read_popularity"]:
            lines.append(
                f"  {item['occurrences']:>4} 次 | {item['domain']}/{item['technology'] or '-'} | "
                f"{item['path']}"
            )
    else:
        lines.append("  （无读卡记录）")
    lines.append("")
    lines.append("== 平台需求分布（在问哪个平台）==")
    if report.get("platform_demand"):
        for item in report["platform_demand"]:
            distinct = (
                f"{item['distinct_principals']} 人" if item["distinct_principals"] else "匿名"
            )
            lines.append(f"  {item['occurrences']:>4} 次 / {distinct:>6} | {item['platform']}")
    else:
        lines.append("  （无检索记录）")
    lines.append("")
    lines.append("== 失败分类（error_kind）==")
    if report.get("failure_kinds"):
        for item in report["failure_kinds"]:
            top_signal = ""
            if item["top_queries"]:
                signal = item["top_queries"][0]
                top_signal = f" | 高频: {signal['query']}×{signal['count']}"
            lines.append(f"  {item['count']:>4} 次 | {item['kind']}{top_signal}")
    else:
        lines.append("  （无失败记录）")
    lines.append("")
    lines.append("== 周趋势（按周一起始的日期区间）==")
    if report.get("weekly_trend"):
        for item in report["weekly_trend"]:
            lines.append(
                f"  {item['week']} | search {item['searches']:>4} 次 | "
                f"零命中 {item['zero_hits']:>4} 次（率 {item['zero_hit_rate']:.3f}）| "
                f"read_card {item['reads']:>4} 次 | 独立 {item['distinct_principals']} 人"
            )
    else:
        lines.append("  （无记录）")
    return "\n".join(lines)


def _markdown_rate(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"


def render_markdown(report: dict[str, Any]) -> str:
    stats = report["stats"]
    lines: list[str] = []
    lines.append(f"# cannbot-knowledge MCP 调用分析 {report['generated_at'][:10]}")
    lines.append("")
    if report["anonymous_mode"]:
        lines.append("> 匿名模式：频次含重复，无法区分独立人数。")
        lines.append("")
    divergence = stats.get("request_response_divergence")
    if divergence:
        lines.append(
            f"> **WARNING**：检测到 {divergence} 组同 request_sha256 不同"
            " response_sha256（多实例漂移，建议核对各实例索引 commit）。"
        )
        lines.append("")

    # Window totals come from funnel_totals (counted before the boards were
    # truncated to --top); summing the truncated boards would undercount.
    totals = report["funnel_totals"]
    search_total = totals["search"]
    zero_total = totals["zero_hit"]
    read_total = totals["read_card"]
    zero_rate = zero_total / search_total if search_total else 0.0
    lines.append("## 漏斗总览")
    lines.append("")
    lines.append(
        f"读取 {stats['lines_read']} 行（去重 {stats['duplicates_dropped']} 行，"
        f"坏行 {stats['skipped_malformed']} 行）；事件：{stats['events'] or '无'}。"
    )
    lines.append("")
    lines.append(
        f"窗口内共 {search_total} 次 search（其中 {zero_total} 次零命中，"
        f"零命中率 {zero_rate:.1%}）、{read_total} 次 read_card。"
        + ("" if search_total else "窗口内没有检索记录，零命中率无从计算。")
    )
    lines.append("")

    lines.append("## 零命中 TOP")
    lines.append("")
    if report["zero_hit"]:
        lines.append("以下文本可直接粘贴进 knowledge_request Issue 的“已尝试的检索”一节：")
        lines.append("")
        lines.append("```")
        for item in report["zero_hit"]:
            lines.append(item["issue_text"])
            lines.append("")
        lines.append("```")
    else:
        lines.append("（无零命中记录）")
    lines.append("")

    lines.append("## 查询词热度 TOP")
    lines.append("")
    if report["query_popularity"]:
        lines.append("| 查询词 | 次数 | 独立人数 | 首要命中 |")
        lines.append("|---|---|---|---|")
        for item in report["query_popularity"]:
            distinct = item["distinct_principals"]
            top_hit = (
                f"{item['top_hits'][0]['path']}×{item['top_hits'][0]['count']}"
                if item["top_hits"]
                else "-"
            )
            lines.append(
                f"| {item['query']} | {item['occurrences']} | "
                f"{distinct if distinct is not None else '匿名'} | {top_hit} |"
            )
    else:
        lines.append("（无检索记录）")
    lines.append("")

    lines.append("## 平台需求分布")
    lines.append("")
    if report.get("platform_demand"):
        lines.append("| 平台 | 次数 | 独立人数 |")
        lines.append("|---|---|---|")
        for item in report["platform_demand"]:
            distinct = item["distinct_principals"]
            lines.append(
                f"| {item['platform']} | {item['occurrences']} | "
                f"{distinct if distinct is not None else '匿名'} |"
            )
    else:
        lines.append("（无检索记录）")
    lines.append("")

    depth_by_path = {
        item["path"]: item for item in report.get("read_depth") or []
    }
    lines.append("## 卡片阅读热度与消费深度")
    lines.append("")
    lines.append("阅读深度按会话内 offset 覆盖区间并集计算；会话 = 同 principal（匿名时同 boot_id）且相邻调用间隔不超过 15 分钟。")
    lines.append("")
    if report["read_popularity"]:
        lines.append(
            "| 卡片 | 次数 | 独立人数 | 阅读深度 | 单次阅读占比 | 翻页续读占比 |"
        )
        lines.append("|---|---|---|---|---|---|")
        for item in report["read_popularity"]:
            depth = depth_by_path.get(item["path"])
            distinct = item["distinct_principals"]
            lines.append(
                f"| {item['path']} | {item['occurrences']} | "
                f"{distinct if distinct is not None else '匿名'} | "
                f"{_markdown_rate(depth['max_depth_read']) if depth else '-'} | "
                f"{_markdown_rate(depth['single_visit_rate']) if depth else '-'} | "
                f"{_markdown_rate(depth['page_turn_rate']) if depth else '-'} |"
            )
    else:
        lines.append("（无读卡记录）")
    lines.append("")

    lines.append("## 失败分类")
    lines.append("")
    if report.get("failure_kinds"):
        lines.append("| 错误类别 | 次数 | 高频查询词 |")
        lines.append("|---|---|---|")
        for item in report["failure_kinds"]:
            signals = (
                "、".join(
                    f"{entry['query']}×{entry['count']}"
                    for entry in item["top_queries"]
                )
                if item["top_queries"]
                else "-"
            )
            lines.append(f"| {item['kind']} | {item['count']} | {signals} |")
    else:
        lines.append("（无失败记录）")
    lines.append("")

    lines.append("## 周趋势")
    lines.append("")
    if report.get("weekly_trend"):
        lines.append("| 周 | search | 零命中 | 零命中率 | read_card | 独立人数 |")
        lines.append("|---|---|---|---|---|---|")
        for item in report["weekly_trend"]:
            lines.append(
                f"| {item['week']} | {item['searches']} | {item['zero_hits']} | "
                f"{item['zero_hit_rate']:.3f} | {item['reads']} | "
                f"{item['distinct_principals']} |"
            )
    else:
        lines.append("（无记录）")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=None, help="only rows within the last N days")
    parser.add_argument("--top", type=int, default=20, help="rows per board (default 20)")
    parser.add_argument(
        "--log-dir",
        default=None,
        help="comma-separated log directories (default: $%s or %s)"
        % (LOG_DIR_ENV, DEFAULT_STATE_DIR),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="report JSON path (default: <default log dir>/reports/<today>.json)",
    )
    arguments = parser.parse_args(argv)
    if arguments.days is not None and arguments.days < 1:
        parser.error("--days must be a positive integer")
    if arguments.top < 1:
        parser.error("--top must be a positive integer")
    if arguments.log_dir:
        directories = [Path(item.strip()) for item in arguments.log_dir.split(",") if item.strip()]
    else:
        directories = default_log_dirs()
    directories = [directory.expanduser() for directory in directories]
    for directory in directories:
        if not directory.is_dir():
            print(f"error: log directory does not exist: {directory}", file=sys.stderr)
            return 2
    records, read_stats = read_lines(directories)
    records = [record for record in records if within_days(record, arguments.days)]
    unique, duplicates = deduplicate(records)
    event_counts = Counter(
        str(record["event"]) for record in unique if record.get("event")
    )
    aggregated = aggregate(unique, arguments.top)
    report = {
        "schema_version": REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "log_dirs": [str(directory) for directory in directories],
        "days": arguments.days,
        "top": arguments.top,
        "stats": {
            "lines_read": len(records),
            "duplicates_dropped": duplicates,
            "skipped_malformed": read_stats["skipped_malformed"],
            "events": dict(sorted(event_counts.items())),
            "request_response_divergence": aggregated.pop("request_response_divergence"),
        },
        **aggregated,
    }
    output = (
        Path(arguments.output).expanduser()
        if arguments.output
        else default_log_dirs()[0].expanduser() / "reports" /
        f"{datetime.now(timezone.utc):%Y-%m-%d}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path = output.with_suffix(".md")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(render_summary(report))
    print(f"\n报告已写入: {output}")
    print(f"Markdown 摘要已写入: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
