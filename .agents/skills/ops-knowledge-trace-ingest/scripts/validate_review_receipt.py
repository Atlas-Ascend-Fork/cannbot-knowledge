#!/usr/bin/env python3
"""Bind a curated-card review to the exact ledger and staged card bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA_VERSION = "trace.curated-review.v1"
SEVERITIES = {"blocker", "major", "minor"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_subject(ledger_path: Path, cards_root: Path) -> dict:
    ledger_path = ledger_path.resolve()
    cards_root = cards_root.resolve()
    if not ledger_path.is_file():
        raise ValueError("ledger is not a file: %s" % ledger_path)
    cards = [
        {
            "path": path.relative_to(cards_root).as_posix(),
            "sha256": _sha256(path),
        }
        for path in sorted(cards_root.rglob("*.md"))
        if path.is_file()
    ]
    if not cards:
        raise ValueError("no staged cards found under: %s" % cards_root)
    bound = {"ledger_sha256": _sha256(ledger_path), "cards": cards}
    return {
        "schema_version": SCHEMA_VERSION,
        "subject_sha256": hashlib.sha256(_canonical(bound)).hexdigest(),
        **bound,
    }


def validate_receipt(ledger_path: Path, cards_root: Path, receipt_path: Path) -> dict:
    errors = []
    subject = build_subject(ledger_path, cards_root)
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
