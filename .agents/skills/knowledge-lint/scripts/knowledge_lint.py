#!/usr/bin/env python3
"""Deterministic governance checks for cannbot-knowledge."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jsonschema.exceptions import SchemaError


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
    source_contract = (
        Path(__file__).resolve().parents[4] / "governance/contracts/knowledge.py"
    )
    target_contract = root / "governance/contracts/knowledge.py"
    if source_contract.resolve() != target_contract.resolve():
        if source_contract.read_bytes() != target_contract.read_bytes():
            raise ValueError(
                "target governance contract does not match this knowledge-lint version"
            )
    module_name = "_cannbot_knowledge_lint_contract"
    spec = importlib.util.spec_from_file_location(module_name, source_contract)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load governance contract: {source_contract}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return (
        module.Contract(root),
        module.relative_markdown_links,
        module.split_frontmatter,
        module.markdown_targets,
    )


CONFLICT_RE = re.compile(r"(?m)^(?:<{7}|={7}|>{7})(?: .*)?$")
IMAGE_RE = re.compile(
    r"!\[[^\]\n]*\](?:\([^\n)]+\)|\[[^\]\n]*\])|<img\b[^>]*>",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|FIXME)\b", re.IGNORECASE)
TRUNCATED_TEXT_RE = re.compile(
    r"(?m)(?:\S\.\.\.[ \t]*$|[\w\u3400-\u9fff）】]\.\.\.(?=\s*[；，。]))"
)
WEAK_DESCRIPTION_RE = re.compile(
    r"^(?:本文件为文档发布时所需的索引文件。|> \[![^]]+]|表\s*\d+|以下内容针对如下型号生效)"
)


def git_view_location(value: str, marker: str) -> tuple[str, str, str] | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if marker not in parts:
        return None
    index = parts.index(marker)
    if index + 1 >= len(parts):
        return None
    repository = parts[:index]
    if repository and repository[-1] == "-":
        repository = repository[:-1]
    revision = parts[index + 1]
    if len(repository) < 2 or not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        return None
    return parsed.hostname.lower(), "/".join(repository), revision.lower()


class Linter:
    def __init__(self, root: Path, strict_navigation: bool):
        self.root = root
        self.strict_navigation = strict_navigation
        self.errors: list[dict[str, str]] = []
        self.checked = 0
        (
            self.contract,
            self.relative_links,
            self.split_frontmatter,
            self.markdown_targets,
        ) = load_contract(root)
        self.checked_local_roots: set[str] = set()

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
            self.validate_body(path, metadata, body)
            self.validate_local_sources(path, metadata)
            if self.strict_navigation:
                self.validate_source_navigation(path, metadata, body)

        try:
            links = self.relative_links(path, self.root / "knowledge")
        except OSError as exc:
            self.error(path, "link.read", str(exc))
            return
        knowledge_root = (self.root / "knowledge").resolve()
        for raw, target in links:
            try:
                target.relative_to(knowledge_root)
            except ValueError:
                self.error(path, "link.outside_bundle", f"local link leaves knowledge/: {raw}")
                continue
            if not target.exists():
                self.error(path, "link.missing", f"missing relative link target: {raw}")
            elif not target.is_file():
                self.error(path, "link.not_file", f"relative link target is not a file: {raw}")

    def validate_body(self, path: Path, metadata: dict[str, object], body: str) -> None:
        if CONFLICT_RE.search(body):
            self.error(path, "body.conflict_marker", "body contains a Git conflict marker")
        if IMAGE_RE.search(body):
            self.error(path, "body.embedded_image", "knowledge body must not embed images")
        if PLACEHOLDER_RE.search(body):
            self.error(path, "body.placeholder", "knowledge body contains TODO or FIXME")
        if TRUNCATED_TEXT_RE.search(body):
            self.error(
                path,
                "body.truncated",
                "knowledge body contains probable truncation dots",
            )
        description = metadata.get("description")
        if isinstance(description, str) and description.rstrip().endswith("..."):
            self.error(
                path,
                "frontmatter.truncated",
                "description ends in truncation dots",
            )
        if isinstance(description, str) and WEAK_DESCRIPTION_RE.match(description.strip()):
            self.error(
                path,
                "frontmatter.description_placeholder",
                "description is publishing markup or a table label, not a standalone summary",
            )

    def validate_local_sources(self, path: Path, metadata: dict[str, object]) -> None:
        sources = metadata.get("sources")
        if not isinstance(sources, list):
            return
        definitions = {
            str(definition.get("root")): definition
            for definition in self.contract.local_sources.values()
            if isinstance(definition, dict)
        }
        for source in sources:
            if not isinstance(source, dict):
                continue
            resource = source.get("resource")
            if not isinstance(resource, str) or resource.startswith(("http://", "https://")):
                continue
            relative = Path(resource)
            if relative.is_absolute() or not relative.parts or ".." in relative.parts:
                continue
            definition = definitions.get(relative.parts[0])
            if not isinstance(definition, dict):
                continue
            source_root = self.root / relative.parts[0]
            if not source_root.exists():
                continue
            if relative.parts[0] not in self.checked_local_roots:
                self.checked_local_roots.add(relative.parts[0])
                marker = source_root / ".complete"
                expected = f"archive_sha256={definition.get('archive_sha256', '')}"
                if not source_root.is_dir() or not marker.is_file():
                    self.error(marker, "source.archive_marker", "restored source requires .complete")
                elif expected not in marker.read_text(encoding="utf-8").splitlines():
                    self.error(
                        marker,
                        "source.archive_marker",
                        "restored source archive SHA-256 does not match Registry",
                    )
            if not (self.root / relative).is_file():
                self.error(path, "source.local_missing", f"local source file does not exist: {resource}")

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
        body_links = [target for target, _ in self.markdown_targets(body)]
        candidates = [*resources, *body_links]
        for resource in resources:
            tree = git_view_location(resource, "tree")
            if tree and not any(
                git_view_location(candidate, "blob") == tree for candidate in candidates
            ):
                self.error(
                    path,
                    "source.navigation",
                    "tree source requires a same-repository, same-revision blob source or body link",
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
            entries = [index for index, line in enumerate(lines) if line.startswith("## ")]
            for position, index in enumerate(entries):
                line = lines[index]
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
                end = entries[position + 1] if position + 1 < len(entries) else len(lines)
                section_headings = [item for item in lines[index + 1 : end] if item.startswith("### ")]
                if (
                    section_headings.count("### Summary") != 1
                    or section_headings.count("### Details") != 1
                    or section_headings.index("### Summary") > section_headings.index("### Details")
                ):
                    self.error(
                        path,
                        "log.sections",
                        "each log entry requires Summary then Details",
                    )
            if not times:
                self.error(path, "log.entry", "log file requires at least one entry")
            elif times != sorted(times, reverse=True):
                self.error(path, "log.order", "log entries must be newest first")

    def validate_full_tree(self) -> None:
        for path, issue in self.contract.validate_index_tree():
            self.error(path, issue.code, issue.message)
        for path, issue in self.contract.validate_repository_infrastructure():
            self.error(path, issue.code, issue.message)

    def run(self, cards: list[Path], full_tree: bool) -> None:
        for path in cards:
            self.validate_markdown(path)
        if full_tree:
            self.validate_full_tree()
            self.validate_logs()


def build_parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    result.add_argument("--card", action="append", default=[])
    result.add_argument("--strict-navigation", action="store_true")
    result.add_argument("--sample", type=int)
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    try:
        args = build_parser().parse_args()
        root = resolve_root(args.knowledge_root)
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
        linter = Linter(root, args.strict_navigation)
        linter.run(cards, full_tree)
        result = {"root": str(root), "checked": linter.checked, "errors": linter.errors}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for error in linter.errors:
                print(f"ERROR {error['code']} {error['path']}: {error['message']}")
            print(f"checked={linter.checked} errors={len(linter.errors)}")
        return 1 if linter.errors else 0
    except (ImportError, OSError, SchemaError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
