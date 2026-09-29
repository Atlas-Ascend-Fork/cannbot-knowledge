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

"""Run retrieval cases against knowledge-query."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
CASES = ROOT / "evals/retrieval_cases.yaml"


def run_cases(
    data: dict[str, object], roots: dict[str, Path], *, quality_gate: bool = False
) -> int:
    failures: list[str] = []
    misses: list[str] = []
    expected_total = 0
    expected_found = 0
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("retrieval cases must be a list")
    quality = data.get("quality", {})
    if not isinstance(quality, dict):
        raise ValueError("quality must be an object")
    if quality_gate:
        for key in ("min_recall_at_k", "min_mrr"):
            value = quality.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
                or value >= 1
            ):
                raise ValueError(f"quality gate requires a valid positive {key}")
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("retrieval case entries must be objects")
        corpus = str(case.get("corpus", "repository"))
        if corpus not in roots:
            raise ValueError(f"unknown retrieval corpus: {corpus}")
        groups = [[path] for path in case.get("expected", [])] + case.get(
            "expected_any", []
        )
        if any(
            not isinstance(group, list)
            or not group
            or any(not isinstance(path, str) or not path for path in group)
            for group in groups
        ):
            raise ValueError(
                f"{case['id']}: expected groups must be nonempty lists of paths"
            )
        expected = {path for group in groups for path in group}
        expected_total += len(groups)
        command = [
            sys.executable,
            str(QUERY),
            "--knowledge-root",
            str(roots[corpus]),
            "search",
            "--query",
            str(case["query"]),
            "--json",
        ]
        for key, value in case.get("filters", {}).items():
            flag = "--type" if key == "type" else f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    command.append(flag)
                continue
            values = value if isinstance(value, list) else [value]
            for item in values:
                command.extend([flag, str(item)])
        started = time.perf_counter()
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        latencies_ms.append((time.perf_counter() - started) * 1000)
        expected_error = case.get("expected_error")
        if expected_error:
            if completed.returncode == 2 and expected_error in completed.stderr:
                print(f"PASS {case['id']}")
            else:
                failures.append(
                    f"{case['id']}: expected error {expected_error!r}, "
                    f"returncode={completed.returncode} stderr={completed.stderr.strip()!r}"
                )
            continue
        if completed.returncode != 0:
            failures.append(f"{case['id']}: query failed: {completed.stderr.strip()}")
            if groups:
                reciprocal_ranks.append(0.0)
            continue
        payload = json.loads(completed.stdout)
        expected_count = case.get("expected_count")
        count_mismatch = (
            expected_count is not None and payload["count"] != expected_count
        )
        hit_items = {item["path"]: item for item in payload["hits"]}
        hits = set(hit_items)
        missing = [group for group in groups if not hits.intersection(group)]
        leaked = set(case.get("excluded", [])) & hits
        expected_found += len(groups) - len(missing)
        if expected:
            ranks = [hit_items[path]["rank"] for path in expected if path in hit_items]
            reciprocal_ranks.append(1.0 / min(ranks) if ranks else 0.0)
        missing_fields: dict[str, list[str]] = {}
        for expected_path in expected:
            if expected_path not in hit_items:
                continue
            fields = case.get("expected_fields", [])
            absent = [
                field for field in fields if field not in hit_items[expected_path]
            ]
            if absent:
                missing_fields[expected_path] = absent
        out_of_scope = []
        filters = case.get("filters", {})
        for path, item in hit_items.items():
            for option, field in (
                ("domain", "domain"),
                ("technology", "technology"),
                ("type", "profile"),
                ("status", "status"),
            ):
                wanted = filters.get(option)
                if not wanted or (option == "status" and wanted == "all"):
                    continue
                if (
                    option == "technology"
                    and filters.get("include_shared")
                    and item.get(field) == "shared"
                ):
                    continue
                if item.get(field) != wanted:
                    out_of_scope.append(f"{path}: {option}")
            platforms = filters.get("platform", [])
            platforms = [platforms] if isinstance(platforms, str) else platforms
            supported = item.get("platforms", [])
            if (
                platforms
                and "agnostic" not in supported
                and not set(platforms) <= set(supported)
            ):
                out_of_scope.append(f"{path}: platform")
        if missing or leaked or missing_fields or count_mismatch or out_of_scope:
            # Only recall misses may be covered by aggregate quality thresholds.
            # All command, count, field and filtering contracts remain mandatory.
            reports = (
                misses
                if quality_gate and not (leaked or missing_fields or count_mismatch or out_of_scope)
                else failures
            )
            reports.append(
                f"{case['id']}: missing={sorted(missing)} leaked={sorted(leaked)} "
                f"missing_fields={missing_fields} count={payload['count']} "
                f"expected_count={expected_count} out_of_scope={out_of_scope}"
            )
        else:
            print(f"PASS {case['id']}")
    recall = expected_found / expected_total if expected_total else None
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else None
    if quality_gate and (recall is None or mrr is None):
        failures.append("quality: no positive evidence cases to evaluate")
    ordered_latency = sorted(latencies_ms)
    p95_index = max(0, math.ceil(len(ordered_latency) * 0.95) - 1)
    p95_ms = ordered_latency[p95_index] if ordered_latency else 0.0
    min_recall = float(quality.get("min_recall_at_k", 0.0))
    min_mrr = float(quality.get("min_mrr", 0.0))
    minimum_operator = ">" if quality_gate else ">="
    if recall is not None and (recall < min_recall or (quality_gate and recall == min_recall)):
        failures.append(
            f"quality: recall@k={recall:.3f} must be {minimum_operator} {min_recall}"
        )
    if mrr is not None and (mrr < min_mrr or (quality_gate and mrr == min_mrr)):
        failures.append(f"quality: MRR={mrr:.3f} must be {minimum_operator} {min_mrr}")
    recall_text = f"{recall:.3f}" if recall is not None else "N/A"
    mrr_text = f"{mrr:.3f}" if mrr is not None else "N/A"
    print(
        f"QUALITY recall@k={recall_text} MRR={mrr_text} p95={p95_ms:.1f}ms cases={len(cases)}"
    )
    for miss in misses:
        print(f"MISS {miss}", file=sys.stderr)
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quality-gate",
        action="store_true",
        help="Require recall/MRR above thresholds; other assertions still fail.",
    )
    args = parser.parse_args()
    try:
        data = yaml.safe_load(CASES.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("retrieval case file must contain an object")
        return run_cases(data, {"repository": ROOT}, quality_gate=args.quality_gate)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"FAIL retrieval harness: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
