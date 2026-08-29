#!/usr/bin/env python3
"""Build, inspect, and verify the local knowledge relationship graph."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import math
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

import yaml



def load_ingest_module():
    module_name = "_cannbot_knowledge_graph_ingest"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    source = Path(__file__).with_name("knowledge_ingest.py")
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ingest support module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ingest = load_ingest_module()


MANAGED_START = "<!-- cannbot:related:start -->"
MANAGED_END = "<!-- cannbot:related:end -->"
MANAGED_RE = re.compile(
    rf"(?ms)^\s*{re.escape(MANAGED_START)}\n.*?^{re.escape(MANAGED_END)}\s*"
)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_:]*|\d{3,}")
SHORT_TECHNICAL = {"ai", "api", "cv", "ge", "gm", "l0", "l1", "l2", "ub", "vf"}
STOP_TERMS = {
    "aicore",
    "ascend",
    "ascendc",
    "ascend950",
    "arch35",
    "api",
    "apis",
    "build",
    "cann",
    "common",
    "concept",
    "concepts",
    "const",
    "example",
    "examples",
    "guide",
    "guides",
    "invalid",
    "kernel",
    "kernels",
    "operator",
    "operators",
    "ops",
    "optimization",
    "optimizations",
    "params",
    "runbook",
    "runbooks",
    "shared",
    "template",
}
ALLOWED_RELATIONS = {
    "exemplifies",
    "explains",
    "links_to",
    "part_of",
    "related",
    "same_topic",
}
DEFAULT_CANDIDATES_PER_CARD = 30
DEFAULT_SHARD_COUNT = 90
REVIEW_EXCERPT_CHARS = 1000
REVIEW_REASON_MIN_CHARS = 24
REVIEW_EVIDENCE_MIN_CHARS = 8
REVIEW_REASON_BANNED_FRAGMENTS = {
    "Agent read both complete cards",
    "agent read both complete cards",
    "共同组成闭环",
    "共享某词",
    "可交叉核对",
    "可直接核对该问题",
    "能够补齐该处",
    "todo",
    "tbd",
    "待补充",
    "占位",
}
REVIEW_BRIDGE_NEGATIONS = {
    "两卡无关",
    "两者无关",
    "不相关",
    "不存在语义衔接",
    "没有直接关系",
    "no semantic connection",
    "not related",
    "unrelated",
}
REVIEW_TERMINAL_TRUNCATION_RE = re.compile(r"(?:\.\.\.|\u2026)\s*$")


@dataclass(frozen=True)
class Card:
    doc_id: str
    path: Path
    profile: str
    metadata: dict[str, object]
    body: str
    fingerprint: str
    terms: dict[str, float]
    symbols: set[str]
    body_mentions: set[str]
    tags: set[str]

    @property
    def title(self) -> str:
        return str(self.metadata["title"])


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_agent_evidence(
    reason: object,
    evidence: object,
    endpoints: tuple[str, str],
    context: object,
    *,
    allow_negative_bridge: bool = False,
    card_bodies: dict[str, str] | None = None,
) -> tuple[str, dict[str, object]]:
    """Validate an Agent decision's audit shape without deciding if the edge is true."""
    if not isinstance(reason, str):
        raise ValueError(f"Agent decision reason must be a string for {context}")
    normalized_reason = " ".join(reason.split())
    if len(normalized_reason) < REVIEW_REASON_MIN_CHARS:
        raise ValueError(f"Agent decision reason is too short for {context}")
    if REVIEW_TERMINAL_TRUNCATION_RE.search(normalized_reason):
        raise ValueError(f"Agent decision reason is truncated for {context}")
    if "；；" in normalized_reason or ";;" in normalized_reason:
        raise ValueError(f"Agent decision reason is malformed for {context}")
    folded_reason = normalized_reason.casefold()
    for fragment in REVIEW_REASON_BANNED_FRAGMENTS:
        if fragment.casefold() in folded_reason:
            raise ValueError(f"Agent decision reason uses a forbidden template for {context}")
    if not isinstance(evidence, dict):
        raise ValueError(f"Agent decision evidence must be an object for {context}")
    anchors = evidence.get("anchors")
    if not isinstance(anchors, dict) or set(anchors) != set(endpoints):
        raise ValueError(f"Agent decision evidence must anchor both endpoints for {context}")
    normalized_anchors: dict[str, str] = {}
    for endpoint in endpoints:
        anchor = anchors.get(endpoint)
        if not isinstance(anchor, str):
            raise ValueError(f"Agent decision anchor must be a string for {context}")
        normalized = " ".join(anchor.split())
        if len(normalized) < REVIEW_EVIDENCE_MIN_CHARS or normalized == endpoint:
            raise ValueError(f"Agent decision anchor is not specific for {context}")
        if card_bodies is not None:
            body = card_bodies.get(endpoint)
            if not isinstance(body, str) or normalized not in " ".join(body.split()):
                raise ValueError(
                    f"Agent decision anchor is not present in endpoint body for {context}"
                )
        normalized_anchors[endpoint] = normalized
    if len(set(normalized_anchors.values())) != 2:
        raise ValueError(f"Agent decision anchors must state distinct endpoint facts for {context}")
    bridge = evidence.get("bridge")
    scope_note = evidence.get("scope_note")
    if not isinstance(bridge, str) or not isinstance(scope_note, str):
        raise ValueError(f"Agent decision bridge and scope_note must be strings for {context}")
    normalized_bridge = " ".join(bridge.split())
    normalized_scope = " ".join(scope_note.split())
    if len(normalized_scope) < REVIEW_EVIDENCE_MIN_CHARS:
        raise ValueError(f"Agent decision scope_note is too short for {context}")
    for value, field in ((normalized_bridge, "bridge"), (normalized_scope, "scope_note")):
        if REVIEW_TERMINAL_TRUNCATION_RE.search(value):
            raise ValueError(f"Agent decision evidence.{field} is truncated for {context}")
    folded_bridge = normalized_bridge.casefold()
    for fragment in REVIEW_REASON_BANNED_FRAGMENTS:
        if fragment.casefold() in folded_bridge:
            raise ValueError(f"Agent decision bridge uses a forbidden template for {context}")
    if not allow_negative_bridge and any(
        fragment.casefold() in folded_bridge for fragment in REVIEW_BRIDGE_NEGATIONS
    ):
        raise ValueError(f"Agent decision bridge explicitly denies the relation for {context}")
    bridge_remainder = normalized_bridge
    for anchor in normalized_anchors.values():
        if anchor not in normalized_reason or anchor not in normalized_bridge:
            raise ValueError(f"Agent decision reason and bridge must include both anchors for {context}")
        bridge_remainder = bridge_remainder.replace(anchor, "", 1)
    if len("".join(bridge_remainder.split())) < REVIEW_EVIDENCE_MIN_CHARS:
        raise ValueError(f"Agent decision bridge does not explain the connection for {context}")
    return normalized_reason, {
        "anchors": normalized_anchors,
        "bridge": normalized_bridge,
        "scope_note": normalized_scope,
    }


def strip_managed(text: str) -> str:
    """Remove only graph-owned related blocks, preserving authored content."""
    return MANAGED_RE.sub("\n", text).rstrip() + "\n"


def normalized_term(raw: str) -> str | None:
    term = raw.lower().strip(":_")
    if not term or term in STOP_TERMS:
        return None
    if len(term) < 3 and term not in SHORT_TECHNICAL:
        return None
    return term


def normalized_term_variants(raw: str) -> set[str]:
    """Normalize spelling variants for recall, not for relationship judgment."""
    result: set[str] = set()
    term = normalized_term(raw)
    if term is not None:
        result.add(term)
    trimmed = raw.strip(":_")
    compact = re.sub(r"[_:]", "", trimmed).lower()
    compact_term = normalized_term(compact)
    if compact_term is not None:
        result.add(compact_term)
    if (trimmed.startswith("Asc") and trimmed[3:4].isupper()) or trimmed.lower().startswith(
        "asc_"
    ):
        without_namespace = re.sub(r"[_:]", "", trimmed[3:]).lower()
        namespace_term = normalized_term(without_namespace)
        if namespace_term is not None:
            result.add(namespace_term)
    return result


def symbol_fragments(raw: str) -> set[str]:
    """Produce broad spelling fragments for API-symbol recall."""
    compact = re.sub(r"[^A-Za-z0-9]", "", raw).lower()
    if len(compact) < 5:
        return set()
    return {f"sym:{compact[index:index + 4]}" for index in range(len(compact) - 3)}


def symbol_terms(metadata: dict[str, object], relative: Path) -> set[str]:
    title_tokens = TOKEN_RE.findall(str(metadata.get("title", "")))
    raw_symbols = [relative.stem]
    raw_symbols.extend(
        raw
        for raw in title_tokens
        if len(title_tokens) == 1
        or "_" in raw
        or ":" in raw
        or any(character.isdigit() for character in raw)
        or any(character.isupper() for character in raw[1:])
    )
    for alias in metadata.get("aliases", []):
        raw_symbols.extend(TOKEN_RE.findall(str(alias)))
    return {
        term
        for raw in raw_symbols
        for term in normalized_term_variants(raw)
        if len(term) >= 4
    }


def body_mentions(body: str) -> set[str]:
    return {
        term
        for raw in TOKEN_RE.findall(body)
        for term in normalized_term_variants(raw)
        if len(term) >= 4
    }


def weighted_terms(
    metadata: dict[str, object], relative: Path, body: str
) -> dict[str, float]:
    fields: list[tuple[str, float]] = [
        (str(metadata.get("title", "")), 6.0),
        (str(metadata.get("description", "")), 2.0),
        (" ".join(str(item) for item in metadata.get("aliases", [])), 5.0),
        (" ".join(relative.with_suffix("").parts), 3.0),
        (body, 0.5),
    ]
    result: dict[str, float] = {}
    for value, weight in fields:
        for raw in TOKEN_RE.findall(value):
            for term in sorted(normalized_term_variants(raw)):
                result[term] = max(result.get(term, 0.0), weight)
    for component in relative.with_suffix("").parts:
        pieces = [piece for piece in component.lower().split("_") if piece]
        for size in range(2, min(4, len(pieces)) + 1):
            for start in range(len(pieces) - size + 1):
                term = normalized_term("_".join(pieces[start : start + size]))
                if term is not None:
                    result[term] = max(result.get(term, 0.0), 4.0)
    symbol_sources = [
        str(metadata.get("title", "")),
        " ".join(str(item) for item in metadata.get("aliases", [])),
        relative.stem,
    ]
    for value in symbol_sources:
        for raw in TOKEN_RE.findall(value):
            for term in sorted(symbol_fragments(raw)):
                result[term] = max(result.get(term, 0.0), 1.5)
    return result


def semantic_fingerprint(metadata: dict[str, object], body: str) -> str:
    """Fingerprint fields and body that can change a relationship judgment."""
    ignored = {"created_at", "updated_at", "verified"}
    semantic_metadata = {
        key: value for key, value in metadata.items() if key not in ignored
    }
    return sha256_text(canonical_json(semantic_metadata) + "\n" + body.strip())


def load_cards(root: Path) -> dict[str, Card]:
    contract = ingest.load_contract(root)
    module = ingest.contract_module()
    knowledge_root = root / "knowledge"
    cards: dict[str, Card] = {}
    for path in sorted(knowledge_root.rglob("*.md")):
        if path.name == "index.md":
            continue
        raw = path.read_text(encoding="utf-8")
        clean = strip_managed(raw)
        metadata, body = module.split_frontmatter(clean)
        if metadata is None:
            raise ValueError(f"missing frontmatter: {path.relative_to(root)}")
        relative = path.relative_to(root)
        issues = contract.validate_card(relative, metadata, body)
        if issues:
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"invalid card {relative}: {details}")
        doc_id = ingest.doc_id(root, path)
        card_relative = path.relative_to(knowledge_root)
        cards[doc_id] = Card(
            doc_id=doc_id,
            path=path,
            profile=contract.derive_card_path(relative).card_type,
            metadata=metadata,
            body=body,
            fingerprint=semantic_fingerprint(metadata, body),
            terms=weighted_terms(metadata, card_relative, body),
            symbols=symbol_terms(metadata, card_relative),
            body_mentions=body_mentions(body),
            tags={str(tag) for tag in metadata.get("tags", [])},
        )
    return cards


def corpus_fingerprint(cards: dict[str, Card]) -> str:
    return sha256_text(canonical_json({doc_id: card.fingerprint for doc_id, card in cards.items()}))


def broad_recall_channels(
    root: Path, cards: dict[str, Card], lexical_limit: int
) -> dict[tuple[str, str], set[str]]:
    """Return broad, auditable recall channels without deciding any relation."""
    channels: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_parent: dict[Path, list[str]] = defaultdict(list)
    path_to_id = {card.path.resolve(): doc_id for doc_id, card in cards.items()}
    knowledge_root = root / "knowledge"
    module = ingest.contract_module()
    symbol_targets: dict[str, list[str]] = defaultdict(list)
    body_mention_frequency: Counter[str] = Counter()
    for doc_id, card in cards.items():
        for symbol in card.symbols:
            symbol_targets[symbol].append(doc_id)
        body_mention_frequency.update(card.body_mentions)
    for doc_id, card in cards.items():
        by_parent[card.path.parent.resolve()].append(doc_id)
        for raw, is_image in module.markdown_targets(card.body):
            if is_image or raw.startswith(("#", "http://", "https://", "mailto:")):
                continue
            clean = unquote(raw.split("#", 1)[0])
            if not clean:
                continue
            target = (
                (knowledge_root / clean.lstrip("/")).resolve()
                if clean.startswith("/")
                else (card.path.parent / clean).resolve()
            )
            target_id = path_to_id.get(target)
            if target_id is not None and target_id != doc_id:
                channels[tuple(sorted((doc_id, target_id)))].add("authored_link")
        for mention in card.body_mentions:
            targets = symbol_targets.get(mention, [])
            if len(targets) > 8 or body_mention_frequency[mention] > 80:
                continue
            for target_id in targets:
                if target_id != doc_id:
                    channels[tuple(sorted((doc_id, target_id)))].add(
                        "body_symbol_mention"
                    )

    # A small directory is normally one documentation/API bundle. Add its siblings to
    # the reading shortlist, but do not infer that a relationship exists.
    maximum_bundle_size = max(lexical_limit, 50)
    for doc_ids in by_parent.values():
        if len(doc_ids) < 2 or len(doc_ids) > maximum_bundle_size:
            continue
        ordered = sorted(doc_ids)
        for index, source in enumerate(ordered):
            for target in ordered[index + 1 :]:
                channels[(source, target)].add("small_bundle_sibling")
    return channels


def candidate_payload(root: Path, cards: dict[str, Card], limit: int) -> dict[str, object]:
    term_postings: dict[str, list[str]] = defaultdict(list)
    tag_postings: dict[str, list[str]] = defaultdict(list)
    for doc_id, card in cards.items():
        for term in card.terms:
            term_postings[term].append(doc_id)
        for tag in card.tags:
            tag_postings[tag].append(doc_id)

    total = len(cards)
    pair_scores: dict[tuple[str, str], float] = defaultdict(float)
    pair_terms: dict[tuple[str, str], set[str]] = defaultdict(set)
    pair_tags: dict[tuple[str, str], set[str]] = defaultdict(set)
    pair_channels = broad_recall_channels(root, cards, limit)

    def score_postings(postings: dict[str, list[str]], is_tag: bool) -> None:
        for token, doc_ids in postings.items():
            frequency = len(doc_ids)
            maximum = 100 if is_tag else 80
            if frequency < 2 or frequency > maximum:
                continue
            idf = math.log((total + 1) / (frequency + 1)) + 1.0
            ordered = sorted(doc_ids)
            for index, source in enumerate(ordered):
                for target in ordered[index + 1 :]:
                    pair = (source, target)
                    if is_tag:
                        pair_scores[pair] += 0.35 * idf
                        pair_tags[pair].add(token)
                    else:
                        weight = min(cards[source].terms[token], cards[target].terms[token])
                        pair_scores[pair] += weight * idf
                        pair_terms[pair].add(token)

    score_postings(term_postings, False)
    score_postings(tag_postings, True)

    per_card: dict[str, list[dict[str, object]]] = defaultdict(list)
    for (source, target), score in pair_scores.items():
        if not pair_terms[(source, target)] and not pair_tags[(source, target)]:
            continue
        item = {
            "score": round(score, 6),
            "shared_terms": sorted(pair_terms[(source, target)]),
            "shared_tags": sorted(pair_tags[(source, target)]),
            "recall_channels": sorted(pair_channels.get((source, target), set()) | {"lexical"}),
        }
        per_card[source].append({"target": target, **item})
        per_card[target].append({"target": source, **item})

    lexical_pairs: set[tuple[str, str]] = set()
    for doc_id in sorted(cards):
        for item in sorted(
            per_card.get(doc_id, []),
            key=lambda item: (-float(item["score"]), str(item["target"])),
        )[:limit]:
            lexical_pairs.add(tuple(sorted((doc_id, str(item["target"])))))

    candidates: dict[str, list[dict[str, object]]] = {}
    for doc_id in sorted(cards):
        selected = {
            str(item["target"]): item
            for item in per_card.get(doc_id, [])
            if tuple(sorted((doc_id, str(item["target"])))) in lexical_pairs
        }
        for pair, channels in pair_channels.items():
            if doc_id not in pair:
                continue
            target = pair[1] if pair[0] == doc_id else pair[0]
            existing = selected.get(target)
            if existing is None:
                selected[target] = {
                    "target": target,
                    "score": 0.0,
                    "shared_terms": sorted(pair_terms.get(pair, set())),
                    "shared_tags": sorted(pair_tags.get(pair, set())),
                    "recall_channels": sorted(channels),
                }
            else:
                existing["recall_channels"] = sorted(
                    set(existing.get("recall_channels", [])) | channels
                )
        candidates[doc_id] = sorted(
            selected.values(),
            key=lambda item: (-float(item["score"]), str(item["target"])),
        )
    return {
        "schema_version": 2,
        "generated_by": "deterministic-broad-recall-v3",
        "corpus_fingerprint": corpus_fingerprint(cards),
        "card_fingerprints": {
            doc_id: card.fingerprint for doc_id, card in sorted(cards.items())
        },
        "term_document_frequencies": {
            term: len(doc_ids) for term, doc_ids in sorted(term_postings.items())
        },
        "lexical_limit_per_card": limit,
        "note": (
            "The lexical limit selects each focal's outgoing lexical shortlist; its incoming "
            "counterparts, authored links, and small-bundle siblings are retained in addition. "
            "Candidates are not accepted graph edges."
        ),
        "candidates": candidates,
    }


def candidates_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    payload = candidate_payload(root, cards, args.limit)
    output = root / "artifacts/graphs/candidates.json"
    ingest.atomic_write(output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    pairs = {
        tuple(sorted((source, str(item["target"]))))
        for source, items in payload["candidates"].items()
        for item in items
    }
    print(f"output={output} cards={len(cards)} candidate_pairs={len(pairs)}")
    return 0


def reset_command(args: argparse.Namespace) -> int:
    """Remove only ignored, reproducible graph artifacts before a full rebuild."""
    root = ingest.resolve_root(args.knowledge_root)
    graph_root = root / "artifacts/graphs"
    targets = [
        graph_root / "adjudication",
        graph_root / "judgment_shards",
        graph_root / "reviews",
        graph_root / "candidates.json",
        graph_root / "edge_judgments.json",
        graph_root / "graph.json",
        graph_root / "graph.html",
    ]
    removed = 0
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
            removed += 1
        elif target.is_file():
            target.unlink()
            removed += 1
    print(f"graph_root={graph_root} removed_targets={removed}")
    return 0


def load_candidates(root: Path, cards: dict[str, Card]) -> dict[str, object]:
    path = root / "artifacts/graphs/candidates.json"
    if not path.is_file():
        raise ValueError("candidate artifact is missing; run candidates first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("corpus_fingerprint") != corpus_fingerprint(cards):
        raise ValueError("candidate artifact is stale for the current corpus")
    return payload


def judgment_path(root: Path) -> Path:
    return root / "artifacts/graphs/edge_judgments.json"


def normalize_agent_relation(
    cards: dict[str, Card], focal_id: str, target_id: str, requested: str
) -> tuple[str, str, str]:
    """Normalize ontology direction without deciding whether the relation is true."""
    focal = cards[focal_id]
    target = cards[target_id]
    profiles = {focal.profile, target.profile}
    if profiles == {"runbooks", "apis"}:
        source, destination = (focal, target) if focal.profile == "runbooks" else (target, focal)
        return source.doc_id, "exemplifies", destination.doc_id
    if profiles == {"guides", "apis"}:
        source, destination = (focal, target) if focal.profile == "guides" else (target, focal)
        return source.doc_id, "explains", destination.doc_id
    source, destination = sorted((focal_id, target_id))
    if focal.profile == target.profile:
        if requested not in {"same_topic", "related"}:
            raise ValueError(
                f"same-profile Agent judgment must choose same_topic or related: {(focal_id, target_id)}"
            )
        return source, requested, destination
    return source, "related", destination


def review_card_payload(root: Path, card: Card) -> dict[str, object]:
    description = " ".join(str(card.metadata.get("description", "")).split())
    sources = [
        str(source.get("resource", ""))
        for source in card.metadata.get("sources", [])
        if isinstance(source, dict) and str(source.get("resource", "")).strip()
    ]
    return {
        "id": card.doc_id,
        "path": card.path.relative_to(root).as_posix(),
        "fingerprint": card.fingerprint,
        "profile": card.profile,
        "type": card.metadata.get("type"),
        "title": card.title,
        "description": description,
        "tags": sorted(card.tags),
        "sources": sources,
        "excerpt": card.body.strip()[:REVIEW_EXCERPT_CHARS],
    }


def shard_root(root: Path) -> Path:
    return root / "artifacts/graphs/judgment_shards"


def make_shards_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    candidates = load_candidates(root, cards)
    candidate_fp = sha256_text(canonical_json(candidates))
    shard_count = min(args.count, len(cards))
    buckets: list[list[str]] = [[] for _ in range(shard_count)]
    for index, doc_id in enumerate(sorted(cards)):
        buckets[index % shard_count].append(doc_id)
    output_root = shard_root(root)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_shards: list[dict[str, object]] = []
    expected_outputs: set[Path] = set()
    for index, focal_ids in enumerate(buckets):
        shard_id = f"shard-{index:03d}"
        focals: list[dict[str, object]] = []
        for focal_id in focal_ids:
            candidate_items: list[dict[str, object]] = []
            for item in candidates["candidates"].get(focal_id, []):
                target_id = str(item["target"])
                target = review_card_payload(root, cards[target_id])
                provisional = normalize_agent_relation(
                    cards, focal_id, target_id, "same_topic"
                )[1]
                candidate_items.append(
                    {
                        **target,
                        "recall_score": item["score"],
                        "recall_hints": {
                            "shared_terms": item.get("shared_terms", []),
                            "shared_tags": item.get("shared_tags", []),
                            "channels": item.get("recall_channels", []),
                        },
                        "provisional_relation": provisional,
                    }
                )
            candidate_set_fp = sha256_text(
                canonical_json(
                    {
                        "focal": cards[focal_id].fingerprint,
                        "targets": [
                            (item["id"], item["fingerprint"]) for item in candidate_items
                        ],
                    }
                )
            )
            focals.append(
                {
                    "focal": review_card_payload(root, cards[focal_id]),
                    "candidate_set_fingerprint": candidate_set_fp,
                    "candidates": candidate_items,
                }
            )
        payload: dict[str, object] = {
            "schema_version": 2,
            "shard_id": shard_id,
            "corpus_fingerprint": corpus_fingerprint(cards),
            "candidate_fingerprint": candidate_fp,
            "instructions": (
                "Recall hints only locate candidates. Read each focal and shortlisted candidate "
                "file in full, excluding the managed related block, then keep only relations "
                "that materially help understand, use, diagnose, or verify the focal knowledge. "
                "Every kept or explicit rejected decision must provide evidence.anchors keyed "
                "by both Concept IDs and quoted verbatim from each authored card body, a bridge "
                "containing both anchors, and a scope_note. Omission means abstain; use rejected "
                "only after reading both complete cards. "
                "The shortlist is not a closed graph boundary: when the focal text reveals a "
                "material relation to another current card, submit it as an explicit "
                "fingerprinted agent_discovered decision."
            ),
            "focals": focals,
        }
        shard_fp = sha256_text(canonical_json(payload))
        payload["shard_fingerprint"] = shard_fp
        output = output_root / f"{shard_id}.json"
        expected_outputs.add(output)
        ingest.atomic_write(output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        manifest_shards.append(
            {
                "shard_id": shard_id,
                "path": output.relative_to(root).as_posix(),
                "shard_fingerprint": shard_fp,
                "focal_ids": focal_ids,
            }
        )
    manifest = {
        "schema_version": 2,
        "corpus_fingerprint": corpus_fingerprint(cards),
        "candidate_fingerprint": candidate_fp,
        "shards": manifest_shards,
    }
    output = output_root / "manifest.json"
    ingest.atomic_write(output, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for stale in output_root.glob("shard-*.json"):
        if stale not in expected_outputs:
            stale.unlink()
    print(
        f"output={output} shards={shard_count} focals={len(cards)} "
        f"directed_candidates={sum(len(items) for items in candidates['candidates'].values())}"
    )
    return 0


def load_shard_manifest(root: Path) -> dict[str, object]:
    path = shard_root(root) / "manifest.json"
    if not path.is_file():
        raise ValueError("judgment shard manifest is missing; run make-shards first")
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_command(args: argparse.Namespace) -> int:
    """Build the semantic cache exclusively from complete Agent review outputs."""
    root = ingest.resolve_root(args.knowledge_root)
    # A failed aggregation must not leave a same-corpus cache available to finalize.
    judgment_path(root).unlink(missing_ok=True)
    conflict_path = root / "artifacts/graphs/adjudication/conflicts.json"
    conflict_path.unlink(missing_ok=True)
    cards = load_cards(root)
    candidates = load_candidates(root, cards)
    manifest = load_shard_manifest(root)
    current_corpus = corpus_fingerprint(cards)
    candidate_fp = sha256_text(canonical_json(candidates))
    if manifest.get("corpus_fingerprint") != current_corpus:
        raise ValueError("judgment shard manifest is stale for the current corpus")
    if manifest.get("candidate_fingerprint") != candidate_fp:
        raise ValueError("judgment shard manifest is stale for the current candidates")
    expected_shards = {str(item["shard_id"]): item for item in manifest["shards"]}
    seen_shards: set[str] = set()
    agent_judges: set[str] = set()
    pair_reviews: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    pair_rejections: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    reviewed_focals: set[str] = set()
    for value in args.input:
        source_path = Path(value).resolve()
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 2:
            raise ValueError(f"unsupported review output schema: {source_path}")
        shard_id = str(payload.get("shard_id", ""))
        expected = expected_shards.get(shard_id)
        if expected is None or shard_id in seen_shards:
            raise ValueError(f"unexpected or duplicate review shard: {shard_id}")
        if payload.get("shard_fingerprint") != expected["shard_fingerprint"]:
            raise ValueError(f"review output does not match shard content: {source_path}")
        judge = str(payload.get("judge", "")).strip()
        if not judge or "deterministic" in judge.lower():
            raise ValueError(f"review output requires a non-deterministic Agent judge: {source_path}")
        agent_judges.add(judge)
        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError(f"review output must contain results: {source_path}")
        expected_focals = set(expected["focal_ids"])
        result_focals = {str(result.get("focal_id", "")) for result in results}
        if result_focals != expected_focals or len(results) != len(result_focals):
            raise ValueError(f"review output does not cover every focal exactly once: {source_path}")
        packet = json.loads((root / str(expected["path"])).read_text(encoding="utf-8"))
        packet_focals = {
            str(item["focal"]["id"]): item for item in packet["focals"]
        }
        for result in results:
            focal_id = str(result["focal_id"])
            focal_packet = packet_focals[focal_id]
            if result.get("candidate_set_fingerprint") != focal_packet["candidate_set_fingerprint"]:
                raise ValueError(f"reviewed focal candidate set is stale: {focal_id}")
            needs_adjudication = result.get("needs_adjudication")
            if not isinstance(needs_adjudication, list):
                raise ValueError(f"reviewed focal needs_adjudication must be a list: {focal_id}")
            if needs_adjudication:
                raise ValueError(f"reviewed focal still needs adjudication: {focal_id}")
            allowed_targets = {
                str(item["id"]): item for item in focal_packet["candidates"]
            }
            kept = result.get("kept", [])
            if not isinstance(kept, list):
                raise ValueError(f"reviewed focal kept must be a list: {focal_id}")
            rejected = result.get("rejected", [])
            if not isinstance(rejected, list):
                raise ValueError(f"reviewed focal rejected must be a list: {focal_id}")
            decided_targets: set[str] = set()
            for decision in kept:
                target_id = str(decision.get("target_id", ""))
                if target_id in decided_targets:
                    raise ValueError(f"reviewed focal repeats a target decision: {(focal_id, target_id)}")
                decided_targets.add(target_id)
                candidate_item = allowed_targets.get(target_id)
                if candidate_item is None:
                    discovered = decision.get("agent_discovered") is True
                    target_card = cards.get(target_id)
                    if (
                        not discovered
                        or target_card is None
                        or target_id == focal_id
                        or decision.get("target_fingerprint") != target_card.fingerprint
                    ):
                        raise ValueError(
                            "Agent accepted a non-candidate pair without a current explicit "
                            f"discovery: {(focal_id, target_id)}"
                        )
                    candidate_item = {
                        "recall_score": None,
                        "recall_hints": {"channels": ["agent_discovered"]},
                    }
                elif decision.get("agent_discovered") is True:
                    raise ValueError(
                        "agent_discovered is only valid outside the current candidate set: "
                        f"{(focal_id, target_id)}"
                    )
                requested = str(decision.get("relation", ""))
                source, relation, target = normalize_agent_relation(
                    cards, focal_id, target_id, requested
                )
                reason, evidence = validate_agent_evidence(
                    decision.get("reason", ""),
                    decision.get("evidence"),
                    tuple(sorted((focal_id, target_id))),
                    (focal_id, target_id),
                    card_bodies={
                        focal_id: cards[focal_id].body,
                        target_id: cards[target_id].body,
                    },
                )
                decision_judge = str(decision.get("judge", judge)).strip()
                if not decision_judge or "deterministic" in decision_judge.lower():
                    raise ValueError(
                        f"Agent decision requires a non-deterministic judge: {(focal_id, target_id)}"
                    )
                confidence = str(decision.get("confidence", "medium"))
                strength = str(decision.get("strength", "supporting"))
                if confidence not in {"high", "medium", "low"}:
                    raise ValueError(f"invalid Agent confidence: {(focal_id, target_id)}")
                if strength not in {"direct", "supporting", "contextual"}:
                    raise ValueError(f"invalid Agent relation strength: {(focal_id, target_id)}")
                pair_reviews[tuple(sorted((source, target)))].append(
                    {
                        "source": source,
                        "relation": relation,
                        "target": target,
                        "reason": reason,
                        "judge": decision_judge,
                        "confidence": confidence,
                        "strength": strength,
                        "evidence": evidence,
                        "recall_score": candidate_item["recall_score"],
                        "recall_hints": candidate_item["recall_hints"],
                        "reviewed_from": focal_id,
                    }
                )
            for decision in rejected:
                target_id = str(decision.get("target_id", ""))
                if target_id in decided_targets:
                    raise ValueError(f"reviewed focal repeats a target decision: {(focal_id, target_id)}")
                decided_targets.add(target_id)
                if target_id not in allowed_targets:
                    raise ValueError(
                        f"Agent rejected a target outside the current candidate set: {(focal_id, target_id)}"
                    )
                pair = tuple(sorted((focal_id, target_id)))
                reason, evidence = validate_agent_evidence(
                    decision.get("reason", ""),
                    decision.get("evidence"),
                    pair,
                    (focal_id, target_id, "rejected"),
                    allow_negative_bridge=True,
                    card_bodies={endpoint: cards[endpoint].body for endpoint in pair},
                )
                decision_judge = str(decision.get("judge", judge)).strip()
                if not decision_judge or "deterministic" in decision_judge.lower():
                    raise ValueError(
                        f"Agent rejection requires a non-deterministic judge: {(focal_id, target_id)}"
                    )
                pair_rejections[pair].append(
                    {
                        "focal": focal_id,
                        "target": target_id,
                        "reason": reason,
                        "judge": decision_judge,
                        "evidence": evidence,
                    }
                )
            reviewed_focals.add(focal_id)
        seen_shards.add(shard_id)
    missing_shards = sorted(set(expected_shards) - seen_shards)
    if missing_shards:
        raise ValueError(f"missing Agent review shards: {', '.join(missing_shards[:5])}")
    if len(cards) > 1 and len(agent_judges) < 2:
        raise ValueError("full relationship review requires at least two independent Agent judges")

    relation_conflicts = {
        pair
        for pair, reviews in pair_reviews.items()
        if len({str(review["relation"]) for review in reviews}) > 1
    }
    existence_conflicts = set(pair_reviews) & set(pair_rejections)
    conflicting_pairs = relation_conflicts | existence_conflicts
    adjudications: dict[tuple[str, str], dict[str, object]] = {}
    if conflicting_pairs:
        conflict_packet: dict[str, object] = {
            "schema_version": 2,
            "corpus_fingerprint": current_corpus,
            "instructions": (
                "Read both complete cards for every pair and decide accept true or false. When "
                "accepted, choose same_topic only when both cards share one core object, contract, "
                "or troubleshooting decision; otherwise choose related. Prior decisions and recall "
                "hints are context, not evidence. Every decision must use bilateral anchors, a "
                "bridge containing both anchors, and a scope_note. The adjudicator must not have "
                "judged this pair."
            ),
            "conflicts": [
                {
                    "pair": list(pair),
                    "kind": (
                        "existence_and_relation_type"
                        if pair in existence_conflicts and pair in relation_conflicts
                        else "existence"
                        if pair in existence_conflicts
                        else "relation_type"
                    ),
                    "left": review_card_payload(root, cards[pair[0]]),
                    "right": review_card_payload(root, cards[pair[1]]),
                    "reviews": pair_reviews[pair],
                    "rejections": pair_rejections.get(pair, []),
                }
                for pair in sorted(conflicting_pairs)
            ],
        }
        conflict_fp = sha256_text(canonical_json(conflict_packet))
        conflict_packet["conflict_fingerprint"] = conflict_fp
        ingest.atomic_write(
            conflict_path,
            json.dumps(conflict_packet, ensure_ascii=False, indent=2) + "\n",
        )
        if not args.adjudication:
            raise ValueError(
                f"{len(conflicting_pairs)} Agent decision conflicts require adjudication; "
                f"packet={conflict_path}"
            )
        for value in args.adjudication:
            adjudication_path = Path(value).resolve()
            adjudication = json.loads(adjudication_path.read_text(encoding="utf-8"))
            if adjudication.get("schema_version") != 2:
                raise ValueError("unsupported conflict adjudication schema")
            if adjudication.get("conflict_fingerprint") != conflict_fp:
                raise ValueError("Agent adjudication does not match the current conflict packet")
            adjudicator = str(adjudication.get("judge", "")).strip()
            if not adjudicator or "deterministic" in adjudicator.lower():
                raise ValueError("conflict adjudication requires a non-deterministic Agent judge")
            decisions = adjudication.get("decisions")
            if not isinstance(decisions, list):
                raise ValueError("conflict adjudication must contain decisions")
            for decision in decisions:
                pair = tuple(
                    sorted((str(decision.get("left", "")), str(decision.get("right", ""))))
                )
                if pair not in conflicting_pairs or pair in adjudications:
                    raise ValueError(f"unexpected or duplicate conflict adjudication: {pair}")
                original_judges = {
                    str(item["judge"])
                    for item in pair_reviews[pair] + pair_rejections.get(pair, [])
                }
                if adjudicator in original_judges:
                    raise ValueError(f"conflict adjudicator must be independent for pair: {pair}")
                accept = decision.get("accept")
                if not isinstance(accept, bool):
                    raise ValueError(f"conflict adjudication requires boolean accept: {pair}")
                reason, evidence = validate_agent_evidence(
                    decision.get("reason", ""),
                    decision.get("evidence"),
                    pair,
                    (pair, "adjudication"),
                    allow_negative_bridge=not accept,
                    card_bodies={endpoint: cards[endpoint].body for endpoint in pair},
                )
                confidence = str(decision.get("confidence", "medium"))
                strength = str(decision.get("strength", "supporting"))
                if confidence not in {"high", "medium", "low"}:
                    raise ValueError(f"invalid adjudication confidence: {pair}")
                if strength not in {"direct", "supporting", "contextual"}:
                    raise ValueError(f"invalid adjudication strength: {pair}")
                adjudicated: dict[str, object] = {
                    "accept": accept,
                    "reason": reason,
                    "judge": adjudicator,
                    "confidence": confidence,
                    "strength": strength,
                    "evidence": evidence,
                }
                if accept:
                    source, relation, target = normalize_agent_relation(
                        cards, pair[0], pair[1], str(decision.get("relation", ""))
                    )
                    adjudicated.update(
                        {"source": source, "relation": relation, "target": target}
                    )
                adjudications[pair] = adjudicated
        if set(adjudications) != set(conflicting_pairs):
            raise ValueError("conflict adjudication does not cover every conflicting pair exactly once")
    elif args.adjudication:
        raise ValueError("conflict adjudication was supplied but no Agent decision conflicts exist")

    judgments: list[dict[str, object]] = []
    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    strength_rank = {"contextual": 0, "supporting": 1, "direct": 2}
    for pair, reviews in sorted(pair_reviews.items()):
        if pair in adjudications and adjudications[pair]["accept"] is False:
            continue
        relations = {str(review["relation"]) for review in reviews}
        if pair not in adjudications:
            selected = dict(
                min(
                    reviews,
                    key=lambda review: (
                        -confidence_rank[str(review["confidence"])],
                        -strength_rank[str(review["strength"])],
                        str(review["judge"]),
                        str(review["reviewed_from"]),
                        str(review["reason"]),
                    ),
                )
            )
        else:
            selected = dict(adjudications[pair])
            selected.pop("accept", None)
            recall_scores = [
                float(review["recall_score"])
                for review in reviews
                if review.get("recall_score") is not None
            ]
            selected["recall_score"] = max(recall_scores) if recall_scores else None
            selected["recall_hints"] = {
                "adjudicated_conflict": sorted(relations),
            }
        selected["judge"] = sorted(
            {str(review["judge"]) for review in reviews}
            | set(
                [str(adjudications[pair]["judge"])] if pair in adjudications else []
            )
        )
        selected["reviewed_from"] = sorted(
            {str(review["reviewed_from"]) for review in reviews}
        )
        judgments.append(selected)
    cache = {
        "schema_version": 2,
        "generated_by": "multi-subagent-semantic-review-v2",
        "corpus_fingerprint": current_corpus,
        "candidate_fingerprint": candidate_fp,
        "card_fingerprints": {
            doc_id: card.fingerprint for doc_id, card in sorted(cards.items())
        },
        "reviewed_focals": sorted(reviewed_focals),
        "review_shards": sorted(seen_shards),
        "review_judges": sorted(agent_judges),
        "judgments": judgments,
    }
    output = judgment_path(root)
    ingest.atomic_write(output, json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
    print(
        f"output={output} reviewed_focals={len(reviewed_focals)} "
        f"agent_edges={len(judgments)}"
    )
    return 0


def validate_judgments(root: Path, cards: dict[str, Card]) -> dict[str, object]:
    path = judgment_path(root)
    if not path.is_file():
        raise ValueError("edge judgment cache is missing; run Agent review and aggregate first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("generated_by") != "multi-subagent-semantic-review-v2":
        raise ValueError("edge judgment cache was not produced by multi-subagent review")
    if payload.get("corpus_fingerprint") != corpus_fingerprint(cards):
        raise ValueError("edge judgment cache is stale for the current corpus")
    candidates = load_candidates(root, cards)
    if payload.get("candidate_fingerprint") != sha256_text(canonical_json(candidates)):
        raise ValueError("edge judgment cache is stale for the current candidates")
    expected_fingerprints = {
        doc_id: card.fingerprint for doc_id, card in sorted(cards.items())
    }
    if payload.get("card_fingerprints") != expected_fingerprints:
        raise ValueError("edge judgment card fingerprints are stale")
    if set(payload.get("reviewed_focals", [])) != set(cards):
        raise ValueError("edge judgment cache does not cover every current focal card")
    review_judges = payload.get("review_judges")
    if (
        len(cards) > 1
        and (
            not isinstance(review_judges, list)
            or len(set(str(judge) for judge in review_judges)) < 2
        )
    ):
        raise ValueError("edge judgment cache requires at least two Agent review identities")
    seen: set[tuple[str, str, str]] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for item in payload.get("judgments", []):
        source = str(item.get("source", ""))
        target = str(item.get("target", ""))
        relation = str(item.get("relation", ""))
        key = (source, relation, target)
        if source not in cards or target not in cards:
            raise ValueError(f"judgment endpoint does not exist: {key}")
        if source == target:
            raise ValueError(f"self relation is not allowed: {key}")
        if relation not in ALLOWED_RELATIONS - {"links_to", "part_of"}:
            raise ValueError(f"unsupported judged relation: {key}")
        if normalize_agent_relation(cards, source, target, relation) != key:
            raise ValueError(f"judged relation has invalid type or direction: {key}")
        if key in seen:
            raise ValueError(f"duplicate judged relation: {key}")
        pair = tuple(sorted((source, target)))
        if pair in seen_pairs:
            raise ValueError(f"multiple judged relations for one pair: {pair}")
        judges = item.get("judge")
        if (
            not isinstance(judges, list)
            or not judges
            or any(not isinstance(judge, str) or not judge.strip() for judge in judges)
        ):
            raise ValueError(f"judged relation requires Agent identities: {key}")
        validate_agent_evidence(
            item.get("reason", ""),
            item.get("evidence"),
            pair,
            key,
            card_bodies={endpoint: cards[endpoint].body for endpoint in pair},
        )
        seen.add(key)
        seen_pairs.add(pair)
    return payload


def related_lines(card: Card, cards: dict[str, Card], judgments: dict[str, object]) -> list[str]:
    items: list[tuple[str, Card, str]] = []
    for edge in judgments["judgments"]:
        source = str(edge["source"])
        target = str(edge["target"])
        if card.doc_id == source:
            items.append((str(edge["relation"]), cards[target], str(edge["reason"])))
        elif card.doc_id == target:
            items.append((str(edge["relation"]), cards[source], str(edge["reason"])))
    items.sort(key=lambda value: (value[0], value[1].title, value[1].doc_id))
    lines: list[str] = []
    for relation, other, reason in items:
        relative = os.path.relpath(other.path, card.path.parent).replace(os.sep, "/")
        href = quote(relative, safe="/._-")
        # Review reasons are evidence text, not authored navigation.  A reviewer may
        # quote Markdown links or table rows from either endpoint; preserving that
        # syntax would resolve links relative to the receiving card or make the
        # single-line navigation item look like a collapsed Markdown table.  Keep
        # the evidence readable while rendering it as single-line plain text.
        rendered_reason = " ".join(reason.split()).translate(
            str.maketrans({"[": "［", "]": "］", "|": "｜"})
        )
        lines.append(f"- [{other.title}]({href})（`{relation}`）：{rendered_reason}")
    return lines


def desired_card_text(card: Card, cards: dict[str, Card], judgments: dict[str, object]) -> str:
    clean = strip_managed(card.path.read_text(encoding="utf-8")).rstrip()
    lines = related_lines(card, cards, judgments)
    if not lines:
        return clean + "\n"
    block = "\n".join([MANAGED_START, "## 相关", "", *lines, MANAGED_END])
    return clean + "\n\n" + block + "\n"


def inject_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    judgments = validate_judgments(root, cards)
    changed = 0
    for card in cards.values():
        expected = desired_card_text(card, cards, judgments)
        actual = card.path.read_text(encoding="utf-8")
        if actual != expected:
            changed += 1
            if not args.check:
                ingest.atomic_write(card.path, expected)
    print(f"checked_cards={len(cards)} changed_cards={changed}")
    return 1 if args.check and changed else 0


def local_markdown_targets(card: Card, knowledge_root: Path) -> list[Path]:
    module = ingest.contract_module()
    targets: list[Path] = []
    for raw, is_image in module.markdown_targets(card.body):
        if is_image or raw.startswith(("#", "http://", "https://", "mailto:")):
            continue
        clean = unquote(raw.split("#", 1)[0])
        if not clean:
            continue
        target = (
            (knowledge_root / clean.lstrip("/")).resolve()
            if clean.startswith("/")
            else (card.path.parent / clean).resolve()
        )
        try:
            target.relative_to(knowledge_root)
        except ValueError:
            continue
        if target.is_file() and target.suffix == ".md":
            targets.append(target)
    return targets


def index_id(root: Path, path: Path) -> str:
    return ingest.doc_id(root, path)


def graph_payload(root: Path, cards: dict[str, Card], judgments: dict[str, object]) -> dict[str, object]:
    knowledge_root = root / "knowledge"
    nodes: list[dict[str, object]] = []
    for card in cards.values():
        nodes.append(
            {
                "id": card.doc_id,
                "kind": "concept",
                "type": card.metadata.get("type"),
                "profile": card.profile,
                "title": card.title,
                "status": card.metadata.get("status"),
                "tags": card.metadata.get("tags", []),
            }
        )
    indexes = sorted(knowledge_root.rglob("index.md"))
    index_ids = {path.resolve(): index_id(root, path) for path in indexes}
    for path in indexes:
        nodes.append(
            {
                "id": index_ids[path.resolve()],
                "kind": "index",
                "title": path.parent.name if path.parent != knowledge_root else "knowledge",
            }
        )

    edges: dict[tuple[str, str, str], dict[str, object]] = {}
    path_to_id = {card.path.resolve(): card.doc_id for card in cards.values()} | index_ids
    for card in cards.values():
        for target_path in local_markdown_targets(card, knowledge_root):
            target_id = path_to_id.get(target_path.resolve())
            if target_id is not None and target_id != card.doc_id:
                key = (card.doc_id, "links_to", target_id)
                edges[key] = {"source": key[0], "relation": key[1], "target": key[2]}

    for item in judgments["judgments"]:
        key = (str(item["source"]), str(item["relation"]), str(item["target"]))
        edges[key] = {
            "source": key[0],
            "relation": key[1],
            "target": key[2],
            "reason": item["reason"],
            "judge": item["judge"],
            "confidence": item["confidence"],
            "strength": item["strength"],
            "evidence": item.get("evidence", {}),
            "recall_score": item.get("recall_score"),
            "recall_hints": item.get("recall_hints", {}),
        }

    for path, child_id in sorted(path_to_id.items(), key=lambda item: item[1]):
        if path.name == "index.md":
            if path.parent == knowledge_root:
                continue
            parent_path = path.parent.parent / "index.md"
        else:
            parent_path = path.parent / "index.md"
        parent_id = index_ids.get(parent_path.resolve())
        if parent_id is None:
            raise ValueError(f"missing parent index for graph node: {child_id}")
        key = (child_id, "part_of", parent_id)
        edges[key] = {"source": key[0], "relation": key[1], "target": key[2]}

    ordered_nodes = sorted(nodes, key=lambda item: str(item["id"]))
    ordered_edges = [edges[key] for key in sorted(edges)]
    relation_counts = Counter(str(edge["relation"]) for edge in ordered_edges)
    return {
        "schema_version": 2,
        "generated_from": [
            "governed concepts and indexes under knowledge/",
            "authored Markdown links excluding managed related blocks",
            "ignored Agent judgments under artifacts/graphs/",
        ],
        "corpus_fingerprint": corpus_fingerprint(cards),
        "nodes": ordered_nodes,
        "edges": ordered_edges,
        "counts": {
            "nodes": len(ordered_nodes),
            "edges": len(ordered_edges),
            "relations": dict(sorted(relation_counts.items())),
        },
    }


def build_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    judgments = validate_judgments(root, cards)
    payload = graph_payload(root, cards, judgments)
    output = root / "artifacts/graphs/graph.json"
    ingest.atomic_write(output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"output={output} nodes={len(payload['nodes'])} edges={len(payload['edges'])}")
    return 0


def render_graph_html(graph: dict[str, object]) -> str:
    rows = []
    for edge in graph["edges"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(edge['source']))}</td>"
            f"<td>{html.escape(str(edge['relation']))}</td>"
            f"<td>{html.escape(str(edge['target']))}</td>"
            "</tr>"
        )
    return """<!doctype html>
<meta charset="utf-8">
<title>CANNBot Knowledge Graph</title>
<style>
body{font:14px system-ui;margin:2rem;color:#1f2937}input{width:100%%;padding:.7rem}
table{border-collapse:collapse;width:100%%;margin-top:1rem}th,td{padding:.45rem;border:1px solid #ddd;text-align:left}
</style>
<h1>CANNBot Knowledge Graph</h1>
<p>nodes=%s edges=%s</p>
<input id="q" placeholder="Filter source, relation, or target">
<table><thead><tr><th>Source</th><th>Relation</th><th>Target</th></tr></thead><tbody>%s</tbody></table>
<script>q.oninput=()=>{for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.innerText.toLowerCase().includes(q.value.toLowerCase())}</script>
""" % (len(graph["nodes"]), len(graph["edges"]), "".join(rows))


def viz_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    graph_path = root / "artifacts/graphs/graph.json"
    if not graph_path.is_file():
        raise ValueError("graph artifact is missing; run build first")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    page = render_graph_html(graph)
    output = root / "artifacts/graphs/graph.html"
    ingest.atomic_write(output, page)
    print(f"output={output}")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    judgments = validate_judgments(root, cards)
    expected = graph_payload(root, cards, judgments)
    graph_path = root / "artifacts/graphs/graph.json"
    if not graph_path.is_file():
        raise ValueError("graph artifact is missing; run build first")
    actual = json.loads(graph_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError("graph artifact is stale or non-deterministic")
    html_path = root / "artifacts/graphs/graph.html"
    if not html_path.is_file():
        raise ValueError("graph visualization is missing; run viz first")
    if html_path.read_text(encoding="utf-8") != render_graph_html(actual):
        raise ValueError("graph visualization is stale or non-deterministic")
    node_ids = {str(node["id"]) for node in actual["nodes"]}
    for edge in actual["edges"]:
        if edge["source"] not in node_ids or edge["target"] not in node_ids:
            raise ValueError(f"graph edge has a missing endpoint: {edge}")
        if edge["relation"] not in ALLOWED_RELATIONS:
            raise ValueError(f"graph edge has an unsupported relation: {edge}")
    stale_blocks = [
        card.doc_id
        for card in cards.values()
        if card.path.read_text(encoding="utf-8") != desired_card_text(card, cards, judgments)
    ]
    if stale_blocks:
        raise ValueError(f"managed related blocks are stale: {', '.join(stale_blocks[:5])}")
    print(
        f"verified nodes={len(actual['nodes'])} edges={len(actual['edges'])} "
        f"managed_cards={sum(bool(related_lines(card, cards, judgments)) for card in cards.values())}"
    )
    return 0


def related_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    judgments = validate_judgments(root, cards)
    card = cards.get(args.doc_id)
    if card is None:
        raise ValueError(f"unknown Concept ID: {args.doc_id}")
    lines = related_lines(card, cards, judgments)
    if not lines:
        print("no accepted semantic relations")
    else:
        print("\n".join(lines))
    return 0


def explain_command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    cards = load_cards(root)
    judgments = validate_judgments(root, cards)
    matches = [
        edge
        for edge in judgments["judgments"]
        if {str(edge["source"]), str(edge["target"])} == {args.left, args.right}
    ]
    if not matches:
        print("no accepted semantic relation")
        return 1
    print(json.dumps(matches, ensure_ascii=False, indent=2))
    return 0


def finalize_command(args: argparse.Namespace) -> int:
    # Validate and render ignored artifacts before mutating any tracked knowledge card.
    build_command(args)
    viz_command(args)
    inject_command(args)
    return verify_command(args)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    sub = result.add_subparsers(dest="command", required=True)
    candidates = sub.add_parser("candidates", help="recall bounded semantic edge candidates")
    candidates.add_argument("--limit", type=int, default=DEFAULT_CANDIDATES_PER_CARD)
    candidates.set_defaults(handler=candidates_command)
    reset = sub.add_parser("reset", help="remove ignored graph artifacts before full rebuild")
    reset.set_defaults(handler=reset_command)
    shards = sub.add_parser("make-shards", help="build stable focal packets for Agent review")
    shards.add_argument("--count", type=int, default=DEFAULT_SHARD_COUNT)
    shards.set_defaults(handler=make_shards_command)
    aggregate = sub.add_parser("aggregate", help="aggregate complete Agent review shards")
    aggregate.add_argument("--input", action="append", required=True)
    aggregate.add_argument("--adjudication", action="append", default=[])
    aggregate.set_defaults(handler=aggregate_command)
    inject = sub.add_parser("inject", help="synchronize managed related blocks")
    inject.add_argument("--check", action="store_true")
    inject.set_defaults(handler=inject_command)
    build = sub.add_parser("build", help="synthesize the complete local graph")
    build.set_defaults(handler=build_command)
    viz = sub.add_parser("viz", help="render a local searchable HTML edge view")
    viz.set_defaults(handler=viz_command)
    verify = sub.add_parser("verify", help="verify cache, graph, and managed blocks")
    verify.set_defaults(handler=verify_command)
    related = sub.add_parser("related", help="show accepted relations for one Concept")
    related.add_argument("doc_id")
    related.set_defaults(handler=related_command)
    explain = sub.add_parser("explain", help="show the judgment evidence for one pair")
    explain.add_argument("left")
    explain.add_argument("right")
    explain.set_defaults(handler=explain_command)
    finalize = sub.add_parser("finalize", help="build, visualize, inject, and verify Agent edges")
    finalize.set_defaults(handler=finalize_command, check=False)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        if getattr(args, "limit", 1) < 1 or getattr(args, "count", 1) < 1:
            raise ValueError("limits must be positive")
        return args.handler(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
