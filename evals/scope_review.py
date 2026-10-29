# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Validate frozen A/B review inputs before computing RFC Scope metrics.

Run as ``python -m evals.scope_review --help``. No judgments are inferred from
machine matches. Reviewer identity is a declaration, not authenticated here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from evals.scope_metrics import summarize


def equivalence_fingerprint(equivalence: dict) -> str:
    raw = json.dumps(equivalence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def evaluate_review(review: dict, captures: dict, capture_sha256: dict, equivalence: dict) -> dict:
    """Reject changed captures and incomplete coverage; pending labels do not score."""
    if not isinstance(review, dict) or review.get("schema_version") != "rfc47.human-evaluation.v1":
        raise ValueError("unsupported human review schema")
    if not isinstance(review.get("human_review_complete"), bool):
        raise ValueError("human_review_complete must be a boolean")
    if not isinstance(equivalence, dict) or any(
        not isinstance(key, str) or not key or not isinstance(value, str) or not value
        for key, value in equivalence.items()
    ):
        raise ValueError("equivalence must map Concept IDs to Concept IDs")

    def canonical(path):
        seen = set()
        while path in equivalence and equivalence[path] != path:
            if path in seen:
                raise ValueError("equivalence contains a cycle")
            seen.add(path)
            path = equivalence[path]
        return path

    for path in equivalence:
        canonical(path)
    if review.get("equivalence_sha256") != equivalence_fingerprint(equivalence):
        raise ValueError("review migration equivalence has changed")
    if review.get("capture_sha256") != capture_sha256 or set(capture_sha256) != {"A", "B"}:
        raise ValueError("review is not bound to these exact capture bytes")
    variants = review.get("variants")
    if not isinstance(variants, dict) or set(variants) != {"A", "B"} or set(captures) != {"A", "B"}:
        raise ValueError("both A and B are required")
    pending = []
    reviewer = review.get("reviewer")
    if reviewer is None:
        pending.append("reviewer")
    elif not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("reviewer must be a nonempty name")
    ids = None
    ordered = {}
    for variant in ["A", "B"]:
        capture = captures[variant]
        if not isinstance(capture, dict) or capture.get("variant") != variant:
            raise ValueError("capture variant mismatch")
        cases, judgments = capture.get("cases"), variants[variant]
        if not isinstance(cases, list) or not cases or not isinstance(judgments, list):
            raise ValueError("captures and judgments require nonempty case lists")
        case_ids = [item.get("id") for item in cases if isinstance(item, dict)]
        if len(case_ids) != len(cases) or any(not isinstance(key, str) or not key for key in case_ids):
            raise ValueError("capture case requires an id")
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("capture contains duplicate case ids")
        if ids is not None and case_ids != ids:
            raise ValueError("A/B case coverage or order differs")
        ids = case_ids
        if [item.get("id") for item in judgments if isinstance(item, dict)] != ids or len(judgments) != len(cases):
            raise ValueError("review case coverage or order differs from capture")
        ordered[variant] = judgments
        for capture_case, case in zip(cases, judgments):
            prefix = f"{variant}.{case['id']}"
            if "error" in capture_case:
                raise ValueError("failed capture cannot be scored as a successful experiment")
            results, labels = capture_case.get("results"), case.get("results")
            if not isinstance(results, list) or len(results) > 5 or not isinstance(labels, list):
                raise ValueError("capture and judgments require ordered top-five results")
            paths = [item.get("path") for item in results if isinstance(item, dict)]
            if len(paths) != len(results) or any(not isinstance(path, str) or not path for path in paths):
                raise ValueError("capture result requires a Concept ID")
            if len(set(paths)) != len(paths):
                raise ValueError("duplicate capture result")
            if [item.get("path") for item in labels if isinstance(item, dict)] != paths or len(labels) != len(results):
                raise ValueError("review result paths or order differ from capture")
            for rank, item in enumerate(labels, 1):
                label = item.get("human_judgment")
                if label is None:
                    pending.append(f"{prefix}.results.{rank}")
                elif not isinstance(label, str) or label not in {"match", "conflict", "unknown"}:
                    raise ValueError("invalid human_judgment")
            value = case.get("confirmed_scope")
            if value is None:
                pending.append(f"{prefix}.confirmed_scope")
            elif not isinstance(value, bool):
                raise ValueError("confirmed_scope must be boolean after review")
            for key in ["expected", "excluded", "answer_points"]:
                values = case.get(key)
                if values is None:
                    pending.append(f"{prefix}.{key}")
                elif not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
                    raise ValueError(f"{key} must be a list of nonempty strings")
                elif len(values) != len(set(values)):
                    raise ValueError(f"duplicate {key}")
    if captures["A"].get("cases_input_sha256") != captures["B"].get("cases_input_sha256"):
        raise ValueError("A/B captures used different frozen inputs")
    frozen = captures["A"].get("cases_input_sha256")
    if not isinstance(frozen, str) or len(frozen) != 64 or any(ch not in "0123456789abcdef" for ch in frozen):
        raise ValueError("capture requires a frozen cases SHA-256")
    if review.get("cases_input_sha256") != frozen:
        raise ValueError("review is bound to different frozen cases")
    for a, b, ca, cb in zip(ordered["A"], ordered["B"], captures["A"]["cases"], captures["B"]["cases"]):
        requests = []
        for captured in [ca, cb]:
            request = copy.deepcopy(captured.get("request"))
            if not isinstance(request, dict) or not isinstance(request.get("filters"), dict):
                raise ValueError("capture requires a query request and filters")
            request.pop("scope", None)
            request["filters"].pop("scope", None)
            requests.append(request)
        if requests[0] != requests[1]:
            raise ValueError("A/B differ in query conditions other than the Scope extension")
        if a.get("confirmed_scope") != b.get("confirmed_scope"):
            raise ValueError("A/B must review applicability against the same confirmed conditions")
        for key in ["expected", "excluded"]:
            if a.get(key) is not None and b.get(key) is not None:
                if {canonical(path) for path in a[key]} != {canonical(path) for path in b[key]}:
                    raise ValueError(f"A/B {key} differs after migration equivalence")
        if a.get("answer_points") is not None and b.get("answer_points") is not None and a["answer_points"] != b["answer_points"]:
            raise ValueError("A/B answer points must use the same frozen gold")
    if pending or not review["human_review_complete"]:
        if review["human_review_complete"]:
            raise ValueError("review marked complete with pending judgments")
        return {"status": "awaiting_human_review", "cases": len(ids), "pending_fields": len(pending),
                "pending": pending, "metrics": None}

    metrics = {}
    for variant, cases in ordered.items():
        metrics[variant] = summarize(cases)
        recalls = []
        violations = []
        for case in cases:
            expected = {canonical(path) for path in case["expected"]}
            returned = {canonical(item["path"]) for item in case["results"]}
            if expected:
                recalls.append(len(expected & returned) / len(expected))
            excluded = {canonical(path) for path in case["excluded"]}
            if returned & excluded:
                violations.append({"id": case["id"], "excluded_hits": sorted(returned & excluded)})
        metrics[variant]["recall_at_5"] = sum(recalls) / len(recalls) if recalls else None
        metrics[variant]["gold_exclusion_violations"] = violations
    a, b = metrics["A"], metrics["B"]
    directions = {"recall_at_5": "nondecreasing", "nonempty_recall_rate": "nondecreasing",
                  "scope_precision_at_5": "increasing", "conflict_rate_at_5": "nonincreasing"}
    criteria = {}
    for key, direction in directions.items():
        av, bv = a[key], b[key]
        criteria[key] = av is not None and bv is not None and (
            bv > av if direction == "increasing" else bv >= av if direction == "nondecreasing" else bv <= av)
    criteria["gold_exclusions"] = not b["gold_exclusion_violations"]
    return {"status": "reviewed", "cases": len(ids), "metrics": metrics, "criteria": criteria,
            "retrieval_criteria_passed": all(criteria.values()),
            "acceptance_complete": False,
            "note": "Retrieval metrics only; workflow judgments, compatibility and repository gates are separate."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--equivalence", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = {key: path.read_bytes() for key, path in [("A", args.baseline), ("B", args.candidate)]}
        report = evaluate_review(json.loads(args.review.read_text()),
                                 {key: json.loads(value) for key, value in raw.items()},
                                 {key: hashlib.sha256(value).hexdigest() for key, value in raw.items()},
                                 json.loads(args.equivalence.read_text()))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["status"] != "reviewed" else 0 if report["retrieval_criteria_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
