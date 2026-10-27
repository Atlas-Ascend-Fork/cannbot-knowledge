#!/usr/bin/env python3
"""Deterministic governance checks for cannbot-knowledge."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

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
    source_root = Path(__file__).resolve().parents[4]
    source_contracts = source_root / "governance/contracts"
    target_contracts = root / "governance/contracts"
    if source_contracts.resolve() != target_contracts.resolve():
        for source in sorted(source_contracts.rglob("*.py")):
            relative = source.relative_to(source_contracts)
            target = target_contracts / relative
            if not target.is_file() or source.read_bytes() != target.read_bytes():
                raise ValueError(
                    "target governance contract does not match this knowledge-lint version"
                )

    package_name = "_cannbot_knowledge_lint_contracts"
    package = sys.modules.get(package_name)
    package_file = source_contracts / "__init__.py"
    if package is None:
        spec = importlib.util.spec_from_file_location(
            package_name,
            package_file,
            submodule_search_locations=[str(source_contracts)],
        )
        if spec is None or spec.loader is None:
            raise ValueError(f"cannot load governance contract: {source_contracts}")
        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package
        spec.loader.exec_module(package)
    elif Path(package.__file__).resolve() != package_file.resolve():
        raise ValueError("governance contract source changed in the current process")

    knowledge = importlib.import_module(f"{package_name}.knowledge")
    checks = importlib.import_module(f"{package_name}.checks")
    return (
        knowledge.Contract(root),
        checks.Document,
        checks.RunContext,
        knowledge.split_frontmatter,
        checks.CHECKS,
    )


class Linter:
    def __init__(self, root: Path, strict_navigation: bool):
        self.root = root
        self.findings: list[dict[str, Any]] = []
        self._seen: set[
            tuple[str, str, str, str, int | None, str, str | None]
        ] = set()
        self.checked = 0
        (
            self.contract,
            self.Document,
            RunContext,
            self.split_frontmatter,
            self.checks,
        ) = load_contract(root)
        self.context = RunContext(strict_navigation=strict_navigation)

    def record(self, check, path: Path | str, issue) -> None:
        location = issue.path or path
        if isinstance(location, Path):
            try:
                display = location.relative_to(self.root).as_posix()
            except ValueError:
                display = str(location)
        else:
            display = location
        key = (
            check.id,
            check.tier,
            issue.code,
            display,
            issue.line,
            issue.message,
            issue.details,
        )
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append(
            {
                "check": check.id,
                "tier": check.tier,
                "path": display,
                "line": issue.line,
                "code": issue.code,
                "message": issue.message,
                "details": issue.details,
            }
        )

    def has_p0(self) -> bool:
        return any(finding["tier"] == "P0" for finding in self.findings)

    def validate_markdown(self, path: Path) -> None:
        self.checked += 1
        relative = path.relative_to(self.root)
        text = ""
        metadata = None
        body = ""
        parse_error = None
        try:
            text = path.read_text(encoding="utf-8")
            metadata, body = self.split_frontmatter(text)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            parse_error = str(exc)

        document = self.Document.create(
            self.contract,
            path,
            relative,
            text,
            metadata,
            body,
            parse_error,
        )
        for check in self.checks:
            if check.document is None:
                continue
            for issue in check.document(self.contract, document, self.context):
                self.record(check, path, issue)

    def validate_full_tree(self) -> None:
        for check in self.checks:
            if (
                check.repository is None
                or check.id in {"logs", "log_order"}
                or check.requires_clean
            ):
                continue
            for path, issue in check.repository(self.contract):
                self.record(check, path, issue)

    def validate_logs(self) -> None:
        for check in self.checks:
            if check.id not in {"logs", "log_order"} or check.repository is None:
                continue
            for path, issue in check.repository(self.contract):
                self.record(check, path, issue)

    def validate_deferred_repository_checks(self) -> None:
        for check in self.checks:
            if (
                not check.requires_clean
                or check.repository is None
                or self.has_p0()
            ):
                continue
            for path, issue in check.repository(self.contract):
                self.record(check, path, issue)

    def run(self, cards: list[Path], full_tree: bool) -> None:
        for path in cards:
            self.validate_markdown(path)
        if full_tree:
            self.validate_full_tree()
            self.validate_logs()
            self.validate_deferred_repository_checks()


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
        linter = Linter(root, args.strict_navigation)
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
        linter.run(cards, full_tree)
        result = {
            "root": str(root),
            "checked": linter.checked,
            "findings": linter.findings,
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for finding in linter.findings:
                location = finding["path"]
                if finding["line"] is not None:
                    location = f"{location}:{finding['line']}"
                details = (
                    f" — {finding['details']}"
                    if finding["details"] is not None
                    else ""
                )
                print(
                    f"{finding['tier']} {finding['check']}/{finding['code']} "
                    f"{location}: {finding['message']}{details}"
                )
            counts = {
                tier: sum(finding["tier"] == tier for finding in linter.findings)
                for tier in ("P0", "P1", "P2")
            }
            print(
                f"checked={linter.checked} "
                f"P0={counts['P0']} P1={counts['P1']} P2={counts['P2']}"
            )
        return 1 if linter.has_p0() else 0
    except (
        ImportError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
