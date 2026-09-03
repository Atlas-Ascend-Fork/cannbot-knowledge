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

"""Run auditable retrieval smoke cases against knowledge-query."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
INDEX = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
CASES = ROOT / "evals/retrieval_cases.yaml"


def build_synthetic_root(data: dict[str, object], target: Path) -> None:
    shutil.copytree(ROOT / "governance", target / "governance")
    (target / "knowledge").mkdir(parents=True)
    for fixture in data.get("synthetic_cards", []):
        if not isinstance(fixture, dict):
            raise ValueError("synthetic_cards entries must be objects")
        path = target / str(fixture["path"])
        metadata = fixture["metadata"]
        body = str(fixture["body"]).strip()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
            + "\n---\n\n"
            + body
            + "\n",
            encoding="utf-8",
        )
    built = subprocess.run(
        [
            sys.executable,
            str(INDEX),
            "--knowledge-root",
            str(target),
            "build",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if built.returncode != 0:
        raise ValueError(f"cannot build synthetic retrieval index: {built.stderr.strip()}")


def run_cases(data: dict[str, object], roots: dict[str, Path]) -> int:
    failures: list[str] = []
    expected_total = 0
    expected_found = 0
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("retrieval cases must be a list")
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("retrieval case entries must be objects")
        corpus = str(case.get("corpus", "repository"))
        if corpus not in roots:
            raise ValueError(f"unknown retrieval corpus: {corpus}")
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
            continue
        payload = json.loads(completed.stdout)
        expected_count = case.get("expected_count")
        count_mismatch = expected_count is not None and payload["count"] != expected_count
        hit_items = {item["path"]: item for item in payload["hits"]}
        hits = set(hit_items)
        expected = set(case.get("expected", []))
        missing = expected - hits
        leaked = set(case.get("excluded", [])) & hits
        expected_total += len(expected)
        expected_found += len(expected & hits)
        if expected:
            ranks = [hit_items[path]["rank"] for path in expected if path in hit_items]
            reciprocal_ranks.append(1.0 / min(ranks) if ranks else 0.0)
        missing_fields: dict[str, list[str]] = {}
        for expected_path in case.get("expected", []):
            if expected_path not in hit_items:
                continue
            fields = case.get("expected_fields", [])
            absent = [field for field in fields if field not in hit_items[expected_path]]
            if absent:
                missing_fields[expected_path] = absent
        if missing or leaked or missing_fields or count_mismatch:
            failures.append(
                f"{case['id']}: missing={sorted(missing)} leaked={sorted(leaked)} "
                f"missing_fields={missing_fields} count={payload['count']} "
                f"expected_count={expected_count}"
            )
        else:
            print(f"PASS {case['id']}")
    quality = data.get("quality", {})
    if not isinstance(quality, dict):
        raise ValueError("quality must be an object")
    recall = expected_found / expected_total if expected_total else None
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else None
    ordered_latency = sorted(latencies_ms)
    p95_index = max(0, math.ceil(len(ordered_latency) * 0.95) - 1)
    p95_ms = ordered_latency[p95_index] if ordered_latency else 0.0
    if recall is not None and recall < float(quality.get("min_recall_at_k", 0.0)):
        failures.append(
            f"quality: recall@k={recall:.3f} below {quality['min_recall_at_k']}"
        )
    if mrr is not None and mrr < float(quality.get("min_mrr", 0.0)):
        failures.append(f"quality: MRR={mrr:.3f} below {quality['min_mrr']}")
    if p95_ms > float(quality.get("max_p95_ms", float("inf"))):
        failures.append(
            f"quality: p95={p95_ms:.1f}ms above {quality['max_p95_ms']}ms"
        )
    recall_text = f"{recall:.3f}" if recall is not None else "N/A"
    mrr_text = f"{mrr:.3f}" if mrr is not None else "N/A"
    print(f"QUALITY recall@k={recall_text} MRR={mrr_text} p95={p95_ms:.1f}ms cases={len(cases)}")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    try:
        data = yaml.safe_load(CASES.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("retrieval case file must contain an object")
        with tempfile.TemporaryDirectory() as temporary:
            synthetic_root = Path(temporary) / "synthetic-repository"
            build_synthetic_root(data, synthetic_root)
            return run_cases(data, {"repository": ROOT, "synthetic": synthetic_root})
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"FAIL retrieval harness: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
