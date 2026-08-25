#!/usr/bin/env python3
"""Create knowledge cards and rebuild deterministic ingest-side artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml


DIRECT_ENTRY_RE = re.compile(r"^- \[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)(?:：.*)?$")
REFERENCE_ENTRY_RE = re.compile(r"^- \[([^]]+)\]\[([^]]*)\](?:：.*)?$")
REFERENCE_DEFINITION_LINE_RE = re.compile(r"^[ \t]{0,3}\[[^]\n]+\]:")
WEAK_SUMMARY_RE = re.compile(
    r"^(?:本文件为文档发布时所需的索引文件。|> \[![^]]+]|表\s*\d+|以下内容针对如下型号生效)"
)


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


def contract_module():
    """Load this Skill's Contract without executing Python from a target root."""
    module_name = "_cannbot_knowledge_ingest_contract"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    source = Path(__file__).resolve().parents[4] / "governance/contracts/knowledge.py"
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load governance contract: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_contract(root: Path):
    source = Path(__file__).resolve().parents[4] / "governance/contracts/knowledge.py"
    target = root / "governance/contracts/knowledge.py"
    if not target.is_file():
        raise ValueError(f"not a governed cannbot-knowledge root: {root}")
    if source.resolve() != target.resolve() and source.read_bytes() != target.read_bytes():
        raise ValueError(
            "target governance contract does not match this knowledge-ingest version"
        )
    return contract_module().Contract(root)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
            raise FileExistsError(f"refusing to overwrite existing card: {path}") from exc
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

    issues = contract.validate_card(relative, metadata, body, check_replacement=True)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(details)

    rendered = "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n\n" + body + "\n"
    if args.dry_run:
        sys.stdout.write(rendered)
        return 0

    atomic_create(target, rendered)
    print(target)
    return 0


def read_card_description(card_path: Path) -> tuple[str, str]:
    """Return the governed title and complete description of one card."""
    metadata, _ = contract_module().split_frontmatter(
        card_path.read_text(encoding="utf-8")
    )
    if metadata is None:
        raise ValueError(f"knowledge card is missing frontmatter: {card_path}")
    title = str(metadata.get("title", "")).strip()
    description = " ".join(str(metadata.get("description", "")).split())
    if not title or not description:
        raise ValueError(f"knowledge card requires title and description: {card_path}")
    return title, description


def summarize_subdir(directory: Path) -> str:
    """Use a direct card, then a descendant card, as a section summary."""
    direct_cards = sorted(
        path for path in directory.glob("*.md") if path.name != "index.md"
    )
    candidates = direct_cards or sorted(
        path for path in directory.rglob("*.md") if path.name != "index.md"
    )
    if candidates:
        return read_card_description(candidates[0])[1]
    return f"{directory.name.replace('_', ' ')} 导航。"


def section_title(directory: Path) -> str:
    summary_card = directory / f"{directory.name}.md"
    if summary_card.is_file():
        return read_card_description(summary_card)[0]
    return directory.name.replace("_", " ")


def desired_entries(directory: Path) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for item in sorted(directory.iterdir()):
        if item.name == "index.md":
            continue
        if item.is_dir() and (
            (item / "index.md").is_file()
            or any(path.suffix == ".md" for path in item.rglob("*.md"))
        ):
            target = f"{item.name}/index.md"
            result.append(
                (target, f"- [{section_title(item)}]({target})：{summarize_subdir(item)}")
            )
        elif item.is_file() and item.suffix == ".md":
            title, description = read_card_description(item)
            result.append((item.name, f"- [{title}]({item.name})：{description}"))
    return result


def direct_entry_target(line: str, reference_definitions: str = "") -> str | None:
    match = DIRECT_ENTRY_RE.fullmatch(line)
    target = match.group(1) if match is not None else None
    if target is None and REFERENCE_ENTRY_RE.fullmatch(line):
        targets = contract_module().markdown_targets(line + "\n" + reference_definitions)
        if len(targets) == 1 and not targets[0][1]:
            target = targets[0][0].split("#", 1)[0]
    if target is None:
        return None
    path = Path(target)
    if (
        len(path.parts) == 1
        and path.suffix == ".md"
        or len(path.parts) == 2
        and path.parts[1] == "index.md"
    ):
        return target
    return None


def refreshed_entry(existing: str, generated: str) -> str:
    if "：" not in existing or "：" not in generated:
        return existing
    summary = existing.split("：", 1)[1].strip()
    if not WEAK_SUMMARY_RE.match(summary) and "> [!" not in summary:
        return existing
    return existing.split("：", 1)[0] + "：" + generated.split("：", 1)[1]


def initial_index(directory: Path, knowledge_root: Path) -> str:
    relative = directory.relative_to(knowledge_root)
    if directory == knowledge_root:
        return '---\nokf_version: "0.2"\n---\n\n# 知识正文\n\nDomain 入口保持完整。\n'
    if relative.parts == ("ops",):
        return (
            "# 算子知识\n\n"
            "按 DSL 隔离语言、API、编译器和实现约束；只有真正不依赖单一 DSL 的结论进入 shared。\n"
        )
    if relative.parts == ("ops", "ascendc"):
        return "# Ascend C 算子知识\n\nAscend C 的 API 参考、开发指南、算子实践和调试调优。\n"
    if relative.parts == ("ops", "ascendc", "apis"):
        return "# Ascend C API\n"
    if relative.parts == ("ops", "ascendc", "guides"):
        return "# Ascend C 开发指南\n"
    return f"# {section_title(directory)}\n"


def synchronized_index(directory: Path, knowledge_root: Path) -> str:
    index = directory / "index.md"
    existing = (
        index.read_text(encoding="utf-8")
        if index.is_file() and index.read_text(encoding="utf-8").strip()
        else initial_index(directory, knowledge_root)
    )
    entries = desired_entries(directory)
    desired = dict(entries)
    lines = existing.rstrip().splitlines()
    reference_definitions = "\n".join(
        line for line in lines if REFERENCE_DEFINITION_LINE_RE.match(line)
    )
    preserved: list[str] = []
    seen: set[str] = set()
    first_navigation: int | None = None
    after_navigation: int | None = None
    for line in lines:
        target = direct_entry_target(line, reference_definitions)
        if target is None:
            preserved.append(line)
            continue
        if first_navigation is None:
            first_navigation = len(preserved)
        if target in desired and target not in seen:
            preserved.append(refreshed_entry(line, desired[target]))
            seen.add(target)
            after_navigation = len(preserved)

    missing = [line for target, line in entries if target not in seen]
    if missing:
        insert_at = after_navigation
        if insert_at is None:
            insert_at = first_navigation if first_navigation is not None else len(preserved)
        if insert_at and preserved[insert_at - 1].strip():
            missing.insert(0, "")
        if insert_at < len(preserved) and preserved[insert_at].strip():
            missing.append("")
        preserved[insert_at:insert_at] = missing
    return "\n".join(preserved).rstrip() + "\n"


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
    knowledge_root = (root / "knowledge").resolve()
    directories = [
        knowledge_root,
        *sorted(path for path in knowledge_root.rglob("*") if path.is_dir()),
    ]
    stale: list[tuple[Path, str]] = []
    for directory in directories:
        expected = synchronized_index(directory, knowledge_root)
        index = directory / "index.md"
        actual = index.read_text(encoding="utf-8") if index.is_file() else None
        if actual != expected:
            stale.append((index, expected))

    if args.check:
        for index, _ in stale:
            print(f"stale index: {index.relative_to(root)}")
        print(f"Checked {len(directories)} indexes, stale {len(stale)}")
        return 1 if stale else 0

    for index, content in stale:
        atomic_write(index, content)
    print(f"Synchronized {len(stale)} indexes, unchanged {len(directories) - len(stale)}")
    return 0


def doc_id(root: Path, path: Path) -> str:
    return path.relative_to(root / "knowledge").with_suffix("").as_posix()


def graph_data(root: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    contract = load_contract(root)
    module = contract_module()
    knowledge_root = (root / "knowledge").resolve()
    nodes: list[dict[str, object]] = []
    edge_keys: set[tuple[str, str]] = set()
    for path in sorted(knowledge_root.rglob("*.md")):
        if path.name == "index.md":
            continue
        metadata, body = module.split_frontmatter(path.read_text(encoding="utf-8"))
        if metadata is None:
            raise ValueError(f"missing frontmatter: {path}")
        issues = contract.validate_card(path.relative_to(root), metadata, body)
        if issues:
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"invalid card {path}: {details}")
        source_id = doc_id(root, path)
        nodes.append(
            {
                "id": source_id,
                "type": metadata.get("type"),
                "profile": contract.derive_card_path(path.relative_to(root)).card_type,
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
            if target.is_file() and target.suffix == ".md" and target.name != "index.md":
                edge_keys.add((source_id, doc_id(root, target)))
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
        "generated_from": "explicit relative Markdown links under knowledge/",
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
