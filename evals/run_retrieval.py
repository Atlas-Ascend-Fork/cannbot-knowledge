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

"""Run retrieval cases against knowledge-query.

Cases may supply a structured ``scope`` and assert returned machine states via
``expected_scope_states`` or audited conflicts via ``expected_scope_excluded``.
These assertions verify the retrieval contract, not human applicability labels.
The original case file and quality thresholds remain the default.
Optional preflight checks expected-card eligibility before running or scoring
queries. It checks declared filters, not semantic correctness or text ranking.
"""

from __future__ import annotations

import argparse
import importlib.util
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


def query_arguments(case: dict) -> list[str]:
    """Use identical query arguments for preflight and the actual execution."""
    arguments = ["search", "--query", str(case["query"]), "--json"]
    filters = case.get("filters", {})
    if not isinstance(filters, dict) or any(not isinstance(key, str) for key in filters):
        raise ValueError("case.filters must be an object with string keys")
    # Generic flags normalize underscores to hyphens; argparse may also accept
    # unique prefixes. Keep every Scope spelling on the audited case.scope path.
    if any(key.replace("_", "-").startswith("scope") for key in filters):
        raise ValueError("use case.scope as the only Scope input")
    if "scope" in case:
        if not isinstance(case["scope"], dict):
            raise ValueError("case.scope must be a Scope object")
        arguments.extend(["--scope-json", json.dumps(case["scope"], ensure_ascii=False)])
    for key, value in filters.items():
        flag = "--type" if key == "type" else f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                arguments.append(flag)
            continue
        for item in value if isinstance(value, list) else [value]:
            arguments.extend([flag, str(item)])
    return arguments


def preflight_cases(data: dict, roots: dict[str, Path]) -> dict:
    """Reject impossible positive expectations without changing recall denominators.

    Unknown Scope remains eligible. Alternative groups need at least one eligible
    member. Negative and expected-error cases are left to the actual query run.
    Only the prepared index and the Query Skill's own matching code are used.
    """
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("retrieval cases must be a list")
    spec = importlib.util.spec_from_file_location("retrieval_preflight_query", QUERY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    opened, reports, ids = {}, [], set()
    try:
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
                raise ValueError("preflight cases require nonempty string ids")
            if case["id"] in ids:
                raise ValueError("duplicate preflight case id")
            ids.add(case["id"])
            expected, expected_any = case.get("expected", []), case.get("expected_any", [])
            if not isinstance(expected, list) or not isinstance(expected_any, list):
                raise ValueError("expected and expected_any must be lists")
            groups = [[path] for path in expected] + expected_any
            if any(not isinstance(g, list) or not g or any(not isinstance(p, str) or not p for p in g) for g in groups):
                raise ValueError("expected groups must be nonempty lists of paths")
            if case.get("expected_error") or not groups:
                reports.append({"id": case["id"], "status": "not_positive_case", "groups": []})
                continue
            corpus = str(case.get("corpus", "repository"))
            if corpus not in roots:
                raise ValueError(f"unknown retrieval corpus: {corpus}")
            root = roots[corpus]
            if corpus not in opened:
                connection, metadata = module.open_index(root)
                opened[corpus] = (connection, module.load_cards(connection), metadata)
            _, cards, _ = opened[corpus]
            args = module.build_parser().parse_args(query_arguments(case))
            module.apply_default_platform(args)
            eligible, mapped_task, scope_registry = module.search_candidates(root, cards, args)
            by_path = {card.path: card for card in cards}
            checked = []
            for group in groups:
                alternatives = []
                for path in group:
                    card = by_path.get(path)
                    comparison = None
                    if card is None:
                        reason = "missing_concept"
                    elif card.doc_id not in eligible:
                        reason = "metadata_filter_conflict"
                    else:
                        if scope_registry is not None:
                            comparison = scope_registry.compare(args.scope, card.metadata.get("scope"))
                        reason = "scope_conflict" if comparison and comparison["state"] == "conflict" else None
                    alternatives.append({"path": path, "eligible": reason is None, "reason": reason,
                                         "scope_match": comparison,
                                         "metadata": None if card is None else {
                                             "domain": card.domain, "technology": card.technology,
                                             "profile": card.profile, "status": card.metadata.get("status"),
                                             "platforms": card.metadata.get("platforms"),
                                         }})
                checked.append({"eligible": any(a["eligible"] for a in alternatives), "alternatives": alternatives})
            reports.append({"id": case["id"], "status": "eligible" if all(g["eligible"] for g in checked) else "invalid_expectation",
                            "request": module.request_payload(args, mapped_task), "groups": checked})
        failures = [r["id"] for r in reports if r["status"] == "invalid_expectation"]
        return {"status": "invalid_expectations" if failures else "ready", "failed_cases": failures,
                "cases": reports, "indexes": {name: value[2] for name, value in opened.items()},
                "note": "Declared eligibility only; not relevance, applicability confirmation, or human review. No cases were removed from scoring."}
    finally:
        for connection, _, _ in opened.values():
            connection.close()


def scope_state(item: object) -> str | None:
    value = item.get("scope_match") if isinstance(item, dict) else None
    state = value.get("state") if isinstance(value, dict) else None
    return state if isinstance(state, str) else None


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
        command = [sys.executable, str(QUERY), "--knowledge-root", str(roots[corpus])]
        scoped = "scope" in case
        scope_states = case.get("expected_scope_states", {})
        scope_excluded = case.get("expected_scope_excluded", [])
        if not isinstance(scope_states, dict) or any(
            not isinstance(path, str) or not path
            or not isinstance(state, str) or state not in {"match", "unknown"}
            for path, state in scope_states.items()
        ):
            raise ValueError("expected_scope_states must map Concept IDs to match/unknown")
        if not isinstance(scope_excluded, list) or any(
            not isinstance(path, str) or not path for path in scope_excluded
        ):
            raise ValueError("expected_scope_excluded must be a list of Concept IDs")
        if (scope_states or scope_excluded) and not scoped:
            raise ValueError("Scope assertions require an explicit case.scope")
        command.extend(query_arguments(case))
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
        scope_errors = []
        if scoped:
            scope_filter = payload.get("scope_filter")
            if not isinstance(scope_filter, dict) or scope_filter.get("enabled") is not True:
                scope_errors.append("explicit Scope filter was not enabled")
                scope_filter = {}
            for path, item in hit_items.items():
                if scope_state(item) not in {"match", "unknown"}:
                    scope_errors.append(f"{path}: invalid returned Scope state")
            for path, state in scope_states.items():
                actual = scope_state(hit_items.get(path))
                if actual != state:
                    scope_errors.append(f"{path}: expected {state}, got {actual}")
            exclusions = scope_filter.get("excluded", [])
            if not isinstance(exclusions, list) or any(
                not isinstance(item, dict) or not isinstance(item.get("path"), str)
                or scope_state(item) != "conflict" for item in exclusions
            ):
                scope_errors.append("invalid Scope exclusion audit")
                exclusions = []
            excluded_items = {item["path"]: item for item in exclusions}
            for path in scope_excluded:
                actual = scope_state(excluded_items.get(path))
                if path in hits or actual != "conflict":
                    scope_errors.append(f"{path}: expected audited conflict exclusion")
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
        if missing or leaked or missing_fields or count_mismatch or out_of_scope or scope_errors:
            # Only recall misses may be covered by aggregate quality thresholds.
            # All command, count, field and filtering contracts remain mandatory.
            reports = (
                misses
                if quality_gate and not (leaked or missing_fields or count_mismatch or out_of_scope or scope_errors)
                else failures
            )
            reports.append(
                f"{case['id']}: missing={sorted(missing)} leaked={sorted(leaked)} "
                f"missing_fields={missing_fields} count={payload['count']} "
                f"expected_count={expected_count} out_of_scope={out_of_scope}"
                + (f" scope_errors={scope_errors}" if scope_errors else "")
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
    parser.add_argument("--cases", type=Path, default=CASES, help="Optional retrieval case file; defaults to the existing corpus.")
    parser.add_argument(
        "--quality-gate",
        action="store_true",
        help="Require recall/MRR above thresholds; other assertions still fail.",
    )
    preflight = parser.add_mutually_exclusive_group()
    preflight.add_argument("--preflight", action="store_true", help="Reject impossible positive expectations before running queries; keep unknown Scope eligible.")
    preflight.add_argument("--preflight-only", action="store_true", help="Only report expected-card eligibility from the prepared index; no ranking metrics.")
    args = parser.parse_args()
    try:
        data = yaml.safe_load(args.cases.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("retrieval case file must contain an object")
        if args.preflight_only and args.quality_gate:
            raise ValueError("--preflight-only does not run the quality gate")
        if args.preflight or args.preflight_only:
            report = preflight_cases(data, {"repository": ROOT})
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if report["status"] != "ready":
                return 2
            if args.preflight_only:
                return 0
        return run_cases(data, {"repository": ROOT}, quality_gate=args.quality_gate)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"FAIL retrieval harness: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
