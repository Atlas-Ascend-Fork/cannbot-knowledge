#!/usr/bin/env python3
"""Deterministic governance checks for cannbot-knowledge."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml


def resolve_root(value: str | None) -> Path:
    if value:
        root = Path(value).resolve()
    elif os.environ.get("CANNBOT_KNOWLEDGE_ROOT"):
        root = Path(os.environ["CANNBOT_KNOWLEDGE_ROOT"]).resolve()
    else:
        root = Path(__file__).resolve().parents[4]
    required = (
        root / "knowledge",
        root / "governance/schemas/registries.yaml",
        root / "governance/contracts/knowledge.py",
    )
    if not required[0].is_dir() or not all(path.is_file() for path in required[1:]):
        raise ValueError(f"not a cannbot-knowledge root: {root}")
    return root


def load_contract(root: Path):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from governance.contracts.knowledge import (
        Contract,
        compare_trees,
        relative_markdown_links,
        split_frontmatter,
    )

    return Contract(root), compare_trees, relative_markdown_links, split_frontmatter


CONFLICT_RE = re.compile(r"(?m)^(?:<{7}|={7}|>{7})(?: .*)?$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|FIXME)\b", re.IGNORECASE)
TREE_RE = re.compile(r"/tree/([0-9a-fA-F]{40})(?:/|$)")


class Linter:
    def __init__(self, root: Path, mirror: Path | None, strict_navigation: bool):
        self.root = root
        self.mirror = mirror
        self.strict_navigation = strict_navigation
        self.errors: list[dict[str, str]] = []
        self.checked = 0
        self.contract, self.compare_trees, self.relative_links, self.split_frontmatter = load_contract(root)

    def error(self, path: Path | str, code: str, message: str) -> None:
        if isinstance(path, Path):
            try:
                display = path.relative_to(self.root).as_posix()
            except ValueError:
                display = str(path)
        else:
            display = path
        self.errors.append({"path": display, "code": code, "message": message})

    def validate_markdown(self, path: Path) -> None:
        self.checked += 1
        relative = path.relative_to(self.root)
        try:
            metadata, body = self.split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, yaml.YAMLError) as exc:
            self.error(path, "frontmatter.parse", str(exc))
            return

        if path.name == "index.md":
            for issue in self.contract.validate_index_frontmatter(relative, metadata):
                self.error(path, issue.code, issue.message)
            for issue in self.contract.validate_index_path(relative):
                self.error(path, issue.code, issue.message)
        elif metadata is None:
            self.error(path, "frontmatter.missing", "knowledge card requires frontmatter")
        else:
            for issue in self.contract.validate_card(relative, metadata, body):
                self.error(path, issue.code, issue.message)
            self.validate_body(path, body)
            if self.strict_navigation:
                self.validate_source_navigation(path, metadata, body)

        try:
            links = self.relative_links(path, self.root / "knowledge")
        except OSError as exc:
            self.error(path, "link.read", str(exc))
            return
        for raw, target in links:
            if not target.exists():
                self.error(path, "link.missing", f"missing relative link target: {raw}")

    def validate_body(self, path: Path, body: str) -> None:
        if CONFLICT_RE.search(body):
            self.error(path, "body.conflict_marker", "body contains a Git conflict marker")
        if IMAGE_RE.search(body):
            self.error(path, "body.embedded_image", "knowledge body must not embed images")
        if PLACEHOLDER_RE.search(body):
            self.error(path, "body.placeholder", "knowledge body contains TODO or FIXME")

    def validate_source_navigation(
        self,
        path: Path,
        metadata: dict[str, object],
        body: str,
    ) -> None:
        sources = metadata.get("sources")
        if not isinstance(sources, list):
            return
        resources = [
            str(source.get("resource", ""))
            for source in sources
            if isinstance(source, dict)
        ]
        corpus = "\n".join([*resources, body])
        for resource in resources:
            match = TREE_RE.search(resource)
            if match and f"/blob/{match.group(1)}/" not in corpus:
                self.error(
                    path,
                    "source.navigation",
                    "tree source requires a same-revision blob source or body link",
                )

    def validate_logs(self) -> None:
        log_root = self.root / "logs"
        if not log_root.is_dir():
            self.error(log_root, "log.missing", "repository requires logs/")
            return
        for path in sorted(log_root.glob("*.md")):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", path.name):
                self.error(path, "log.filename", "log filename must use YYYY-MM-DD.md")
                continue
            date = path.stem
            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines or lines[0] != f"# {date}":
                self.error(path, "log.heading", f"first line must be # {date}")
            times: list[str] = []
            for line in lines:
                if line.startswith("## "):
                    match = re.match(r"## \[(\d{2}:\d{2})\] [^|]+ \| .+", line)
                    valid_time = False
                    if match:
                        hour, minute = (int(value) for value in match.group(1).split(":"))
                        valid_time = hour < 24 and minute < 60
                    if not valid_time:
                        self.error(path, "log.entry", f"invalid log entry heading: {line}")
                    else:
                        assert match is not None
                        times.append(match.group(1))
            if not times:
                self.error(path, "log.entry", "log file requires at least one entry")
            elif times != sorted(times, reverse=True):
                self.error(path, "log.order", "log entries must be newest first")

    def validate_full_tree(self) -> None:
        for path, issue in self.contract.validate_index_tree():
            self.error(path, issue.code, issue.message)

    def validate_mirror(self) -> None:
        if self.mirror is None:
            return
        source = self.root / ".agents/skills"
        for issue in self.compare_trees(source, self.mirror):
            self.error(self.mirror, issue.code, issue.message)

    def run(self, cards: list[Path], full_tree: bool) -> None:
        for path in cards:
            self.validate_markdown(path)
        if full_tree:
            self.validate_full_tree()
            self.validate_logs()
        self.validate_mirror()


def build_parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    result.add_argument("--card", action="append", default=[])
    result.add_argument("--skill-mirror", help="path to cannbot-skills plugin skills directory")
    result.add_argument("--strict-navigation", action="store_true")
    result.add_argument("--sample", type=int)
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    try:
        args = build_parser().parse_args()
        root = resolve_root(args.knowledge_root)
        mirror = Path(args.skill_mirror).resolve() if args.skill_mirror else None
        if mirror is not None and not mirror.is_dir():
            raise ValueError(f"invalid --skill-mirror path: {mirror}")
        if args.card and args.sample is not None:
            raise ValueError("--card and --sample cannot be combined")
        if args.sample is not None and args.sample < 1:
            raise ValueError("--sample must be greater than zero")
        if args.card:
            cards = [(root / value).resolve() for value in args.card]
            for card in cards:
                if not card.is_file() or root / "knowledge" not in card.parents:
                    raise ValueError(f"invalid --card path: {card}")
            full_tree = False
        elif args.sample is not None:
            all_cards = sorted(
                path
                for path in (root / "knowledge").rglob("*.md")
                if path.name != "index.md"
            )
            cards = sorted(
                all_cards,
                key=lambda path: hashlib.sha256(
                    path.relative_to(root).as_posix().encode()
                ).hexdigest(),
            )[: args.sample]
            full_tree = False
        else:
            cards = sorted((root / "knowledge").rglob("*.md"))
            full_tree = True
        linter = Linter(root, mirror, args.strict_navigation)
        linter.run(cards, full_tree)
        result = {"root": str(root), "checked": linter.checked, "errors": linter.errors}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for error in linter.errors:
                print(f"ERROR {error['code']} {error['path']}: {error['message']}")
            print(f"checked={linter.checked} errors={len(linter.errors)}")
        return 1 if linter.errors else 0
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
