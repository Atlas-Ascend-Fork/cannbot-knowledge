# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Aggregate frozen, separately reviewed Scope judgments without inventing labels."""

from __future__ import annotations

from typing import Any


def summarize_workflows(
    decisions: list[dict[str, Any]],
    created_cards: list[dict[str, Any]],
    stable_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate separate reviewer judgments for RFC workflow metrics.

    These inputs are human review records, not machine Scope states or lint
    results. Pending labels fail instead of silently improving the denominator.
    This validates shape only; it cannot authenticate the reviewer.
    human_scope_complete judges whether applicability is adequately documented,
    including in prose; it does not require optional Scope metadata or every
    dimension to be populated, and must not be inferred from field coverage.
    """
    def records(values, required):
        if not isinstance(values, list):
            raise ValueError("workflow judgments must be lists")
        ids = set()
        for item in values:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                raise ValueError("workflow judgment requires an id")
            if item["id"] in ids:
                raise ValueError("duplicate workflow judgment id")
            ids.add(item["id"])
            if any(not isinstance(item.get(key), bool) for key in required):
                raise ValueError("workflow metrics require complete separate human judgments")
        return values

    decisions = records(decisions, ["completed"])
    completed = [item for item in decisions if item["completed"]]
    if any(not isinstance(item.get("human_applicable"), bool) for item in completed):
        raise ValueError("completed decisions require human_applicable")
    created_cards = records(created_cards, ["human_duplicate"])
    evidence_fields = ["human_source_complete", "human_scope_complete", "human_validation_complete", "human_boundary_complete"]
    stable_cards = records(stable_cards, evidence_fields)
    return {
        "decision_accuracy": sum(item["human_applicable"] for item in completed) / len(completed) if completed else None,
        "completed_decisions": len(completed),
        "incomplete_decisions": len(decisions) - len(completed),
        "duplicate_rate": sum(item["human_duplicate"] for item in created_cards) / len(created_cards) if created_cards else None,
        "reviewed_created_cards": len(created_cards),
        "evidence_completeness": sum(all(item[key] for key in evidence_fields) for item in stable_cards) / len(stable_cards) if stable_cards else None,
        "reviewed_stable_cards": len(stable_cards),
    }


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Each case supplies confirmed_scope, expected paths and ordered judgments.

    Results must carry a separate human_judgment, not Query's scope_match. This
    validates the evaluation input shape; it cannot authenticate human review.
    All cases contribute recall/coverage; only explicit Scope cases contribute
    micro-averaged applicability ratios. Zero denominators are represented by None.
    """
    if not isinstance(cases, list):
        raise ValueError("metric cases must be a list")
    counts = {"match": 0, "conflict": 0, "unknown": 0}
    recall_values = []
    positive = nonempty = explicit = 0
    returned_counts = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("confirmed_scope"), bool):
            raise ValueError("metric cases require a confirmed_scope boolean")
        expected = case.get("expected")
        results = case.get("results")
        if not isinstance(expected, list) or any(not isinstance(path, str) or not path for path in expected):
            raise ValueError("expected must be a list of Concept IDs")
        if len(set(expected)) != len(expected):
            raise ValueError("expected contains duplicate Concept IDs")
        if not isinstance(results, list):
            raise ValueError("results must be an ordered list")
        top = results[:5]
        paths = []
        for item in top:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"]:
                raise ValueError("result requires a Concept ID path")
            paths.append(item["path"])
            if case["confirmed_scope"]:
                judgment = item.get("human_judgment")
                if not isinstance(judgment, str) or judgment not in counts:
                    raise ValueError("explicit Scope metrics require separate human_judgment labels")
                counts[judgment] += 1
        if len(set(paths)) != len(paths):
            raise ValueError("top five results contain duplicate Concept IDs")
        returned_counts.append(len(top))
        if expected:
            positive += 1
            nonempty += bool(top)
            recall_values.append(len(set(paths) & set(expected)) / len(expected))
        explicit += case["confirmed_scope"]
    total = sum(counts.values())
    return {
        "scope_cases": explicit,
        "scope_returned": total,
        "scope_precision_at_5": counts["match"] / total if total else None,
        "conflict_rate_at_5": counts["conflict"] / total if total else None,
        "unknown_rate_at_5": counts["unknown"] / total if total else None,
        "recall_at_5": sum(recall_values) / len(recall_values) if recall_values else None,
        "nonempty_recall_rate": nonempty / positive if positive else None,
        "returned_counts": returned_counts,
        "counts": counts,
    }
