#!/usr/bin/env python3
"""Restore pinned source worktrees and localize registered Git provenance."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote, urldefrag

import yaml

import knowledge_ingest as ingest


sys.dont_write_bytecode = True
resources = importlib.import_module(f"{ingest.contract_package().__name__}.source_resources")
links = importlib.import_module(f"{ingest.contract_package().__name__}.checks.links")


def run_git(*args: str) -> None:
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
        check=True,
    )


def fetch_repository(root: Path, definition: dict) -> None:
    source_root = root / definition["root"]
    if source_root.resolve() != source_root:
        raise ValueError(f"refusing symlink source root or ancestor: {source_root}")
    cache = source_root / ".objects.git"
    if not cache.exists():
        if source_root.exists() and any(source_root.iterdir()):
            raise ValueError(f"refusing unmanaged source directory: {source_root}")
        source_root.mkdir(parents=True, exist_ok=True)
        run_git("init", "--quiet", "--bare", str(cache))
        run_git("-C", str(cache), "remote", "add", "origin", definition["repository"] + ".git")
    if cache.is_symlink() or resources.git_read(cache, "remote", "get-url", "origin").removesuffix(".git") != definition["repository"]:
        raise ValueError(f"source object store origin mismatch: {cache}")
    for revision in definition["revisions"]:
        checkout = source_root / revision
        if not checkout.exists():
            print(f"Fetching {definition['repository']} @ {revision}", flush=True)
            run_git("-C", str(cache), "fetch", "--quiet", "--depth=1", "--no-tags", "origin", revision)
            run_git("-C", str(cache), "worktree", "add", "--quiet", "--detach", str(checkout), revision)
        resources.validate_checkout(root, definition, revision)
        print(f"Verified {definition['root']}/{revision}", flush=True)


def source_frontmatter(original: str, metadata: dict) -> str:
    """Replace only source resources and updated_at, preserving YAML layout."""
    nodes = dict((key.value, value) for key, value in yaml.compose(original).value)
    replacements = []

    def replace_scalar(node, value):
        if node.value == value:
            return
        if node.style == '"':
            rendered = json.dumps(value, ensure_ascii=False)
        elif node.style == "'":
            rendered = "'" + value.replace("'", "''") + "'"
        elif node.style is None:
            rendered = value
        else:
            rendered = json.dumps(value, ensure_ascii=False)
        replacements.append((node.start_mark.index, node.end_mark.index, rendered))

    replace_scalar(nodes["updated_at"], metadata["updated_at"])
    for node, source in zip(nodes["sources"].value, metadata["sources"], strict=True):
        fields = dict((key.value, value) for key, value in node.value)
        replace_scalar(fields["resource"], source["resource"])
    previous = len(original) + 1
    for start, end, replacement in sorted(replacements, reverse=True):
        if end > previous:
            raise ValueError("overlapping YAML source scalars are not supported")
        original = original[:start] + replacement + original[end:]
        previous = start
    if yaml.safe_load(original) != metadata:
        raise ValueError("source rewrite would change unrelated frontmatter fields")
    return original


def selected_sources(contract, source_ids: list[str] | None = None) -> list[dict]:
    definitions = {key: value for key, value in contract.local_sources.items() if value.get("kind") == "git"}
    if source_ids is None:
        return list(definitions.values())
    unknown = set(source_ids) - definitions.keys()
    if unknown:
        raise ValueError(f"unknown Git source IDs: {', '.join(sorted(unknown))}")
    return [definitions[key] for key in dict.fromkeys(source_ids)]


def localize(root: Path, stamp: str, *, paths: list[str] | None = None, source_ids: list[str] | None = None) -> int:
    report = ingest.graph_artifact_path(root, "artifacts/graphs/source_resources.json")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp):
        raise ValueError("updated-at must be a UTC timestamp YYYY-MM-DDTHH:MM:SSZ")
    if datetime.fromisoformat(stamp.replace("Z", "+00:00")) > datetime.now(timezone.utc):
        raise ValueError("updated-at must not be in the future")
    contract = ingest.load_contract(root)
    directories = []
    for value in paths or ["knowledge/ops/ascendc/operators"]:
        directory = root / value
        if (not resources.safe_path(value) or not directory.is_relative_to(root / "knowledge")
                or directory.resolve() != directory or not directory.is_dir()):
            raise ValueError(f"localize path must be an existing directory under knowledge/: {value}")
        directories.append(directory)
    definitions = selected_sources(contract, source_ids)
    selected_roots = {definition["root"] for definition in definitions}

    def resolve(value: str):
        if not any(value.startswith((definition["root"] + "/", definition["repository"] + "/")) for definition in definitions):
            return None
        return resources.git_source(contract, value)

    # Rewrites require every selected snapshot to pass read-only validation first.
    for definition in definitions:
        for revision in definition["revisions"]:
            resources.validate_checkout(root, definition, revision)
    pending: dict[Path, str] = {}
    missing: list[dict[str, str]] = []
    for path in sorted({path for directory in directories for path in directory.rglob("*.md")}):
        if path.name == "index.md":
            continue
        if path.resolve() != path:
            raise ValueError(f"refusing symlink knowledge card: {path}")
        raw = path.read_bytes().decode("utf-8")
        framing = re.match(r"\A---\n(.*?)\n---\n(?P<gap>\n*)", raw, re.S)
        if framing is None:
            raise ValueError(f"missing card frontmatter: {path}")
        metadata = yaml.safe_load(framing.group(1))
        updated = False
        for source in metadata["sources"]:
            resolved = resolve(source["resource"])
            if resolved is not None and resolved.root in selected_roots and source["resource"] != resolved.resource:
                if not resolved.local_path(root).exists():
                    missing.append({"card": path.relative_to(root).as_posix(), "resource": source["resource"], "reason": "absent from pinned commit"})
                    continue
                source["resource"] = resolved.resource
                updated = True
        body = raw[framing.end():]
        authored = body
        masked = links.mask_code(authored)
        destinations = [(match.start(3), match.end(3), match.group(3)) for match in links.INLINE_LINK_RE.finditer(masked) if not match.group(1)]
        destinations.extend((match.start(2 if match.group(2) else 3), match.end(2 if match.group(2) else 3), match.group(2) or match.group(3)) for match in links.REFERENCE_DEFINITION_RE.finditer(masked))
        for start, end, original in sorted(destinations, reverse=True):
            target = original.split()[0].strip("<>")
            base, fragment = urldefrag(target)
            resolved = resolve(base)
            if resolved is None or resolved.root not in selected_roots or not base.startswith("https://"):
                continue
            destination = resolved.local_path(root)
            if not destination.exists():
                missing.append({"card": path.relative_to(root).as_posix(), "resource": target, "reason": "body link absent from pinned commit"})
                continue
            # Directory URLs remain remote navigation; source files become local links.
            if not destination.is_file() or (fragment and not re.fullmatch(r"L[1-9][0-9]*(?:-L[1-9][0-9]*)?", fragment)):
                continue
            local = quote(os.path.relpath(destination, path.parent), safe="/._-")
            if fragment:
                local += "#" + fragment
            replacement = authored[:start] + original.replace(target, local, 1) + authored[end:]
            updated |= replacement != authored
            authored = replacement
        if not updated:
            continue
        metadata["updated_at"] = stamp
        body = authored
        rendered = "---\n" + source_frontmatter(framing.group(1), metadata) + "\n---\n" + framing.group("gap") + body
        pending[path] = rendered
    for path, rendered in pending.items():
        ingest.atomic_write(path, rendered)
    ingest.atomic_write(report, json.dumps({"missing_sources": missing}, ensure_ascii=False, indent=2) + "\n")
    print(f"unavailable source references={len(missing)} report={report.relative_to(root)}")
    return len(pending)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch")
    verify = commands.add_parser("verify")
    local = commands.add_parser("localize")
    local.add_argument("--updated-at", required=True)
    local.add_argument("--path", action="append", help="knowledge directory; defaults to Ascend C Operators")
    for command in (fetch, verify, local):
        command.add_argument("--source", action="append", help="registered Git source ID; repeat to select several")
    args = parser.parse_args()
    try:
        root = ingest.resolve_root(args.knowledge_root)
        definitions = selected_sources(ingest.load_contract(root), args.source)
        if args.command == "fetch":
            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(lambda definition: fetch_repository(root, definition), definitions))
        elif args.command == "verify":
            for definition in definitions:
                for revision in definition["revisions"]:
                    resources.validate_checkout(root, definition, revision)
            print(f"verified Git snapshots={sum(len(item['revisions']) for item in definitions)}")
        else:
            count = localize(root, args.updated_at, paths=args.path, source_ids=args.source)
            print(f"localized {'knowledge' if args.path else 'Operator'} cards={count}")
    except (OSError, ValueError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
