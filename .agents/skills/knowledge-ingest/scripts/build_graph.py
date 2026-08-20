#!/usr/bin/env python3
"""Rebuild an ignored local graph from explicit links between knowledge cards."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


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
    from governance.contracts.knowledge import Contract, split_frontmatter

    return Contract(root), split_frontmatter


def doc_id(root: Path, path: Path) -> str:
    return path.relative_to(root / "knowledge").with_suffix("").as_posix()


def linked_cards(root: Path, source: Path, body: str) -> set[Path]:
    knowledge_root = (root / "knowledge").resolve()
    targets: set[Path] = set()
    for raw in LINK_RE.findall(body):
        target_text = raw.split()[0].strip("<>")
        if not target_text or target_text.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = unquote(target_text.split("#", 1)[0])
        if not clean:
            continue
        if clean.startswith("/"):
            target = (knowledge_root / clean.lstrip("/")).resolve()
        else:
            target = (source.parent / clean).resolve()
        try:
            target.relative_to(knowledge_root)
        except ValueError:
            continue
        if target.is_file() and target.suffix == ".md" and target.name != "index.md":
            targets.add(target)
    return targets


def build(root: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    contract, split_frontmatter = load_contract(root)
    nodes: list[dict[str, object]] = []
    edge_keys: set[tuple[str, str]] = set()
    for path in sorted((root / "knowledge").rglob("*.md")):
        if path.name == "index.md":
            continue
        metadata, body = split_frontmatter(path.read_text(encoding="utf-8"))
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
        for target in linked_cards(root, path, body):
            edge_keys.add((source_id, doc_id(root, target)))
    edges = [
        {"source": source, "relation": "links_to", "target": target}
        for source, target in sorted(edge_keys)
    ]
    return nodes, edges


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    args = parser.parse_args()
    try:
        root = resolve_root(args.knowledge_root)
        nodes, edges = build(root)
        output = root / "artifacts/graphs/graph.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "generated_from": "explicit relative Markdown links under knowledge/",
            "nodes": nodes,
            "edges": edges,
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"output={output} nodes={len(nodes)} edges={len(edges)}")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
