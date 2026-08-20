#!/usr/bin/env python3
"""Validate decision-scoped retrieval state and optionally create a ready receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from retrieval.index import load_cards, open_index  # noqa: E402
from retrieval.root import (  # noqa: E402
    atomic_create_json,
    canonical_json_sha256,
    extract_knowledge_root,
    resolve_root,
    sha256_file,
)


sys.dont_write_bytecode = True
STATE_SCHEMA = "cannbot-retrieval-state.v1"
REVIEW_SCHEMA = "cannbot-retrieval-review.v1"
READY_SCHEMA = "cannbot-retrieval-ready.v1"
RECEIPT_SCHEMA = "cannbot-knowledge-search.v2"
SEARCH_SCHEMA = "knowledge-search.v4"
DECISION_STATUSES = {"covered", "conflicting", "insufficient", "gap"}


class Audit:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []

    def error(self, code: str, location: str, message: str) -> None:
        self.errors.append({"code": code, "location": location, "message": message})

    def warning(self, code: str, location: str, message: str) -> None:
        self.warnings.append({"code": code, "location": location, "message": message})


def read_json(path: Path, audit: Audit, location: str) -> dict[str, Any]:
    if not path.is_absolute():
        audit.error("path.absolute", location, "path must be absolute")
        return {}
    if not path.is_file():
        audit.error("path.exists", location, f"file does not exist: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        audit.error("json.invalid", location, str(exc))
        return {}
    if not isinstance(value, dict):
        audit.error("json.object", location, "top-level JSON must be an object")
        return {}
    return value


def string(value: Any, audit: Audit, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        audit.error("value.string", location, "must be a non-empty string")
        return ""
    return value.strip()


def string_list(value: Any, audit: Audit, location: str) -> list[str]:
    if not isinstance(value, list):
        audit.error("value.list", location, "must be a list")
        return []
    result = []
    for index, item in enumerate(value):
        result.append(string(item, audit, f"{location}[{index}]"))
    if len(result) != len(set(result)):
        audit.error("value.duplicate", location, "must not contain duplicates")
    return [item for item in result if item]


def validate_state(
    root: Path,
    state_path: Path,
    review_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any], Audit, bool]:
    audit = Audit()
    state = read_json(state_path, audit, "state")
    connection, index_metadata = open_index(root, full=True)
    try:
        cards = {card.path: card for card in load_cards(connection)}
    finally:
        connection.close()
    if state.get("schema_version") != STATE_SCHEMA:
        audit.error("state.schema", "state.schema_version", f"expected {STATE_SCHEMA}")

    target = state.get("target")
    if not isinstance(target, dict):
        audit.error("target.object", "state.target", "must be an object")
        target = {}
    string(target.get("entity"), audit, "state.target.entity")
    platforms = string_list(target.get("platforms"), audit, "state.target.platforms")
    known_platforms = set(load_contract(root).platforms)
    unknown = sorted(set(platforms) - known_platforms)
    if unknown:
        audit.error(
            "target.platform",
            "state.target.platforms",
            f"unknown platforms: {', '.join(unknown)}",
        )
    if not platforms:
        audit.error("target.platform", "state.target.platforms", "at least one platform is required")

    decisions_value = state.get("decisions")
    if not isinstance(decisions_value, list) or not decisions_value:
        audit.error("decision.list", "state.decisions", "must be a non-empty list")
        decisions_value = []
    decision_ids: set[str] = set()
    decision_statuses: dict[str, str] = {}
    receipt_sha256s: dict[str, str] = {}
    for index, decision in enumerate(decisions_value):
        location = f"state.decisions[{index}]"
        if not isinstance(decision, dict):
            audit.error("decision.object", location, "must be an object")
            continue
        decision_id = string(decision.get("id"), audit, location + ".id")
        string(decision.get("question"), audit, location + ".question")
        if decision_id in decision_ids:
            audit.error("decision.duplicate", location + ".id", f"duplicate decision: {decision_id}")
        decision_ids.add(decision_id)
        status = string(decision.get("status"), audit, location + ".status")
        if status not in DECISION_STATUSES:
            audit.error(
                "decision.status",
                location + ".status",
                f"must be one of: {', '.join(sorted(DECISION_STATUSES))}",
            )
        decision_statuses[decision_id] = status

        receipts = string_list(decision.get("receipts"), audit, location + ".receipts")
        if status != "gap" and not receipts:
            audit.error("decision.receipts", location + ".receipts", "non-gap decision needs a receipt")
        receipt_evidence: dict[str, str] = {}
        for receipt_index, receipt_value in enumerate(receipts):
            receipt_path = Path(receipt_value)
            receipt_location = f"{location}.receipts[{receipt_index}]"
            receipt = read_json(receipt_path, audit, receipt_location)
            if receipt_path.is_absolute() and receipt_path.is_file():
                receipt_sha256s[str(receipt_path)] = sha256_file(receipt_path)
            if receipt.get("schema_version") != RECEIPT_SCHEMA:
                audit.error("receipt.schema", receipt_location, f"expected {RECEIPT_SCHEMA}")
                continue
            request = receipt.get("request")
            if not isinstance(request, dict):
                audit.error("receipt.request", receipt_location + ".request", "must be an object")
                request = {}
            request_sha256 = canonical_json_sha256(request)
            if receipt.get("request_sha256") != request_sha256:
                audit.error(
                    "receipt.request_hash",
                    receipt_location + ".request_sha256",
                    "does not match the canonical request content",
                )
            if request.get("decision") != decision_id:
                audit.error(
                    "receipt.decision",
                    receipt_location,
                    "receipt request.decision must equal the decision id",
                )
            if receipt.get("knowledge_root") != str(root):
                audit.error(
                    "receipt.root",
                    receipt_location + ".knowledge_root",
                    "does not match the current knowledge root",
                )
            index_value = receipt.get("index")
            if not isinstance(index_value, dict):
                audit.error("receipt.index", receipt_location, "receipt index provenance is missing")
            else:
                for field in ("content_fingerprint", "governance_fingerprint"):
                    if index_value.get(field) != index_metadata.get(field):
                        audit.error(
                            "receipt.stale",
                            receipt_location + ".index." + field,
                            "receipt does not match the current prepared index",
                        )
            result = receipt.get("result")
            if not isinstance(result, dict):
                audit.error("receipt.result", receipt_location + ".result", "must be an object")
                result = {}
            if result.get("schema_version") != SEARCH_SCHEMA:
                audit.error(
                    "receipt.result_schema",
                    receipt_location + ".result.schema_version",
                    f"expected {SEARCH_SCHEMA}",
                )
            if result.get("request") != request:
                audit.error(
                    "receipt.result_request",
                    receipt_location + ".result.request",
                    "does not match the receipt request",
                )
            if result.get("request_sha256") != request_sha256:
                audit.error(
                    "receipt.result_request_hash",
                    receipt_location + ".result.request_sha256",
                    "does not match the canonical request content",
                )
            if result.get("index") != index_value:
                audit.error(
                    "receipt.result_index",
                    receipt_location + ".result.index",
                    "does not match the receipt index provenance",
                )
            results = result.get("results")
            hits_alias = result.get("hits")
            if not isinstance(results, list):
                audit.error("receipt.results", receipt_location + ".result.results", "must be a list")
                results = []
            if hits_alias != results:
                audit.error(
                    "receipt.hits_alias",
                    receipt_location + ".result.hits",
                    "must equal result.results",
                )
            if result.get("count") != len(results):
                audit.error(
                    "receipt.result_count",
                    receipt_location + ".result.count",
                    "does not match the number of results",
                )
            for hit in results:
                if isinstance(hit, dict) and isinstance(hit.get("path"), str):
                    receipt_evidence[hit["path"]] = str(hit.get("card_sha256", ""))

        evidence = decision.get("evidence")
        if not isinstance(evidence, list):
            audit.error("evidence.list", location + ".evidence", "must be a list")
            evidence = []
        if status in {"covered", "conflicting"} and not evidence:
            audit.error("evidence.required", location + ".evidence", f"{status} decision needs evidence")
        for evidence_index, item in enumerate(evidence):
            item_location = f"{location}.evidence[{evidence_index}]"
            if not isinstance(item, dict):
                audit.error("evidence.object", item_location, "must be an object")
                continue
            path = string(item.get("path"), audit, item_location + ".path")
            fingerprint = string(
                item.get("card_sha256"), audit, item_location + ".card_sha256"
            )
            if receipt_evidence.get(path) != fingerprint:
                audit.error(
                    "evidence.receipt",
                    item_location,
                    "evidence path and fingerprint must occur in a bound search receipt",
                )
            current = cards.get(path)
            if current is None:
                audit.error("evidence.path", item_location + ".path", "card no longer exists")
            elif current.card_sha256 != fingerprint:
                audit.error(
                    "evidence.stale",
                    item_location + ".card_sha256",
                    "card content changed after retrieval",
                )

    state_sha256 = sha256_file(state_path) if state_path.is_file() else ""
    review: dict[str, Any] = {}
    if review_path is not None:
        review = read_json(review_path, audit, "review")
        if review.get("schema_version") != REVIEW_SCHEMA:
            audit.error("review.schema", "review.schema_version", f"expected {REVIEW_SCHEMA}")
        if review.get("state_sha256") != state_sha256:
            audit.error("review.state", "review.state_sha256", "does not match state content")
        if review.get("verdict") not in {"approve", "reject"}:
            audit.error("review.verdict", "review.verdict", "must be approve or reject")
        if review.get("verdict") == "reject":
            audit.error("review.reject", "review.verdict", "review rejected the retrieval state")

    ready = not audit.errors and bool(decision_statuses) and all(
        status == "covered" for status in decision_statuses.values()
    )
    details = {
        "state_sha256": state_sha256,
        "decision_statuses": decision_statuses,
        "index": {
            "content_fingerprint": index_metadata["content_fingerprint"],
            "governance_fingerprint": index_metadata["governance_fingerprint"],
            "index_version": index_metadata["index_version"],
        },
        "review_sha256": sha256_file(review_path) if review_path and review_path.is_file() else None,
        "receipt_sha256s": dict(sorted(receipt_sha256s.items())),
    }
    return state, details, audit, ready


def load_contract(root: Path):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from governance.contracts.knowledge import Contract

    return Contract(root)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="retrieval_state",
        allow_abbrev=False,
        description=__doc__,
        epilog="Global root option accepted anywhere: --knowledge-root PATH.",
    )
    result.add_argument("--knowledge-root", help=argparse.SUPPRESS)
    result.add_argument("state")
    result.add_argument("--review")
    result.add_argument("--receipt")
    result.add_argument("--require-ready", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        cleaned, explicit = extract_knowledge_root(sys.argv[1:] if argv is None else argv)
        args = parser().parse_args(cleaned)
        root = resolve_root(explicit, __file__)
        state_path = Path(args.state).expanduser().resolve()
        review_path = Path(args.review).expanduser().resolve() if args.review else None
        _, details, audit, ready = validate_state(root, state_path, review_path)
        if args.require_ready and not ready and not audit.errors:
            audit.error("state.not_ready", "state.decisions", "all decisions must be covered")
        if args.receipt:
            if not ready or audit.errors:
                audit.error("receipt.not_ready", "--receipt", "ready receipt requires a ready state")
            else:
                atomic_create_json(
                    Path(args.receipt),
                    {
                        "schema_version": READY_SCHEMA,
                        "state": str(state_path),
                        **details,
                    },
                )
        payload = {
            "ok": not audit.errors,
            "ready": ready and not audit.errors,
            "errors": audit.errors,
            "warnings": audit.warnings,
            **details,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not audit.errors else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"error": {"type": exc.__class__.__name__, "message": str(exc)}},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
