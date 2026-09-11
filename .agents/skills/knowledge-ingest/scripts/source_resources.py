#!/usr/bin/env python3
"""Restore and verify Registry-pinned source worktrees without changing knowledge."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib
from pathlib import Path
import subprocess
import sys

import yaml

import knowledge_ingest as ingest


sys.dont_write_bytecode = True
resources = importlib.import_module(f"{ingest.contract_package().__name__}.source_resources")


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("fetch")
    commands.add_parser("verify")
    args = parser.parse_args()
    try:
        root = ingest.resolve_root(args.knowledge_root)
        definitions = [item for item in ingest.load_contract(root).local_sources.values() if item.get("kind") == "git"]
        if args.command == "fetch":
            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(lambda definition: fetch_repository(root, definition), definitions))
        elif args.command == "verify":
            for definition in definitions:
                for revision in definition["revisions"]:
                    resources.validate_checkout(root, definition, revision)
            print(f"verified Git snapshots={sum(len(item['revisions']) for item in definitions)}")
    except (OSError, ValueError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
