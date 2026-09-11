#!/usr/bin/env python3
"""Inventory a pinned Git source and verify an auditable ingest ledger."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from knowledge_ingest import contract_module, contract_package, load_contract  # noqa: E402


SCHEMA = "cannbot-reference-inventory.v1"
LEDGER_SCHEMA = "cannbot-reference-ledger.v1"
VERIFICATION_SCHEMA = "cannbot-reference-verification.v1"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ROLES = {
    "primary",
    "supporting",
    "example",
    "constraint",
    "header",
    "implementation",
    "evidence",
}


def git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=text,
    )
    if result.returncode:
        stderr = result.stderr if text else result.stderr.decode("utf-8", "replace")
        raise ValueError(stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def source_root(value: str) -> Path:
    root = Path(value).resolve()
    if not root.is_dir() or not (root / ".git").exists():
        raise ValueError(f"not a Git checkout: {root}")
    return root


def normalize_scope(value: str) -> str:
    scope = value.strip().strip("/")
    path = PurePosixPath(scope)
    if not scope or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"invalid scope: {value}")
    return path.as_posix()


def classify(path: str) -> str:
    parsed = PurePosixPath(path)
    suffix = parsed.suffix.lower()
    lowered_parts = {part.lower() for part in parsed.parts}
    if lowered_parts & {"test", "tests"} or parsed.name.lower().startswith("test_"):
        return "test"
    if suffix in {".md", ".mdx", ".rst", ".txt"}:
        return "technical_doc"
    if suffix in {".h", ".hh", ".hpp", ".cuh"}:
        return "header"
    if suffix in {".c", ".cc", ".cpp", ".cu", ".py"}:
        return "implementation"
    if suffix in {".cmake", ".mk"} or parsed.name in {
        "CMakeLists.txt",
        "Makefile",
    }:
        return "build"
    return "other"


def tracked_entries(root: Path, scopes: list[str]) -> list[dict[str, Any]]:
    raw = git(root, "ls-files", "-s", "-z", text=False)
    assert isinstance(raw, bytes)
    entries: list[dict[str, Any]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, blob_oid, stage = header.decode("ascii").split()
        if stage != "0":
            continue
        path = raw_path.decode("utf-8", "surrogateescape")
        selected = any(path == scope or path.startswith(f"{scope}/") for scope in scopes)
        entries.append(
            {
                "path": path,
                "mode": mode,
                "blob_oid": blob_oid,
                "kind": classify(path),
                "selected": selected,
                "default_action": "review" if selected else "defer",
            }
        )
    return sorted(entries, key=lambda item: item["path"])


def digest(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8", "surrogatepass")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        errors="surrogatepass",
    )
    os.replace(temporary, path)


def atomic_create_json(path: Path, payload: object) -> None:
    """Atomically create a verification receipt without replacing an existing entry."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", errors="surrogatepass") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ValueError(f"refusing to overwrite verification receipt: {path}") from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8", errors="surrogatepass"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def inventory(args: argparse.Namespace) -> int:
    root = source_root(args.source_root)
    scopes = list(dict.fromkeys(normalize_scope(value) for value in args.scope))
    commit = str(git(root, "rev-parse", "HEAD")).strip()
    repo = args.repo
    if not repo:
        remote = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            check=False,
            capture_output=True,
            text=True,
        )
        repo = remote.stdout.strip() if remote.returncode == 0 else ""
    ref = args.ref or str(git(root, "branch", "--show-current")).strip()
    if not isinstance(repo, str) or not re.match(r"^https?://", repo):
        raise ValueError("source repository must be a canonical HTTP(S) URL; pass --repo")
    if not ref:
        raise ValueError("source ref is required for a detached checkout; pass --ref")
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError(f"source commit must be a 40-hex Git commit: {commit}")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "source": {
            "repo": repo,
            "ref": ref,
            "commit": commit,
        },
        "scopes": scopes,
        "entries": tracked_entries(root, scopes),
    }
    payload["inventory_sha256"] = digest(payload)
    atomic_json(Path(args.output), payload)
    selected = sum(bool(item["selected"]) for item in payload["entries"])
    print(f"entries={len(payload['entries'])} selected={selected} commit={commit}")
    return 0


def scaffold_ledger(args: argparse.Namespace) -> int:
    data = load_json(Path(args.inventory))
    validate_inventory_shape(data)
    decisions = []
    for entry in data["entries"]:
        selected = bool(entry["selected"])
        decisions.append(
            {
                "path": entry["path"],
                "action": "pending" if selected else "defer",
                "reason": "" if selected else "outside selected scope",
            }
        )
    payload = {
        "schema_version": LEDGER_SCHEMA,
        "inventory_sha256": data["inventory_sha256"],
        "decisions": decisions,
    }
    atomic_json(Path(args.output), payload)
    print(f"decisions={len(decisions)} pending={sum(d['action'] == 'pending' for d in decisions)}")
    return 0


def validate_inventory_shape(data: dict[str, Any]) -> None:
    if data.get("schema_version") != SCHEMA:
        raise ValueError(f"unsupported inventory schema: {data.get('schema_version')}")
    claimed = data.get("inventory_sha256")
    unsigned = {key: value for key, value in data.items() if key != "inventory_sha256"}
    if claimed != digest(unsigned):
        raise ValueError("inventory_sha256 does not match inventory content")
    entries = data.get("entries")
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        raise ValueError("inventory entries must be a list of objects")
    paths = [item.get("path") for item in entries]
    if any(not isinstance(path, str) for path in paths) or len(paths) != len(set(paths)):
        raise ValueError("inventory paths must be unique strings")
    source = data.get("source")
    if not isinstance(source, dict):
        raise ValueError("inventory source must be an object")
    repo = source.get("repo")
    ref = source.get("ref")
    commit = source.get("commit")
    if not isinstance(repo, str) or not re.match(r"^https?://", repo):
        raise ValueError("inventory source.repo must be a canonical HTTP(S) URL")
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError("inventory source.ref must be a non-empty string")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise ValueError("inventory source.commit must be a 40-hex Git commit")


def valid_target(value: object) -> bool:
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and len(path.parts) >= 4
        and path.parts[0] == "knowledge"
        and ".." not in path.parts
        and path.suffix == ".md"
        and path.name != "index.md"
    )


def target_contract(value: str):
    root = Path(value).resolve()
    if not (root / "knowledge").is_dir():
        raise ValueError(f"not a cannbot-knowledge root: {root}")
    contract = load_contract(root)
    return root, contract, contract_module().split_frontmatter


def source_binds_entry(resource: object, inventory: dict[str, Any], path: str, contract=None) -> bool:
    if not isinstance(resource, str):
        return False
    if contract is not None and not resource.startswith(("http://", "https://")):
        resources = importlib.import_module(f"{contract_package().__name__}.source_resources")
        try:
            local = resources.git_source(contract, resource)
        except ValueError:
            return False
        if local is None:
            return False
        resource = local.url
    source = inventory["source"]
    repository = str(source["repo"]).rstrip("/")
    if repository.endswith(".git"):
        repository = repository[:-4]
    decoded = unquote(resource)
    if not decoded.startswith(repository + "/"):
        return False
    commit = str(source["commit"])
    suffix = decoded[len(repository) :]
    fixed_paths = (
        f"/blob/{commit}/{path}",
        f"/-/blob/{commit}/{path}",
    )
    return any(suffix == fixed or suffix.startswith(fixed + "#") for fixed in fixed_paths)


def validate_produced_cards(
    root: Path,
    contract,
    split_frontmatter,
    inventory_data: dict[str, Any],
    decisions: list[dict[str, Any]],
    errors: list[str],
) -> list[dict[str, Any]]:
    produced: list[dict[str, Any]] = []
    inventory_entries = {item["path"]: item for item in inventory_data["entries"]}
    targets: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        if decision.get("action") == "ingest" and valid_target(decision.get("target_card")):
            targets.setdefault(str(decision["target_card"]), []).append(decision)

    for target_value, target_decisions in sorted(targets.items()):
        relative = Path(target_value)
        target = (root / relative).resolve()
        if not target.is_file() or root not in target.parents:
            errors.append(f"{target_value}: produced target card does not exist")
            continue
        try:
            metadata, body = split_frontmatter(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"{target_value}: cannot read produced card: {exc}")
            continue
        if metadata is None:
            errors.append(f"{target_value}: produced card is missing frontmatter")
            continue
        issues = contract.validate_card(relative, metadata, body)
        for issue in issues:
            errors.append(f"{target_value}: {issue.code}: {issue.message}")

        sources = metadata.get("sources")
        source_values = sources if isinstance(sources, list) else []
        bound_sources: list[dict[str, str]] = []
        for decision in target_decisions:
            source_path = str(decision["path"])
            role = str(decision.get("role", ""))
            if source_path not in inventory_entries:
                continue
            match = next(
                (
                    source
                    for source in source_values
                    if isinstance(source, dict)
                    and source.get("role") == role
                    and source_binds_entry(source.get("resource"), inventory_data, source_path, contract)
                ),
                None,
            )
            if match is None:
                errors.append(
                    f"{target_value}: no card source binds {source_path} "
                    f"at {inventory_data['source']['commit']} with role {role}"
                )
            else:
                inventory_entry = inventory_entries[source_path]
                bound_sources.append(
                    {
                        "path": source_path,
                        "blob_oid": str(inventory_entry["blob_oid"]),
                        "role": role,
                        "resource": str(match["resource"]),
                    }
                )
        produced.append(
            {
                "target_card": target_value,
                "card_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "sources": bound_sources,
            }
        )
    return produced


def verify(args: argparse.Namespace) -> int:
    inventory_data = load_json(Path(args.inventory))
    ledger = load_json(Path(args.ledger))
    validate_inventory_shape(inventory_data)
    root, contract, split_frontmatter = target_contract(args.knowledge_root)
    errors: list[str] = []
    if ledger.get("schema_version") != LEDGER_SCHEMA:
        errors.append(f"unsupported ledger schema: {ledger.get('schema_version')}")
    if ledger.get("inventory_sha256") != inventory_data["inventory_sha256"]:
        errors.append("ledger inventory_sha256 does not match inventory")
    decisions = ledger.get("decisions")
    if not isinstance(decisions, list) or any(not isinstance(item, dict) for item in decisions):
        raise ValueError("ledger decisions must be a list of objects")
    inventory_paths = {item["path"] for item in inventory_data["entries"]}
    decision_paths = [item.get("path") for item in decisions]
    invalid_paths = [path for path in decision_paths if not isinstance(path, str)]
    if invalid_paths:
        errors.append("ledger decision paths must be strings")
    valid_decision_path_values = [path for path in decision_paths if isinstance(path, str)]
    valid_decision_paths = set(valid_decision_path_values)
    if len(valid_decision_path_values) != len(valid_decision_paths):
        errors.append("ledger contains duplicate decision paths")
    missing = sorted(inventory_paths - valid_decision_paths)
    extra = sorted(valid_decision_paths - inventory_paths)
    if missing:
        errors.append(f"ledger is missing paths: {', '.join(missing[:10])}")
    if extra:
        errors.append(f"ledger contains unknown paths: {', '.join(extra[:10])}")
    for decision in decisions:
        path = decision.get("path", "<missing>")
        action = decision.get("action")
        if action not in {"ingest", "defer", "skip"}:
            errors.append(f"{path}: action must be ingest, defer, or skip")
        elif action == "ingest":
            if not valid_target(decision.get("target_card")):
                errors.append(f"{path}: ingest requires a knowledge/...md target_card")
            else:
                try:
                    contract.derive_card_path(Path(str(decision["target_card"])))
                except ValueError as exc:
                    errors.append(f"{path}: invalid target_card: {exc}")
            if decision.get("role") not in ROLES:
                errors.append(f"{path}: ingest requires a registered source role")
        elif not str(decision.get("reason", "")).strip():
            errors.append(f"{path}: {action} requires a reason")
    targets: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        if decision.get("action") == "ingest" and valid_target(decision.get("target_card")):
            targets.setdefault(str(decision["target_card"]), []).append(decision)
    for target, target_decisions in sorted(targets.items()):
        primary_count = sum(item.get("role") == "primary" for item in target_decisions)
        if primary_count != 1:
            errors.append(f"{target}: ingest decisions require exactly one primary source")
    produced = validate_produced_cards(
        root,
        contract,
        split_frontmatter,
        inventory_data,
        decisions,
        errors,
    )
    if args.source_root:
        root = source_root(args.source_root)
        actual_commit = str(git(root, "rev-parse", "HEAD")).strip()
        expected_commit = inventory_data.get("source", {}).get("commit")
        if actual_commit != expected_commit:
            errors.append(
                f"source checkout is at {actual_commit}, inventory expects {expected_commit}"
            )
        scopes = [normalize_scope(value) for value in inventory_data.get("scopes", [])]
        if tracked_entries(root, scopes) != inventory_data["entries"]:
            errors.append("tracked source tree no longer matches inventory")
    counts = Counter(item.get("action", "missing") for item in decisions)
    result = {
        "schema_version": VERIFICATION_SCHEMA,
        "inventory_sha256": inventory_data["inventory_sha256"],
        "ledger_sha256": digest(ledger),
        "source": inventory_data["source"],
        "entries": len(inventory_paths),
        "actions": dict(sorted(counts.items())),
        "produced": produced,
        "errors": errors,
    }
    if args.receipt and not errors:
        atomic_create_json(Path(args.receipt), result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for error in errors:
            print(f"ERROR {error}")
        print(" ".join([f"entries={result['entries']}", *(f"{key}={value}" for key, value in result["actions"].items()), f"errors={len(errors)}"]))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    inventory_cmd = commands.add_parser("inventory")
    inventory_cmd.add_argument("--source-root", required=True)
    inventory_cmd.add_argument("--scope", action="append", required=True)
    inventory_cmd.add_argument("--repo")
    inventory_cmd.add_argument("--ref")
    inventory_cmd.add_argument("--output", required=True)
    inventory_cmd.set_defaults(handler=inventory)
    scaffold_cmd = commands.add_parser("scaffold-ledger")
    scaffold_cmd.add_argument("--inventory", required=True)
    scaffold_cmd.add_argument("--output", required=True)
    scaffold_cmd.set_defaults(handler=scaffold_ledger)
    verify_cmd = commands.add_parser("verify")
    verify_cmd.add_argument("--inventory", required=True)
    verify_cmd.add_argument("--ledger", required=True)
    verify_cmd.add_argument("--source-root")
    verify_cmd.add_argument("--knowledge-root", required=True)
    verify_cmd.add_argument("--receipt")
    verify_cmd.add_argument("--json", action="store_true")
    verify_cmd.set_defaults(handler=verify)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
