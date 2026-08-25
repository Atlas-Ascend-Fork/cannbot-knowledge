#!/usr/bin/env python3
"""Create knowledge cards and rebuild deterministic ingest-side artifacts."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
import tempfile
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
    if not (root / "knowledge").is_dir():
        raise ValueError(f"not a cannbot-knowledge root: {root}")
    return root


def contract_package():
    """Load this Skill's trusted Contract package."""
    module_name = "_cannbot_knowledge_ingest_contracts"
    loaded = sys.modules.get(module_name)
    source = Path(__file__).resolve().parents[4] / "governance/contracts"
    package_file = source / "__init__.py"
    if loaded is not None:
        if Path(loaded.__file__).resolve() != package_file.resolve():
            raise ValueError(
                "governance contract source changed in the current process"
            )
        return loaded
    spec = importlib.util.spec_from_file_location(
        module_name,
        package_file,
        submodule_search_locations=[str(source)],
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load governance contract: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def contract_module():
    package = contract_package()
    return importlib.import_module(f"{package.__name__}.knowledge")


def indexes_module():
    package = contract_package()
    return importlib.import_module(f"{package.__name__}.indexes")


def load_contract(root: Path):
    source = Path(__file__).resolve().parents[4] / "governance/contracts"
    target = root / "governance/contracts"
    if not (target / "knowledge.py").is_file():
        raise ValueError(f"not a governed cannbot-knowledge root: {root}")
    if source.resolve() != target.resolve():
        for source_file in sorted(source.rglob("*.py")):
            target_file = target / source_file.relative_to(source)
            if (
                not target_file.is_file()
                or source_file.read_bytes() != target_file.read_bytes()
            ):
                raise ValueError(
                    "target governance contract does not match this knowledge-ingest version"
                )
    return contract_module().Contract(root)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def source_objects(urls: list[str]) -> list[dict[str, str]]:
    return [
        {"resource": url, **({"role": "primary"} if index == 0 else {})}
        for index, url in enumerate(urls)
    ]


def atomic_create(path: Path, content: str) -> None:
    """Atomically create a UTF-8 file without replacing an existing entry."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_value = tempfile.mkstemp(
        prefix=f"{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_value)
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise FileExistsError(
                f"refusing to overwrite existing card: {path}"
            ) from exc
    finally:
        temporary.unlink(missing_ok=True)


def create(args: argparse.Namespace) -> int:
    root = resolve_root(args.knowledge_root)
    contract = load_contract(root)
    relative = Path(args.path)
    path_info = contract.derive_card_path(relative)
    card_type = path_info.card_type
    target = (root / relative).resolve()
    if (root / "knowledge").resolve() not in target.parents:
        raise ValueError("target escapes knowledge root")

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

    issues = contract.validate_card(relative, metadata, body)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(details)

    rendered = (
        "---\n"
        + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
        + "\n---\n\n"
        + body
        + "\n"
    )
    if args.dry_run:
        sys.stdout.write(rendered)
        return 0

    atomic_create(target, rendered)
    print(target)
    return 0


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_value = tempfile.mkstemp(
        prefix=f"{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_value)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def sync_indexes(args: argparse.Namespace) -> int:
    root = resolve_root(args.knowledge_root)
    total, stale = indexes_module().index_updates(root)

    if args.check:
        for update in stale:
            print(f"stale index: {update.path.relative_to(root)}")
        print(f"Checked {total} indexes, stale {len(stale)}")
        return 1 if stale else 0

    for update in stale:
        atomic_write(update.path, update.content)
    print(f"Synchronized {len(stale)} indexes, unchanged {total - len(stale)}")
    return 0


def doc_id(root: Path, path: Path) -> str:
    return path.relative_to(root / "knowledge").with_suffix("").as_posix()


def graph_data(root: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    contract = load_contract(root)
    module = contract_module()
    knowledge_root = contract.root / "knowledge"
    nodes: list[dict[str, object]] = []
    edge_keys: set[tuple[str, str]] = set()
    for path in sorted(knowledge_root.rglob("*.md")):
        if path.name == "index.md":
            continue
        metadata, body = module.split_frontmatter(path.read_text(encoding="utf-8"))
        if metadata is None:
            raise ValueError(f"missing frontmatter: {path}")
        issues = contract.validate_card(path.relative_to(contract.root), metadata, body)
        if issues:
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"invalid card {path}: {details}")
        source_id = doc_id(contract.root, path)
        nodes.append(
            {
                "id": source_id,
                "type": metadata.get("type"),
                "profile": contract.derive_card_path(
                    path.relative_to(contract.root)
                ).card_type,
                "title": metadata.get("title"),
                "status": metadata.get("status"),
                "tags": metadata.get("tags", []),
            }
        )
        for _, target in module.relative_markdown_links(path, knowledge_root):
            try:
                target.relative_to(knowledge_root)
            except ValueError:
                continue
            if (
                target.is_file()
                and target.suffix == ".md"
                and target.name != "index.md"
            ):
                edge_keys.add((source_id, doc_id(contract.root, target)))
    edges = [
        {"source": source, "relation": "links_to", "target": target}
        for source, target in sorted(edge_keys)
    ]
    return nodes, edges


def build_graph(args: argparse.Namespace) -> int:
    root = resolve_root(args.knowledge_root)
    nodes, edges = graph_data(root)
    output = root / "artifacts/graphs/graph.json"
    payload = {
        "schema_version": 1,
        "nodes": nodes,
        "edges": edges,
    }
    atomic_write(output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"output={output} nodes={len(nodes)} edges={len(edges)}")
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
    command.add_argument(
        "--status", choices=["draft", "stable", "deprecated"], default="draft"
    )
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
    indexes = sub.add_parser(
        "sync-indexes",
        help="synchronize complete direct-child index navigation",
    )
    indexes.add_argument(
        "--check",
        action="store_true",
        help="report stale indexes without writing them",
    )
    indexes.set_defaults(handler=sync_indexes)
    graph = sub.add_parser(
        "build-graph",
        help="rebuild the ignored graph from explicit knowledge links",
    )
    graph.set_defaults(handler=build_graph)
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
