#!/usr/bin/env python3
"""Bind a curated-card review to the semantic ledger and staged card bytes.

Reviewer-owned approval flags are normalized before hashing so a PASS receipt can
authorize their deterministic pending -> approved transition without becoming
stale. All curator-owned decisions and every staged card byte remain bound.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path


SCHEMA_VERSION = "trace.curated-review.v2"
SEVERITIES = {"blocker", "major", "minor"}
REVIEWER_RE = re.compile(r"^subagent:[A-Za-z0-9_./-]+$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _review_subject_ledger(ledger: dict) -> dict:
    """Return the ledger view reviewed by an independent reviewer.

    Only flags that the reviewer is uniquely allowed to approve are normalized.
    This keeps the subject stable when a validated PASS receipt is applied while
    ensuring every curator decision, source mapping, anchor, and artifact remains
    immutable.
    """
    normalized = json.loads(json.dumps(ledger, ensure_ascii=False))
    for entry in normalized.get("entries") or []:
        if entry.get("status") not in {"published", "merged"}:
            continue
        audit = entry.get("evidence_audit") or {}
        audit["result"] = "pending"
        snapshot = audit.get("trace_snapshot") or {}
        for artifact in snapshot.get("mechanism_artifacts") or []:
            artifact["verbatim_verified"] = False
        fixed_source = audit.get("fixed_source") or {}
        for source_file in fixed_source.get("files") or []:
            source_file["navigation_verified"] = False
    return normalized


def build_subject(
    ledger_path: Path,
    cards_root: Path,
    *,
    ledger_bytes: bytes | None = None,
    card_bytes: dict[str, bytes] | None = None,
) -> dict:
    ledger_path = ledger_path.resolve()
    cards_root = cards_root.resolve()
    if ledger_bytes is None:
        if not ledger_path.is_file():
            raise ValueError("ledger is not a file: %s" % ledger_path)
        ledger_bytes = ledger_path.read_bytes()
    if card_bytes is None:
        cards = [
            {
                "path": path.relative_to(cards_root).as_posix(),
                "sha256": _sha256(path),
            }
            for path in sorted(cards_root.rglob("*.md"))
            if path.is_file()
        ]
    else:
        cards = [
            {"path": path, "sha256": _sha256_bytes(data)}
            for path, data in sorted(card_bytes.items())
        ]
    if not cards:
        raise ValueError("no staged cards found under: %s" % cards_root)
    try:
        ledger = json.loads(ledger_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ledger is not valid JSON: %s" % error) from error
    expected_targets = {
        str(entry.get("target_path"))
        for entry in ledger.get("entries") or []
        if entry.get("status") in {"published", "merged"}
        and entry.get("target_path")
    }
    actual_targets = {card["path"] for card in cards}
    if expected_targets != actual_targets:
        raise ValueError(
            "staged card targets do not match ledger: expected=%s actual=%s"
            % (sorted(expected_targets), sorted(actual_targets))
        )
    ledger_sha256 = hashlib.sha256(
        _canonical(_review_subject_ledger(ledger))
    ).hexdigest()
    bound = {"ledger_sha256": ledger_sha256, "cards": cards}
    return {
        "schema_version": SCHEMA_VERSION,
        "subject_sha256": hashlib.sha256(_canonical(bound)).hexdigest(),
        **bound,
    }


def validate_receipt(
    ledger_path: Path,
    cards_root: Path,
    receipt_path: Path,
    *,
    ledger_bytes: bytes | None = None,
    card_bytes: dict[str, bytes] | None = None,
) -> dict:
    errors = []
    try:
        subject = build_subject(
            ledger_path,
            cards_root,
            ledger_bytes=ledger_bytes,
            card_bytes=card_bytes,
        )
    except (OSError, ValueError) as error:
        return {"ok": False, "errors": ["invalid review subject: %s" % error]}
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"ok": False, "errors": ["invalid receipt: %s" % error]}

    for key in ("schema_version", "subject_sha256", "ledger_sha256", "cards"):
        if receipt.get(key) != subject[key]:
            errors.append("receipt %s does not match current subject" % key)
    verdict = receipt.get("verdict")
    if verdict not in {"PASS", "NEEDS_REVISION"}:
        errors.append("verdict must be PASS or NEEDS_REVISION")
    findings = receipt.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append("finding[%d] must be an object" % index)
            continue
        if finding.get("severity") not in SEVERITIES:
            errors.append("finding[%d] has invalid severity" % index)
        for key in ("card", "issue", "location", "suggestion"):
            if not str(finding.get(key) or "").strip():
                errors.append("finding[%d].%s is required" % (index, key))
    unresolved = [
        finding for finding in findings
        if isinstance(finding, dict)
        and finding.get("severity") in {"blocker", "major"}
    ]
    if verdict == "PASS" and unresolved:
        errors.append("PASS receipt contains blocker or major findings")
    if verdict == "NEEDS_REVISION" and not unresolved:
        errors.append("NEEDS_REVISION requires a blocker or major finding")
    if not str(receipt.get("summary") or "").strip():
        errors.append("summary is required")
    reviewer = str(receipt.get("reviewer") or "")
    if not REVIEWER_RE.fullmatch(reviewer):
        errors.append("reviewer must be a canonical subagent identity")
    if receipt.get("attestation") != "agent-runtime-message":
        errors.append("attestation must be agent-runtime-message")
    reviewed_at = str(receipt.get("reviewed_at") or "")
    try:
        parsed_reviewed_at = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError:
        parsed_reviewed_at = None
    if (
        parsed_reviewed_at is None
        or parsed_reviewed_at.tzinfo is None
        or not reviewed_at.endswith("Z")
    ):
        errors.append("reviewed_at must be RFC 3339 UTC ending in Z")
    return {
        "ok": not errors,
        "subject_sha256": subject["subject_sha256"],
        "cards": len(subject["cards"]),
        "verdict": verdict,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    parser.add_argument("cards_root", type=Path)
    parser.add_argument("receipt", nargs="?", type=Path)
    parser.add_argument("--subject", action="store_true")
    arguments = parser.parse_args()
    if arguments.subject:
        if arguments.receipt is not None:
            parser.error("receipt is not accepted with --subject")
        print(json.dumps(build_subject(arguments.ledger, arguments.cards_root), ensure_ascii=False, indent=2))
        return 0
    if arguments.receipt is None:
        parser.error("receipt is required unless --subject is used")
    result = validate_receipt(arguments.ledger, arguments.cards_root, arguments.receipt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
