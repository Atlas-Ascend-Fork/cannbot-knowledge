#!/usr/bin/env python3
"""Build an auditable semantic re-review queue from miner manifests.

This script never accepts or rejects knowledge.  It inventories existing DRAFT
candidates and old skipped entries whose reason may have been caused by the
legacy repair-only evidence gate, then assigns stable shards for miner agents.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


RECLASSIFY_REASONS = {
    "failed_validation",
    "incomplete_code_chain",
    "incomplete_code_pair",
    "incomplete_validation",
    "invalid_after",
    "missing_complete_before_after",
    "negative_result",
    "no_after_validation",
    "no_closure",
    "no_end_to_end_performance_gain",
    "no_final_validation",
    "no_full_validation",
    "no_full_before_after",
    "no_performance_closure",
    "no_validated_after",
    "no_validation_closure",
    "unstable_performance",
    "from_scratch_no_failure",
}


def event_count(manifest):
    coverage = manifest.get("coverage") or {}
    for key in ("normalized_events", "total_events", "event_count", "scanned_events"):
        value = coverage.get(key)
        if isinstance(value, int):
            return value
    return 0


def stable_shard(trace_id, shards):
    digest = hashlib.sha256(trace_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % shards


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest_root", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=3)
    parser.add_argument(
        "--broad-unverifiable-min-events",
        type=int,
        default=100,
        help="also re-review generic unverifiable traces at or above this size",
    )
    args = parser.parse_args()
    if args.shards < 1:
        parser.error("--shards must be positive")

    items = []
    reason_counts = Counter()
    manifests = sorted(args.manifest_root.rglob("manifest.json"))
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"invalid manifest {manifest_path}: {exc}") from exc
        trace_id = str(manifest.get("trace_id") or manifest_path.parent.name)
        count = event_count(manifest)
        shard = stable_shard(trace_id, args.shards)
        for candidate in manifest.get("candidates") or []:
            items.append(
                {
                    "trace_id": trace_id,
                    "manifest_path": str(manifest_path.resolve()),
                    "event_count": count,
                    "shard": shard,
                    "source_kind": "candidate",
                    "reason": "existing_candidate",
                    "draft_path": candidate.get("draft_path"),
                    "claim": candidate.get("signal") or candidate.get("phenomenon") or "",
                }
            )
            reason_counts["existing_candidate"] += 1
        for skipped in manifest.get("skipped") or []:
            reason = str(skipped.get("reason") or "")
            broad = reason == "unverifiable" and count >= args.broad_unverifiable_min_events
            if reason not in RECLASSIFY_REASONS and not broad:
                continue
            items.append(
                {
                    "trace_id": trace_id,
                    "manifest_path": str(manifest_path.resolve()),
                    "event_count": count,
                    "shard": shard,
                    "source_kind": "skipped",
                    "reason": reason,
                    "claim": skipped.get("claim") or skipped.get("detail") or "",
                    "event_refs": skipped.get("event_refs") or [],
                    "reclassification_required": True,
                }
            )
            reason_counts[reason] += 1

    summary = {
        "manifest_count": len(manifests),
        "queue_item_count": len(items),
        "trace_count": len({item["trace_id"] for item in items}),
        "shards": args.shards,
        "by_source_kind": dict(Counter(item["source_kind"] for item in items)),
        "by_reason": dict(sorted(reason_counts.items())),
        "by_shard": dict(sorted(Counter(str(item["shard"]) for item in items).items())),
    }
    payload = {
        "schema_version": "trace.rereview-queue.v1",
        "policy": {
            "semantic_decision_required": True,
            "automatic_publish": False,
            "knowledge_forms": [
                "repair_recipe",
                "diagnostic_rule",
                "negative_result",
                "validated_pattern",
            ],
        },
        "summary": summary,
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
