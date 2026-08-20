#!/usr/bin/env python3
"""Create a governed draft knowledge card without overwriting existing content."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def resolve_root(value: str | None) -> Path:
    if value:
        root = Path(value).resolve()
    elif os.environ.get("CANNBOT_KNOWLEDGE_ROOT"):
        root = Path(os.environ["CANNBOT_KNOWLEDGE_ROOT"]).resolve()
    else:
        root = Path(__file__).resolve().parents[4]
    if not (root / "knowledge").is_dir() or not (root / "governance/schemas/registries.yaml").is_file():
        raise ValueError(f"not a cannbot-knowledge root: {root}")
    return root


def load_contract(root: Path):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from governance.contracts.knowledge import Contract

    return Contract(root)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_objects(urls: list[str]) -> list[dict[str, str]]:
    return [
        {"resource": url, **({"role": "primary"} if index == 0 else {})}
        for index, url in enumerate(urls)
    ]


def create(args: argparse.Namespace) -> int:
    root = resolve_root(args.knowledge_root)
    contract = load_contract(root)
    relative = Path(args.path)
    path_info = contract.derive_card_path(relative)
    card_type = path_info.card_type
    target = (root / relative).resolve()
    if root not in target.parents:
        raise ValueError("target escapes knowledge root")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing card: {target}")

    body_path = Path(args.body_file).resolve()
    body = body_path.read_text(encoding="utf-8").strip()
    if not body:
        raise ValueError("--body-file must contain distilled knowledge")

    stamp = utc_now()
    metadata: dict[str, object] = {
        "type": contract.okf_type(card_type),
        "title": args.title.strip(),
        "description": args.description.strip(),
        "tags": args.tag,
        "status": args.status,
        "sources": source_objects(args.source),
        "created_at": stamp,
        "updated_at": stamp,
    }

    if card_type != "glossaries":
        metadata["platforms"] = args.platform
    if bool(args.verified_by) != bool(args.verified_at):
        raise ValueError("--verified-by and --verified-at must be provided together")
    if args.verified_by:
        metadata["verified"] = {"by": args.verified_by, "at": args.verified_at}
    if args.cann_version:
        metadata["cann_versions"] = args.cann_version
    if args.alias:
        metadata["aliases"] = args.alias
    if card_type == "interoperability":
        if not args.source_technology or not args.target_technology:
            raise ValueError("interoperability requires source and target technology")
        metadata["source_technology"] = args.source_technology
        metadata["target_technology"] = args.target_technology
    if args.replaced_by:
        metadata["replaced_by"] = args.replaced_by

    issues = contract.validate_card(relative, metadata, body, check_replacement=True)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(details)

    rendered = "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n\n" + body + "\n"
    if args.dry_run:
        sys.stdout.write(rendered)
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print(target)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    sub = result.add_subparsers(dest="command", required=True)
    command = sub.add_parser("create", help="create a new governed candidate card")
    command.add_argument("--path", required=True)
    command.add_argument("--title", required=True)
    command.add_argument("--description", required=True)
    command.add_argument("--tag", action="append", required=True)
    command.add_argument("--status", choices=["draft", "stable", "deprecated"], default="draft")
    command.add_argument("--source", action="append", default=[])
    command.add_argument("--platform", action="append", default=[])
    command.add_argument("--verified-by")
    command.add_argument("--verified-at")
    command.add_argument("--cann-version", action="append", default=[])
    command.add_argument("--alias", action="append", default=[])
    command.add_argument("--source-technology")
    command.add_argument("--target-technology")
    command.add_argument("--replaced-by")
    command.add_argument("--body-file", required=True)
    command.add_argument("--dry-run", action="store_true")
    command.set_defaults(handler=create)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        return args.handler(args)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
