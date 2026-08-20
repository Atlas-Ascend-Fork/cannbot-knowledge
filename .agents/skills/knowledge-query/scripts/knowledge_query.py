#!/usr/bin/env python3
"""Query the prepared cannbot-knowledge index and return governed card locators."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from retrieval.index import (  # noqa: E402
    IndexedCard,
    load_cards,
    open_index,
    phrase_matches,
    posting_scores,
    query_tokens,
)
from retrieval.root import (  # noqa: E402
    atomic_create_json,
    canonical_json_sha256,
    extract_knowledge_root,
    repository_state,
    resolve_root,
)


sys.dont_write_bytecode = True
SEARCH_SCHEMA = "knowledge-search.v4"
RECEIPT_SCHEMA = "cannbot-knowledge-search.v2"


def load_governance(root: Path) -> tuple[dict[str, object], set[str]]:
    registries = yaml.safe_load(
        (root / "governance/schemas/registries.yaml").read_text(encoding="utf-8")
    )
    profiles = yaml.safe_load(
        (root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
    )
    if not isinstance(registries, dict) or not isinstance(profiles, dict):
        raise ValueError("governance registries and profiles must be mappings")
    profile_values = profiles.get("profiles")
    if not isinstance(profile_values, dict):
        raise ValueError("profiles.yaml must define a profiles mapping")
    return registries, set(profile_values)


def verification_events(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    value = metadata.get("verified")
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [event for event in value if isinstance(event, dict)]
    return []


def trust_tier(metadata: dict[str, Any]) -> str:
    events = verification_events(metadata)
    if any(str(event.get("by", "")).startswith("human:") for event in events):
        return "human-reviewed"
    if events:
        return "machine-confirmed"
    return "unverified"


def task_tag(registries: dict[str, object], value: str | None) -> str | None:
    if not value:
        return None
    candidate = value if value.startswith("task.") else f"task.{value}"
    task = (registries.get("tags") or {}).get(candidate)
    if not isinstance(task, dict) or task.get("dimension") != "task":
        raise ValueError(f"unknown task: {value}")
    return candidate


def registry_keys(registries: dict[str, object], section: str) -> set[str]:
    values = registries.get(section)
    if not isinstance(values, dict):
        raise ValueError(f"registries.yaml must define a {section} mapping")
    return set(values)


def validate_filters(registries: dict[str, object], args: argparse.Namespace) -> None:
    if args.domain and args.domain not in registry_keys(registries, "domains"):
        raise ValueError(f"unknown domain: {args.domain}")
    technologies = registry_keys(registries, "technologies")
    routes = technologies | registry_keys(registries, "scopes")
    if args.technology and args.technology not in routes:
        raise ValueError(f"unknown technology or scope: {args.technology}")
    if args.include_shared and args.technology not in technologies:
        raise ValueError("--include-shared requires a concrete technology")
    if args.source_technology and args.source_technology not in technologies:
        raise ValueError(f"unknown source technology: {args.source_technology}")
    if args.target_technology and args.target_technology not in technologies:
        raise ValueError(f"unknown target technology: {args.target_technology}")
    platforms = registry_keys(registries, "platforms")
    unknown_platforms = sorted(set(args.platform) - platforms)
    if unknown_platforms:
        raise ValueError(f"unknown platforms: {', '.join(unknown_platforms)}")
    tags = registry_keys(registries, "tags")
    unknown_tags = sorted(set(args.tag) - tags)
    if unknown_tags:
        raise ValueError(f"unknown tags: {', '.join(unknown_tags)}")
    if args.include_unlocated and args.platform:
        raise ValueError("--include-unlocated cannot be combined with --platform")
    if args.include_unlocated and args.status not in {"draft", "all"}:
        raise ValueError("--include-unlocated requires --status draft or all")
    platform_identification = args.technology == "platforms"
    if not args.platform and not args.include_unlocated and not platform_identification:
        raise ValueError(
            "platform is required; determine a target platform, use the platforms scope "
            "for identification, or explicitly request draft --include-unlocated cards"
        )


def matches(
    card: IndexedCard,
    args: argparse.Namespace,
    mapped_task: str | None,
    selected_route_domains: set[str],
) -> bool:
    metadata = card.metadata
    if args.status != "all" and metadata.get("status") != args.status:
        return False
    if args.domain and card.domain != args.domain:
        return False
    if args.technology:
        route_matches = card.technology == args.technology
        shared_matches = (
            args.include_shared
            and card.technology == "shared"
            and card.domain in selected_route_domains
            and (
                card.profile != "interoperability"
                or args.technology
                in {
                    metadata.get("source_technology"),
                    metadata.get("target_technology"),
                }
            )
        )
        if not route_matches and not shared_matches:
            return False
    if args.card_type and card.profile != args.card_type:
        return False
    card_tags = set(metadata.get("tags") or [])
    required_tags = set(args.tag or [])
    if mapped_task:
        required_tags.add(mapped_task)
    if not required_tags.issubset(card_tags):
        return False
    if args.include_unlocated:
        if card.profile == "glossaries" or metadata.get("platforms"):
            return False
    elif args.platform and card.profile != "glossaries":
        platforms = set(metadata.get("platforms") or [])
        if "agnostic" not in platforms and not set(args.platform).issubset(platforms):
            return False
    if args.cann_version:
        versions = set(metadata.get("cann_versions") or [])
        if not set(args.cann_version).issubset(versions):
            return False
    if args.source_technology and metadata.get("source_technology") != args.source_technology:
        return False
    if args.target_technology and metadata.get("target_technology") != args.target_technology:
        return False
    return True


def index_provenance(
    metadata: dict[str, Any],
    root: Path,
    *,
    include_current_repository: bool = False,
) -> dict[str, Any]:
    result = {
        "schema_version": metadata["schema_version"],
        "index_version": metadata["index_version"],
        "content_fingerprint": metadata["content_fingerprint"],
        "governance_fingerprint": metadata["governance_fingerprint"],
        "card_count": metadata["card_count"],
        "posting_count": metadata["posting_count"],
        "built_repository_state": metadata.get("repository_state"),
    }
    if include_current_repository:
        result["query_repository_state"] = repository_state(root)
    return result


def discover(
    root: Path,
    cards: list[IndexedCard],
    index_metadata: dict[str, Any],
    args: argparse.Namespace,
) -> int:
    result = {
        "schema_version": "knowledge-discovery.v1",
        "root": str(root),
        "cards": len(cards),
        "domains": dict(sorted(Counter(card.domain for card in cards).items())),
        "technologies": dict(
            sorted(Counter(card.technology or "none" for card in cards).items())
        ),
        "types": dict(
            sorted(Counter(str(card.metadata.get("type")) for card in cards).items())
        ),
        "profiles": dict(sorted(Counter(card.profile for card in cards).items())),
        "statuses": dict(
            sorted(Counter(str(card.metadata.get("status")) for card in cards).items())
        ),
        "index": index_provenance(index_metadata, root),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"root: {result['root']}")
        print(f"cards: {result['cards']}")
        for key in ("domains", "technologies", "types", "profiles", "statuses"):
            print(
                f"{key}: "
                + ", ".join(f"{name}={count}" for name, count in result[key].items())
            )
    return 0


def request_payload(args: argparse.Namespace, mapped_task: str | None) -> dict[str, Any]:
    filters = {
        "domain": args.domain,
        "technology": args.technology,
        "profile": args.card_type,
        "task": mapped_task,
        "tags": args.tag,
        "platforms": args.platform,
        "include_unlocated": args.include_unlocated,
        "cann_versions": args.cann_version,
        "include_shared": args.include_shared,
        "source_technology": args.source_technology,
        "target_technology": args.target_technology,
        "status": args.status,
    }
    return {
        "query": args.query,
        "decision": args.decision,
        "match": args.match,
        **filters,
        "filters": filters,
        "limit": args.limit,
    }


def search(
    root: Path,
    cards: list[IndexedCard],
    index_metadata: dict[str, Any],
    connection,
    args: argparse.Namespace,
) -> int:
    registries, profiles = load_governance(root)
    if args.card_type and args.card_type not in profiles:
        raise ValueError(f"unknown knowledge type: {args.card_type}")
    validate_filters(registries, args)
    mapped_task = task_tag(registries, args.task)
    selected_route = None
    if args.technology:
        selected_route = (registries.get("technologies") or {}).get(args.technology)
        selected_route = selected_route or (registries.get("scopes") or {}).get(
            args.technology
        )
    selected_route_domains = (
        set(selected_route.get("domains", [])) if isinstance(selected_route, dict) else set()
    )
    eligible = {
        card.doc_id: card
        for card in cards
        if matches(card, args, mapped_task, selected_route_domains)
    }
    normalized_query = args.query.lower().strip()
    if not normalized_query:
        raise ValueError("--query must not be empty")
    phrase_ids = phrase_matches(connection, normalized_query)
    if args.match == "literal":
        raw_scores = {doc_id: 1.0 for doc_id in phrase_ids}
    else:
        raw_scores = posting_scores(connection, query_tokens(args.query))
        for doc_id in phrase_ids:
            raw_scores[doc_id] = raw_scores.get(doc_id, 0.0) + 4.0

    ranked: list[tuple[float, IndexedCard]] = []
    for doc_id, score in raw_scores.items():
        card = eligible.get(doc_id)
        if card is None or score <= 0:
            continue
        tier = trust_tier(card.metadata)
        if tier == "unverified":
            score *= 0.8
        elif tier == "machine-confirmed":
            score *= 0.9
        ranked.append((score, card))
    ranked.sort(key=lambda item: (-item[0], item[1].path))
    ranked = ranked[: args.limit]

    results = []
    for rank, (score, card) in enumerate(ranked, start=1):
        metadata = card.metadata
        result = {
            "rank": rank,
            "score": round(score, 3),
            "match_basis": args.match,
            "path": card.path,
            "local_path": str(root / card.relative_path),
            "card_lines": card.card_lines,
            "card_sha256": card.card_sha256,
            "title": metadata.get("title"),
            "description": metadata.get("description"),
            "domain": card.domain,
            "technology": card.technology,
            "type": metadata.get("type"),
            "profile": card.profile,
            "status": metadata.get("status"),
            "trust_tier": trust_tier(metadata),
            "platforms": metadata.get("platforms"),
            "tags": metadata.get("tags"),
            "sources": metadata.get("sources", [])[:2],
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
        }
        for field in (
            "cann_versions",
            "aliases",
            "verified",
            "source_technology",
            "target_technology",
            "replaced_by",
        ):
            if field in metadata:
                result[field] = metadata[field]
        results.append(result)

    request = request_payload(args, mapped_task)
    request_sha256 = canonical_json_sha256(request)
    provenance = index_provenance(
        index_metadata,
        root,
        include_current_repository=bool(args.receipt),
    )
    payload = {
        "schema_version": SEARCH_SCHEMA,
        "request_sha256": request_sha256,
        "request": request,
        "query": args.query,
        "match": args.match,
        "filters": request["filters"],
        "limit": args.limit,
        "count": len(results),
        "index": provenance,
        "results": results,
        "hits": results,
    }
    if args.receipt:
        receipt = {
            "schema_version": RECEIPT_SCHEMA,
            "knowledge_root": str(root),
            "knowledge_commit": provenance["query_repository_state"]["commit"],
            "knowledge_dirty": provenance["query_repository_state"]["dirty"],
            "request": request,
            "request_sha256": request_sha256,
            "index": provenance,
            "result": payload,
        }
        atomic_create_json(Path(args.receipt), receipt)
    if args.text:
        for hit in results:
            print(
                f"[{hit['rank']} score={hit['score']:.3f}] {hit['title']} "
                f"status={hit['status']} trust={hit['trust_tier']}"
            )
            print(f"  path: {hit['path']}")
            print(f"  local_path: {hit['local_path']} ({hit['card_lines']} lines)")
            print(f"  description: {hit['description']}")
        if not results:
            print("no matches")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="knowledge_query",
        allow_abbrev=False,
        description=__doc__,
        epilog="Global root option accepted anywhere: --knowledge-root PATH.",
    )
    result.add_argument("--knowledge-root", help=argparse.SUPPRESS)
    commands = result.add_subparsers(dest="command", required=True)
    discover_cmd = commands.add_parser("discover", allow_abbrev=False)
    discover_cmd.add_argument("--json", action="store_true")
    search_cmd = commands.add_parser("search", allow_abbrev=False)
    search_cmd.add_argument("--query", required=True)
    search_cmd.add_argument("--decision")
    search_cmd.add_argument("--domain")
    search_cmd.add_argument("--technology")
    search_cmd.add_argument("--type", dest="card_type")
    search_cmd.add_argument("--task")
    search_cmd.add_argument("--tag", action="append", default=[])
    search_cmd.add_argument("--platform", action="append", default=[])
    search_cmd.add_argument("--include-unlocated", action="store_true")
    search_cmd.add_argument("--cann-version", action="append", default=[])
    search_cmd.add_argument("--include-shared", action="store_true")
    search_cmd.add_argument("--source-technology")
    search_cmd.add_argument("--target-technology")
    search_cmd.add_argument(
        "--status",
        choices=["stable", "draft", "deprecated", "all"],
        default="stable",
    )
    search_cmd.add_argument("--match", choices=["text", "literal"], default="text")
    search_cmd.add_argument("-k", "--k", "--limit", dest="limit", type=int, default=10)
    output = search_cmd.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="JSON is the default")
    output.add_argument("--text", action="store_true")
    search_cmd.add_argument("--receipt")
    return result


def main(argv: list[str] | None = None) -> int:
    connection = None
    try:
        cleaned, explicit = extract_knowledge_root(sys.argv[1:] if argv is None else argv)
        args = build_parser().parse_args(cleaned)
        if getattr(args, "limit", 1) < 1:
            raise ValueError("--limit must be greater than zero")
        root = resolve_root(explicit, __file__)
        connection, index_metadata = open_index(
            root,
            full=bool(getattr(args, "receipt", None)),
        )
        cards = load_cards(connection)
        if args.command == "discover":
            return discover(root, cards, index_metadata, args)
        return search(root, cards, index_metadata, connection, args)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(
            json.dumps(
                {"error": {"type": exc.__class__.__name__, "message": str(exc)}},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
