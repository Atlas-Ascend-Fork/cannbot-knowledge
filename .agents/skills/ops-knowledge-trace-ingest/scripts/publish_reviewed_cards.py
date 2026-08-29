#!/usr/bin/env python3
"""Atomically publish exactly the staged Runbook bytes bound by a PASS receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

import yaml

from governance.contracts.knowledge import Contract, split_frontmatter
from validate_review_receipt import validate_receipt


ACCEPTED_STATUSES = {"published", "merged"}
MERGE_OPERATIONS = {"upvote", "merge", "downvote"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_runbook_areas(repository_root: Path) -> set[str]:
    registry = repository_root / "governance/schemas/registries.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    return set((data.get("paths") or {}).get("runbook_areas") or [])


def require_approved_audits(ledger: dict) -> None:
    for entry in ledger.get("entries") or []:
        if entry.get("status") not in ACCEPTED_STATUSES:
            continue
        label = entry.get("target_path") or entry.get("target_slug") or "<entry>"
        audit = entry.get("evidence_audit") or {}
        if audit.get("result") != "pass":
            raise ValueError(f"{label}: evidence audit is not approved")
        if audit.get("mode") == "trace_snapshot":
            artifacts = (audit.get("trace_snapshot") or {}).get(
                "mechanism_artifacts"
            ) or []
            if not artifacts or any(
                artifact.get("verbatim_verified") is not True
                for artifact in artifacts
            ):
                raise ValueError(f"{label}: trace artifacts are not approved")
        elif audit.get("mode") == "fixed_source":
            files = (audit.get("fixed_source") or {}).get("files") or []
            if not files or any(
                source_file.get("navigation_verified") is not True
                for source_file in files
            ):
                raise ValueError(f"{label}: fixed-source navigation is not approved")
        else:
            raise ValueError(f"{label}: invalid evidence mode")


def publish(
    ledger_path: Path,
    cards_root: Path,
    receipt_path: Path,
    repository_root: Path,
    check_only: bool = False,
) -> dict:
    repository_root = repository_root.resolve()
    cards_root = cards_root.resolve()
    ledger_bytes = ledger_path.read_bytes()
    frozen_cards = {
        path.relative_to(cards_root).as_posix(): path.read_bytes()
        for path in sorted(cards_root.rglob("*.md"))
        if path.is_file()
    }
    review = validate_receipt(
        ledger_path,
        cards_root,
        receipt_path,
        ledger_bytes=ledger_bytes,
        card_bytes=frozen_cards,
    )
    if not review.get("ok") or review.get("verdict") != "PASS":
        raise ValueError("staged cards lack a valid PASS receipt")
    ledger = json.loads(ledger_bytes.decode("utf-8"))
    require_approved_audits(ledger)
    contract = Contract(repository_root)
    areas = load_runbook_areas(repository_root)
    operations = {}
    for entry in ledger.get("entries") or []:
        if entry.get("status") not in ACCEPTED_STATUSES:
            continue
        target_path = entry.get("target_path")
        operation = entry.get("operation")
        if not target_path or operation not in {"new", *MERGE_OPERATIONS}:
            raise ValueError("accepted ledger entry has invalid target/operation")
        if target_path in operations:
            raise ValueError(f"duplicate ledger target: {target_path}")
        operations[str(target_path)] = str(operation)
    runbooks_root = repository_root / "knowledge/ops/ascendc/runbooks"
    plans = []
    for relative_text, staged_bytes in sorted(frozen_cards.items()):
        relative = Path(relative_text)
        if (
            len(relative.parts) != 2
            or relative.parts[0] not in areas
            or relative.name == "index.md"
        ):
            raise ValueError(f"invalid staged Runbook path: {relative.as_posix()}")
        operation = operations.get(relative_text)
        if operation is None:
            raise ValueError(f"staged path is absent from ledger: {relative_text}")
        try:
            metadata, body = split_frontmatter(staged_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, yaml.YAMLError) as error:
            raise ValueError(
                f"invalid staged Runbook frontmatter: {relative_text}: {error}"
            ) from error
        if metadata is None:
            raise ValueError(f"staged Runbook lacks frontmatter: {relative_text}")
        contract_relative = Path("knowledge/ops/ascendc/runbooks") / relative
        issues = contract.validate_card(contract_relative, metadata, body)
        if issues:
            summary = "; ".join(
                f"{issue.code}: {issue.message}" for issue in issues[:5]
            )
            raise ValueError(
                f"staged Runbook violates machine contract: {relative_text}: {summary}"
            )
        destination = runbooks_root / relative
        if operation == "new" and destination.exists() and not check_only:
            raise ValueError(f"new target already exists: {destination}")
        if operation in MERGE_OPERATIONS and not destination.is_file():
            raise ValueError(f"merge target does not exist: {destination}")
        plans.append(
            (destination, hashlib.sha256(staged_bytes).hexdigest(), staged_bytes)
        )

    for destination, expected_sha, staged_bytes in plans:
        if check_only:
            if not destination.is_file() or sha256_file(destination) != expected_sha:
                raise ValueError(f"published bytes differ from staged card: {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(staged_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()
        if sha256_file(destination) != expected_sha:
            raise ValueError(f"published SHA-256 mismatch: {destination}")

    return {
        "mode": "check" if check_only else "publish",
        "cards": len(plans),
        "targets": [
            {
                "path": destination.relative_to(repository_root).as_posix(),
                "sha256": expected_sha,
            }
            for destination, expected_sha, _ in plans
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("cards_root", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--knowledge-root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        result = publish(
            arguments.ledger,
            arguments.cards_root,
            arguments.receipt,
            arguments.knowledge_root,
            check_only=arguments.check,
        )
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"ERROR: {error}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
