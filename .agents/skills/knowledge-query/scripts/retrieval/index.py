"""Persistent deterministic search index for the governed knowledge bundle."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .root import repository_state, sha256_file


INDEX_VERSION = 1
INDEX_SCHEMA = "cannbot-knowledge-index.v1"
INDEX_RELATIVE_PATH = Path("artifacts/indexes/knowledge.sqlite3")
TOKEN_RE = re.compile(r"[a-zA-Z0-9_+./:-]+|[\u4e00-\u9fff]{2,}")
GOVERNANCE_INPUTS = (
    "governance/contracts/knowledge.py",
    "governance/schemas/frontmatter.schema.json",
    "governance/schemas/profiles.yaml",
    "governance/schemas/registries.yaml",
)


@dataclass(frozen=True)
class IndexedCard:
    doc_id: int
    path: str
    relative_path: str
    domain: str
    technology: str | None
    profile: str
    metadata: dict[str, Any]
    card_lines: int
    card_sha256: str


def index_path(root: Path) -> Path:
    return root / INDEX_RELATIVE_PATH


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(entries: Iterable[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for path, value in sorted(entries):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def governance_fingerprint(root: Path) -> str:
    entries = []
    for relative in GOVERNANCE_INPUTS:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"missing index governance input: {relative}")
        entries.append((relative, sha256_file(path)))
    return _fingerprint(entries)


def card_fingerprint(metadata: dict[str, Any], body: str) -> str:
    return hashlib.sha256(f"{_canonical_json(metadata)}\n{body}".encode("utf-8")).hexdigest()


def token_counts(value: str) -> Counter[str]:
    result: Counter[str] = Counter()
    for token in TOKEN_RE.findall(value.lower()):
        result[token] += 1
        if re.fullmatch(r"[\u4e00-\u9fff]{3,}", token):
            for offset in range(len(token) - 1):
                result[token[offset : offset + 2]] += 1
    return result


def query_tokens(value: str) -> list[str]:
    return list(token_counts(value))


def _load_contract(root: Path):
    import sys

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from governance.contracts.knowledge import Contract, split_frontmatter

    return Contract(root), split_frontmatter


def _card_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in (root / "knowledge").rglob("*.md")
        if path.name != "index.md"
    )


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE manifest (
            relative_path TEXT PRIMARY KEY,
            size INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            file_sha256 TEXT NOT NULL
        );
        CREATE TABLE documents (
            doc_id INTEGER PRIMARY KEY,
            concept_id TEXT NOT NULL UNIQUE,
            relative_path TEXT NOT NULL UNIQUE,
            domain TEXT NOT NULL,
            technology TEXT,
            profile TEXT NOT NULL,
            okf_type TEXT NOT NULL,
            status TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            body TEXT NOT NULL,
            search_text TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            card_lines INTEGER NOT NULL,
            card_sha256 TEXT NOT NULL
        );
        CREATE TABLE postings (
            term TEXT NOT NULL,
            doc_id INTEGER NOT NULL,
            title_tf INTEGER NOT NULL,
            description_tf INTEGER NOT NULL,
            tags_tf INTEGER NOT NULL,
            aliases_tf INTEGER NOT NULL,
            body_tf INTEGER NOT NULL,
            PRIMARY KEY (term, doc_id),
            FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
        ) WITHOUT ROWID;
        CREATE INDEX documents_domain_idx ON documents(domain);
        CREATE INDEX documents_technology_idx ON documents(technology);
        CREATE INDEX documents_profile_idx ON documents(profile);
        CREATE INDEX documents_status_idx ON documents(status);
        CREATE INDEX postings_doc_idx ON postings(doc_id);
        """
    )


def build_index(root: Path) -> dict[str, Any]:
    root = root.resolve()
    contract, split_frontmatter = _load_contract(root)
    destination = index_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_value = tempfile.mkstemp(
        prefix=destination.name + ".",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_value)
    content_entries: list[tuple[str, str]] = []
    card_count = 0
    posting_count = 0
    try:
        connection = sqlite3.connect(temporary)
        try:
            _create_schema(connection)
            for doc_id, path in enumerate(_card_files(root), start=1):
                before = path.stat()
                raw = path.read_bytes()
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (
                    after.st_size,
                    after.st_mtime_ns,
                ):
                    raise ValueError(f"knowledge card changed while indexing: {path}")
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError(f"knowledge card is not UTF-8: {path}") from exc
                metadata, body = split_frontmatter(text)
                if metadata is None:
                    raise ValueError(f"invalid card {path}: missing frontmatter")
                relative = path.relative_to(root)
                path_info = contract.derive_card_path(relative)
                issues = contract.validate_card(relative, metadata, body)
                if issues:
                    detail = "; ".join(f"{item.code}: {item.message}" for item in issues)
                    raise ValueError(f"invalid card {path}: {detail}")

                relative_text = relative.as_posix()
                file_sha256 = hashlib.sha256(raw).hexdigest()
                content_entries.append((relative_text, file_sha256))
                stat = after
                connection.execute(
                    "INSERT INTO manifest VALUES (?, ?, ?, ?)",
                    (relative_text, stat.st_size, stat.st_mtime_ns, file_sha256),
                )
                title = str(metadata.get("title", ""))
                description = str(metadata.get("description", ""))
                tags = " ".join(str(value) for value in metadata.get("tags", []))
                aliases = " ".join(str(value) for value in metadata.get("aliases", []))
                search_text = "\n".join((title, description, tags, aliases, body)).lower()
                fingerprint = card_fingerprint(metadata, body)
                connection.execute(
                    """
                    INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        path_info.doc_id,
                        relative_text,
                        path_info.domain,
                        path_info.route,
                        path_info.card_type,
                        str(metadata.get("type", "")),
                        str(metadata.get("status", "")),
                        title,
                        description,
                        body,
                        search_text,
                        _canonical_json(metadata),
                        len(text.splitlines()),
                        fingerprint,
                    ),
                )
                fields = (
                    token_counts(title),
                    token_counts(description),
                    token_counts(tags),
                    token_counts(aliases),
                    token_counts(body),
                )
                all_terms = set().union(*(set(field) for field in fields))
                connection.executemany(
                    "INSERT INTO postings VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        (term, doc_id, *(field.get(term, 0) for field in fields))
                        for term in sorted(all_terms)
                    ),
                )
                card_count += 1
                posting_count += len(all_terms)

            metadata = {
                "schema_version": INDEX_SCHEMA,
                "index_version": INDEX_VERSION,
                "content_fingerprint": _fingerprint(content_entries),
                "governance_fingerprint": governance_fingerprint(root),
                "card_count": card_count,
                "posting_count": posting_count,
                "repository_state": repository_state(root),
            }
            connection.executemany(
                "INSERT INTO meta VALUES (?, ?)",
                ((key, _canonical_json(value)) for key, value in sorted(metadata.items())),
            )
            connection.commit()
        finally:
            connection.close()
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return metadata
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _read_meta(connection: sqlite3.Connection) -> dict[str, Any]:
    return {key: json.loads(value) for key, value in connection.execute("SELECT key, value FROM meta")}


def _connect_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def verify_index(root: Path, *, full: bool = False) -> dict[str, Any]:
    root = root.resolve()
    path = index_path(root)
    if not path.is_file():
        raise ValueError(f"knowledge index is missing: {path}; run knowledge_index.py build")
    try:
        connection = _connect_readonly(path)
    except sqlite3.Error as exc:
        raise ValueError(f"cannot open knowledge index {path}: {exc}") from exc
    try:
        check = connection.execute("PRAGMA quick_check").fetchone()[0]
        if check != "ok":
            raise ValueError(f"knowledge index quick_check failed: {check}")
        metadata = _read_meta(connection)
        if metadata.get("schema_version") != INDEX_SCHEMA:
            raise ValueError("knowledge index schema is unsupported; rebuild the index")
        if metadata.get("index_version") != INDEX_VERSION:
            raise ValueError("knowledge index version is stale; rebuild the index")
        current_governance = governance_fingerprint(root)
        if metadata.get("governance_fingerprint") != current_governance:
            raise ValueError("knowledge governance changed after index build; rebuild the index")
        manifest = {
            row["relative_path"]: row
            for row in connection.execute(
                "SELECT relative_path, size, mtime_ns, file_sha256 FROM manifest"
            )
        }
        current_paths = {
            path.relative_to(root).as_posix(): path for path in _card_files(root)
        }
        if set(manifest) != set(current_paths):
            raise ValueError("knowledge card set changed after index build; rebuild the index")
        content_entries: list[tuple[str, str]] = []
        for relative, card_path in current_paths.items():
            stat = card_path.stat()
            expected = manifest[relative]
            if stat.st_size != expected["size"] or stat.st_mtime_ns != expected["mtime_ns"]:
                raise ValueError(f"knowledge card changed after index build: {relative}")
            file_sha256 = expected["file_sha256"]
            if full:
                file_sha256 = sha256_file(card_path)
                if file_sha256 != expected["file_sha256"]:
                    raise ValueError(f"knowledge card content changed after index build: {relative}")
            content_entries.append((relative, file_sha256))
        if full and metadata.get("content_fingerprint") != _fingerprint(content_entries):
            raise ValueError("knowledge content fingerprint is stale; rebuild the index")
        if metadata.get("card_count") != len(manifest):
            raise ValueError("knowledge index card count is inconsistent; rebuild the index")
        return metadata
    except sqlite3.Error as exc:
        raise ValueError(f"invalid knowledge index {path}: {exc}") from exc
    finally:
        connection.close()


def open_index(
    root: Path,
    *,
    full: bool = False,
) -> tuple[sqlite3.Connection, dict[str, Any]]:
    metadata = verify_index(root, full=full)
    return _connect_readonly(index_path(root)), metadata


def load_cards(connection: sqlite3.Connection) -> list[IndexedCard]:
    result = []
    for row in connection.execute(
        """
        SELECT doc_id, concept_id, relative_path, domain, technology, profile,
               metadata_json, card_lines, card_sha256
        FROM documents ORDER BY concept_id
        """
    ):
        result.append(
            IndexedCard(
                doc_id=row["doc_id"],
                path=row["concept_id"],
                relative_path=row["relative_path"],
                domain=row["domain"],
                technology=row["technology"],
                profile=row["profile"],
                metadata=json.loads(row["metadata_json"]),
                card_lines=row["card_lines"],
                card_sha256=row["card_sha256"],
            )
        )
    return result


def posting_scores(connection: sqlite3.Connection, terms: list[str]) -> dict[int, float]:
    if not terms:
        return {}
    placeholders = ",".join("?" for _ in terms)
    rows = connection.execute(
        f"""
        SELECT doc_id,
               SUM(4.0 * title_tf + 2.5 * description_tf + 2.0 * tags_tf
                   + 2.0 * aliases_tf + 0.5 * MIN(body_tf, 4)) AS score
        FROM postings WHERE term IN ({placeholders}) GROUP BY doc_id
        """,
        terms,
    )
    return {int(row["doc_id"]): float(row["score"]) for row in rows}


def phrase_matches(connection: sqlite3.Connection, phrase: str) -> set[int]:
    if not phrase:
        return set()
    return {
        int(row["doc_id"])
        for row in connection.execute(
            "SELECT doc_id FROM documents WHERE instr(search_text, ?) > 0",
            (phrase.lower(),),
        )
    }
