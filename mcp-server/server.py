#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Read-only MCP server exposing the cannbot-knowledge retrieval contract.

The server is an adapter, not a search engine: discover and search shell out
to the existing knowledge_query CLI (fail-closed index checks included) and
pass its JSON payload through verbatim; read_card serves governed cards from
the knowledge/ bundle root. All diagnostics go to stderr - in stdio mode the
stdout channel carries protocol frames only.
"""

from __future__ import annotations

import argparse
import asyncio
import contextvars
import copy
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from urllib.parse import unquote

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
SKILL_SCRIPTS = REPO_ROOT / ".agents/skills/knowledge-query/scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from pydantic import Field  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

from retrieval.index import open_index  # noqa: E402
from retrieval.root import ENV_KEY, resolve_root  # noqa: E402

from log_uploader import LogUploader  # noqa: E402


TRANSPORT_ENV = "CANNBOT_MCP_TRANSPORT"
HOST_ENV = "CANNBOT_MCP_HOST"
PORT_ENV = "CANNBOT_MCP_PORT"
TOKENS_ENV = "CANNBOT_MCP_TOKENS"
RATE_LIMIT_ENV = "CANNBOT_MCP_RATE_LIMIT"
LOG_ENV = "CANNBOT_MCP_LOG"
LOG_DIR_ENV = "CANNBOT_MCP_LOG_DIR"
LOG_UPLOAD_REMOTE_ENV = "CANNBOT_MCP_LOG_UPLOAD_REMOTE"
LOG_UPLOAD_INTERVAL_ENV = "CANNBOT_MCP_LOG_UPLOAD_INTERVAL"
LOG_UPLOAD_BRANCH_ENV = "CANNBOT_MCP_LOG_UPLOAD_BRANCH"
MAX_SUBPROCS_ENV = "CANNBOT_MCP_MAX_SUBPROCS"
SUBPROC_TIMEOUT_ENV = "CANNBOT_MCP_SUBPROC_TIMEOUT"
HEADERS_ROOT_ENV = "CANNBOT_MCP_HEADERS_ROOT"
PLATFORM_ENUM_TEXT = "a2 / a3 / 950 / 310p / 910 / kirin_x90 / kirin_9030 / agnostic"
DEFAULT_LOG_DIR = Path.home() / ".local/state/cannbot-knowledge/mcp"
DEFAULT_UPLOAD_REMOTE = "https://gitcode.com/qixingkai/cannbot-knowledeg-log.git"
READ_DEFAULT_LINES = 200
READ_MAX_LINES = 500
_AUTH_FAILURE_WINDOW_S = 60.0
_AUTH_FAILURE_LIMIT = 10
_AUTH_BLOCK_S = 300.0


@dataclass
class RequestMeta:
    transport: str = "stdio"
    principal: str | None = None
    jsonrpc_id: Any = None


request_meta: contextvars.ContextVar[RequestMeta] = contextvars.ContextVar(
    "cannbot_mcp_request_meta", default=RequestMeta()
)


def _utc_now() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


CALL_LOG_SCHEMA = "mcp-call-log.v2"
BOOT_ID = secrets.token_hex(4)


class StructuredToolError(ToolError):
    """ToolError carrying the error_kind recorded in the call log."""

    def __init__(self, message: str, *, kind: str = "internal") -> None:
        super().__init__(message)
        self.kind = kind


def tool_error_kind(exc: BaseException) -> str | None:
    kind = getattr(exc, "kind", None)
    return kind if isinstance(kind, str) and kind else None


class CallLogger:
    """Append-only JSONL call/event log written outside the repository."""

    def __init__(self) -> None:
        self.directory: Path | None = None
        self.enabled = False
        self._lock = threading.Lock()

    def configure(self, directory: Path, enabled: bool, repo_root: Path) -> None:
        resolved = directory.expanduser()
        try:
            inside_repo = resolved.resolve().is_relative_to(repo_root.resolve())
        except OSError:
            inside_repo = False
        if enabled and inside_repo:
            print(
                "cannbot-mcp: refusing to write call logs inside the knowledge "
                f"repository ({resolved}); logging disabled",
                file=sys.stderr,
            )
            enabled = False
        self.directory = resolved
        self.enabled = enabled

    def _append(self, record: dict[str, Any]) -> None:
        if not self.enabled or self.directory is None:
            return
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            target = self.directory / (
                f"calls-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
            )
            line = json.dumps(record, ensure_ascii=False) + "\n"
            with self._lock, open(target, "a", encoding="utf-8") as stream:
                stream.write(line)
        except OSError as exc:
            print(f"cannbot-mcp: failed to write call log: {exc}", file=sys.stderr)

    def log_call(
        self,
        *,
        transport: str,
        principal: str | None,
        tool: str,
        arguments: dict[str, Any],
        ok: bool,
        count: int | None,
        latency_ms: float,
        request_sha256: str | None,
        index: dict[str, Any] | None,
        hits: list[str] | None,
        scores: list[float] | None = None,
        card_sha256: str | None = None,
        total_lines: int | None = None,
        returned_lines: int | None = None,
        truncated: bool | None = None,
        response_sha256: str | None = None,
        response_bytes: int | None = None,
        error: str | None,
        error_kind: str | None = None,
        jsonrpc_id: Any = None,
        boot_id: str | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "schema": CALL_LOG_SCHEMA,
            "ts": _utc_now(),
            # one stable id per logged call: multi-instance union merges can
            # duplicate a line verbatim, and only a per-call id keeps that
            # duplicate apart from a same-millisecond identical sibling call.
            "call_id": secrets.token_hex(8),
            "boot_id": boot_id,
            "transport": transport,
            "principal": principal,
            "tool": tool,
            "args": arguments,
            "ok": ok,
            "count": count,
            "latency_ms": latency_ms,
            "request_sha256": request_sha256,
            "index": index,
            "hits": hits,
            "scores": scores,
            "card_sha256": card_sha256,
            "total_lines": total_lines,
            "returned_lines": returned_lines,
            "truncated": truncated,
            "response_sha256": response_sha256,
            "response_bytes": response_bytes,
            "error": error,
            "error_kind": error_kind,
            "jsonrpc_id": jsonrpc_id,
        }
        if tool != "read_card":
            for key in ("card_sha256", "total_lines", "returned_lines", "truncated"):
                record.pop(key)
        if tool != "search":
            record.pop("scores")
        self._append(record)

    def log_event(self, **fields: Any) -> None:
        self._append({"schema": CALL_LOG_SCHEMA, "ts": _utc_now(), **fields})


class TokenList:
    """Parsed CANNBOT_MCP_TOKENS list: bare tokens are anonymous."""

    def __init__(self, entries: list[tuple[str, str | None]]) -> None:
        self.entries = entries

    @classmethod
    def parse(cls, raw: str | None) -> "TokenList":
        entries: list[tuple[str, str | None]] = []
        seen: set[str] = set()
        for item in (raw or "").split(","):
            item = item.strip()
            if not item:
                continue
            token, _, label = item.partition(":")
            token = token.strip()
            label = label.strip() or None
            if not token or token in seen:
                continue
            seen.add(token)
            entries.append((token, label))
        return cls(entries)

    def __len__(self) -> int:
        return len(self.entries)

    def match(self, presented: str) -> tuple[bool, str | None]:
        for token, label in self.entries:
            if secrets.compare_digest(token, presented):
                return True, label
        return False, None


@dataclass
class RateDecision:
    allowed: bool
    retry_after_s: int = 0


class RateLimiter:
    """Replaceable rate-limit interface; swap the in-memory implementation for
    a shared (e.g. Redis) one without touching call sites."""

    def check(self, key: str, *, limit: int, window_s: float = 60.0) -> RateDecision:
        raise NotImplementedError


class SlidingWindowRateLimiter(RateLimiter):
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, *, limit: int, window_s: float = 60.0) -> RateDecision:
        if limit <= 0:
            return RateDecision(True)
        now = time.monotonic()
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= now - window_s:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_s - now) + 1)
                return RateDecision(False, retry_after)
            events.append(now)
            return RateDecision(True)


class IpCooldown:
    """Temporary block for source IPs with repeated authentication failures."""

    def __init__(self) -> None:
        self._failures: dict[str, deque[float]] = {}
        self._blocked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, ip: str) -> RateDecision:
        now = time.monotonic()
        with self._lock:
            until = self._blocked_until.get(ip, 0.0)
            if until > now:
                return RateDecision(False, max(1, int(until - now) + 1))
        return RateDecision(True)

    def record_failure(self, ip: str) -> None:
        now = time.monotonic()
        with self._lock:
            events = self._failures.setdefault(ip, deque())
            events.append(now)
            while events and events[0] <= now - _AUTH_FAILURE_WINDOW_S:
                events.popleft()
            if len(events) >= _AUTH_FAILURE_LIMIT:
                self._blocked_until[ip] = now + _AUTH_BLOCK_S
                events.clear()

    def record_success(self, ip: str) -> None:
        with self._lock:
            self._failures.pop(ip, None)


class CliRunner:
    """Subprocess adapter around knowledge_query.py with a concurrency gate."""

    def __init__(
        self,
        script: Path,
        root: Path,
        max_subprocs: int,
        timeout_s: float,
    ) -> None:
        self.script = script
        self.root = root
        self.timeout_s = timeout_s
        self._semaphore = asyncio.Semaphore(max(1, max_subprocs))

    async def run(self, arguments: list[str]) -> dict[str, Any]:
        command = [
            sys.executable,
            str(self.script),
            "--knowledge-root",
            str(self.root),
            *arguments,
        ]
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        async with self._semaphore:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=environment,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout_s
                )
            except asyncio.CancelledError:
                # The SDK cancelled the handler (client went away): kill and
                # reap the subprocess, then let the cancellation propagate.
                process.kill()
                await process.wait()
                raise
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise StructuredToolError(
                    f"knowledge CLI exceeded the {self.timeout_s:g}s subprocess "
                    "timeout and was terminated; the server stays up - retry the "
                    "call or ask the maintainer to inspect the knowledge root",
                    kind="subprocess_timeout",
                ) from None
        return self._interpret(
            process.returncode or 0,
            stdout.decode("utf-8", "replace"),
            stderr.decode("utf-8", "replace"),
        )

    def _interpret(
        self, returncode: int, stdout: str, stderr: str
    ) -> dict[str, Any]:
        if returncode != 0:
            raise StructuredToolError(
                self._cli_failure(returncode, stderr),
                kind=self._cli_failure_kind(stderr),
            )
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            raise StructuredToolError(
                "knowledge CLI produced unparseable output "
                f"(exit {returncode}); stderr: {self._tail(stderr)}",
                kind="cli_error",
            ) from None
        if not isinstance(payload, dict):
            raise StructuredToolError(
                "knowledge CLI produced an unexpected payload shape "
                f"(exit {returncode}); stderr: {self._tail(stderr)}",
                kind="cli_error",
            )
        return payload

    def _cli_failure_kind(self, stderr: str) -> str:
        """CLI error category from the structured JSON error's code field.

        The knowledge CLI prints its error as a JSON object on stderr; a
        present code field maps directly, otherwise index-stale/missing
        wording (the same markers the rebuild hint uses) classifies the row
        and everything else falls into the generic cli_error bucket.
        """
        for line in stderr.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                decoded = json.loads(line)
            except json.JSONDecodeError:
                continue
            error = decoded.get("error") if isinstance(decoded, dict) else None
            if isinstance(error, dict) and error.get("code"):
                return str(error["code"])
            if isinstance(error, dict) and error.get("message"):
                return _cli_error_kind_from_message(str(error["message"]))
        if "index" in stderr and "missing" in stderr:
            return "index_missing"
        return "cli_error"

    def _cli_failure(self, returncode: int, stderr: str) -> str:
        message = ""
        for line in stderr.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                decoded = json.loads(line)
            except json.JSONDecodeError:
                continue
            error = decoded.get("error") if isinstance(decoded, dict) else None
            if isinstance(error, dict) and error.get("message"):
                message = str(error["message"])
                break
        if not message:
            message = stderr.strip() or "no diagnostics"
        hint = ""
        if "index" in message and any(
            marker in message
            for marker in ("rebuild", "index build", "missing", "inconsistent", "unsupported", "stale")
        ):
            hint = (
                "; the maintainer should rebuild it with: python3 "
                ".agents/skills/knowledge-query/scripts/knowledge_index.py "
                f"--knowledge-root {self.root} build"
            )
        return f"knowledge CLI failed (exit {returncode}): {message}{hint}"

    @staticmethod
    def _tail(stderr: str, limit: int = 400) -> str:
        text = stderr.strip()
        return text if len(text) <= limit else text[-limit:]


def _cli_error_kind_from_message(message: str) -> str:
    """Classify CLI failures from the stderr error message keywords."""
    if "platform is required" in message:
        return "platform_missing"
    if "index is missing" in message:
        return "index_missing"
    if "index" in message and any(
        marker in message
        for marker in ("rebuild", "index build", "inconsistent", "unsupported", "stale")
    ):
        return "index_stale"
    return "cli_error"


class CardReader:
    """Paginated, traversal-safe card reads from the knowledge bundle."""

    def __init__(self, root: Path, transport: str) -> None:
        self.root = root
        self.bundle = root / "knowledge"
        self.transport = transport

    def canonicalize(self, raw: str) -> tuple[str, Path, str]:
        if not raw or raw != raw.strip():
            raise StructuredToolError(
                "path must be a non-empty trimmed value", kind="invalid_argument"
            )
        if raw.startswith("/") or "\\" in raw or "\0" in raw:
            raise StructuredToolError(
                "path must be Bundle-relative (no absolute paths or backslashes)",
                kind="path_out_of_bundle",
            )
        parts = PurePosixPath(raw).parts
        if any(part in ("..", ".") for part in parts):
            raise StructuredToolError(
                "path must not contain '.' or '..' segments",
                kind="path_out_of_bundle",
            )
        markdown_relative = raw if raw.endswith(".md") else raw + ".md"
        bundle_root = self.bundle.resolve()
        target = (self.bundle / markdown_relative).resolve()
        if not target.is_relative_to(bundle_root):
            raise StructuredToolError(
                "path escapes the knowledge bundle; only paths inside knowledge/ "
                "are readable",
                kind="path_out_of_bundle",
            )
        if not target.is_file():
            raise StructuredToolError(
                f"card file does not exist: {markdown_relative}; use search to "
                "obtain a valid path",
                kind="path_not_indexed",
            )
        concept_id = markdown_relative[: -len(".md")]
        return concept_id, target, markdown_relative

    def open_index_row(self, concept_id: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        try:
            connection, metadata = open_index(self.root, full=False)
        except (OSError, ValueError) as exc:
            raise StructuredToolError(
                f"knowledge index check failed: {exc}; the maintainer should "
                "rebuild it with: python3 .agents/skills/knowledge-query/scripts/"
                f"knowledge_index.py --knowledge-root {self.root} build",
                kind=_cli_error_kind_from_message(str(exc)),
            ) from exc
        try:
            row = connection.execute(
                "SELECT doc_id FROM documents WHERE concept_id = ?", (concept_id,)
            ).fetchone()
        except sqlite3.Error as exc:
            raise StructuredToolError(
                f"knowledge index query failed: {exc}", kind="cli_error"
            ) from exc
        finally:
            connection.close()
        return ({"doc_id": row["doc_id"]} if row is not None else None), metadata

    def read(
        self, raw_path: str, offset: int, limit: int
    ) -> dict[str, Any]:
        if offset < 0:
            raise StructuredToolError(
                "offset must be a non-negative line offset", kind="invalid_argument"
            )
        if limit < 1:
            raise StructuredToolError(
                "limit must be at least 1 line", kind="invalid_argument"
            )
        limit = min(limit, READ_MAX_LINES)
        concept_id, target, markdown_relative = self.canonicalize(raw_path)
        row, metadata = self.open_index_row(concept_id)
        if row is None and target.name != "index.md":
            raise StructuredToolError(
                f"card is not present in the knowledge index: {markdown_relative}; "
                "use search to obtain a valid path",
                kind="path_not_indexed",
            )
        raw = target.read_bytes()
        text = raw.decode("utf-8")
        lines = text.splitlines(keepends=True)
        total_lines = len(lines)
        if offset >= total_lines:
            raise StructuredToolError(
                f"offset {offset} is beyond the end of the card "
                f"({total_lines} lines); valid offsets are 0..{total_lines - 1}",
                kind="offset_out_of_range",
            )
        selected = lines[offset : offset + limit]
        returned = len(selected)
        truncated = offset + returned < total_lines
        frontmatter, _body = self._split_frontmatter(text)
        payload: dict[str, Any] = {
            "path": concept_id,
            "title": frontmatter.get("title") or markdown_relative,
            "type": frontmatter.get("type"),
            "status": frontmatter.get("status"),
            "card_sha256": hashlib.sha256(raw).hexdigest(),
            "total_lines": total_lines,
            "offset": offset,
            "returned_lines": returned,
            "truncated": truncated,
            "next_offset": offset + returned if truncated else None,
            "content": "".join(selected),
            "frontmatter": frontmatter,
            "sources": frontmatter.get("sources", []),
            "source_headers": frontmatter.get("source_headers", []),
            "links": self._links(text, target),
            "images": self._images(text),
            "index": {
                "schema_version": metadata.get("schema_version"),
                "index_version": metadata.get("index_version"),
                "content_fingerprint": metadata.get("content_fingerprint"),
                "governance_fingerprint": metadata.get("governance_fingerprint"),
                "card_count": metadata.get("card_count"),
                "posting_count": metadata.get("posting_count"),
                "built_repository_state": metadata.get("repository_state"),
            },
        }
        if self.transport == "stdio":
            # Instance-local absolute paths stay out of the shared payload so
            # response_sha256 (drift-checked across instances) cannot differ
            # just because two instances mount the bundle at different paths.
            payload["local_only"] = {
                "local_path": str(target),
                "sources_root": str(self.root),
                "headers_root": os.environ.get(HEADERS_ROOT_ENV) or None,
            }
        return payload

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
        lines = text.split("\n")
        if not lines or lines[0].strip() != "---":
            return {}, text
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                block = "\n".join(lines[1:index])
                body = "\n".join(lines[index + 1 :])
                try:
                    data = yaml.safe_load(block)
                except yaml.YAMLError as exc:
                    raise StructuredToolError(
                        f"invalid frontmatter: {exc}", kind="invalid_argument"
                    ) from exc
                if data is None:
                    data = {}
                if not isinstance(data, dict):
                    raise StructuredToolError(
                        "frontmatter must be a mapping", kind="invalid_argument"
                    )
                return data, body
        return {}, text

    def _links(self, text: str, card_file: Path) -> list[dict[str, Any]]:
        bundle_root = self.bundle.resolve()
        links: list[dict[str, Any]] = []
        seen: set[tuple[str, str | None]] = set()
        for is_image, destination, label in _extract_markdown_links(text):
            if is_image:
                continue
            if destination.startswith(("http://", "https://", "mailto:")):
                continue
            clean = unquote(destination.split("#", 1)[0].strip().strip("<>"))
            resolved_path: str | None = None
            if clean:
                if clean.startswith("/"):
                    candidate = bundle_root / clean.lstrip("/")
                else:
                    candidate = card_file.parent / clean
                try:
                    resolved = candidate.resolve()
                    resolved_path = resolved.relative_to(bundle_root).as_posix()
                except (OSError, ValueError):
                    continue
            key = (destination, resolved_path)
            if key in seen:
                continue
            seen.add(key)
            entry: dict[str, Any] = {"href": destination, "text": label}
            if resolved_path is not None:
                entry["resolved_path"] = resolved_path
            links.append(entry)
        return links

    @staticmethod
    def _images(text: str) -> list[dict[str, Any]]:
        images: list[dict[str, Any]] = []
        seen: set[str] = set()
        for is_image, destination, label in _extract_markdown_links(text):
            if not is_image or destination in seen:
                continue
            seen.add(destination)
            images.append({"url": destination, "alt": label})
        return images


_MD_LABEL = r"(?:\\.|[^\]\\\n])*"
_INLINE_LINK_RE = re.compile(rf"(!?)\[({_MD_LABEL})\]\(([^)\n]+)\)")
_REFERENCE_USE_RE = re.compile(rf"(!?)\[({_MD_LABEL})\]\[({_MD_LABEL})\]")
_REFERENCE_DEF_RE = re.compile(
    rf"(?m)^[ \t]{{0,3}}\[({_MD_LABEL})\]:[ \t]*(?:<([^>\n]+)>|(\S+))"
)
_FENCE_RE = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"(?P<ticks>`+)[^\n]*?(?P=ticks)")


def _mask_code(text: str) -> str:
    def blank(value: str) -> str:
        return "".join("\n" if char == "\n" else " " for char in value)

    lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = _FENCE_RE.match(line)
        if fence_char is None:
            if match is None:
                lines.append(line)
                continue
            fence = match.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            lines.append(blank(line))
            continue
        lines.append(blank(line))
        if match is not None:
            fence = match.group("fence")
            if fence[0] == fence_char and len(fence) >= fence_length:
                fence_char = None
                fence_length = 0
    masked = "".join(lines)
    return _INLINE_CODE_RE.sub(lambda match: blank(match.group()), masked)


def _extract_markdown_links(text: str) -> list[tuple[bool, str, str]]:
    """Return (is_image, destination, label) outside code spans, in order."""

    def destination_of(value: str) -> str:
        return value.split()[0].strip("<>") if value.strip() else ""

    masked = _mask_code(text)
    entries: list[tuple[int, bool, str, str]] = [
        (
            match.start(),
            bool(match.group(1)),
            destination_of(match.group(3)),
            match.group(2),
        )
        for match in _INLINE_LINK_RE.finditer(masked)
    ]
    definitions: dict[str, str] = {}
    for match in _REFERENCE_DEF_RE.finditer(masked):
        label = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
        definitions[label] = destination_of(match.group(2) or match.group(3) or "")
    for match in _REFERENCE_USE_RE.finditer(masked):
        label = re.sub(
            r"\s+", " ", (match.group(3) or match.group(2)).strip()
        ).casefold()
        target = definitions.get(label)
        if target:
            entries.append(
                (match.start(), bool(match.group(1)), target, match.group(2))
            )
    entries.sort(key=lambda item: item[0])
    return [(is_image, destination, label) for _offset, is_image, destination, label in entries]


def _digest_view(payload: Any, tool: str) -> Any:
    """Copy of a response payload with instance-local absolute paths removed.

    The digest is the multi-instance divergence signal, so it must depend on
    the content only, never on where this instance mounts the bundle: search
    results carry a per-hit ``local_path`` (under both ``results`` and
    ``hits``, which the CLI emits as one list but the subprocess JSON
    round-trip deserializes into two independent objects) and discover
    carries the bundle ``root`` straight from the CLI contract, and read_card
    carries the stdio-only ``local_only`` block. The client-visible payload
    is returned untouched (the search/discover passthrough parity is a
    documented contract); only the hashed copy drops these fields.
    """
    view = copy.deepcopy(payload)
    if not isinstance(view, dict):
        return view
    if tool == "search":
        for key in ("results", "hits"):
            items = view.get(key)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        item.pop("local_path", None)
    elif tool == "discover":
        view.pop("root", None)
    else:
        view.pop("local_only", None)
    return view


def _canonical_response_digest(payload: Any) -> tuple[str, int]:
    """Hash the canonical JSON serialization of a response payload.

    sort_keys plus fixed separators keep the digest stable across instances
    and versions; drifting digests for identical requests are the
    multi-instance divergence signal.
    """
    serialized = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest(), len(serialized)


def _repository_version() -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "describe", "--tags", "--always", "--dirty"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "dev"
    if completed.returncode != 0:
        return "dev"
    return completed.stdout.strip() or "dev"


mcp_server = MCPServer(
    "cannbot-knowledge",
    instructions=(
        "Read-only access to the cannbot-knowledge base: call discover to see "
        "what is covered, search to rank candidate cards, read_card to read "
        "one card with its sources and links. Confirm the target platform "
        "before searching; searches without a platform fail closed."
    ),
    version=_repository_version(),
)
_LOGGER = CallLogger()
_RUNNER: CliRunner | None = None
_READER: CardReader | None = None


def _require_runner() -> CliRunner:
    if _RUNNER is None:
        raise ToolError("server context is not initialized")
    return _RUNNER


def _require_reader() -> CardReader:
    if _READER is None:
        raise ToolError("server context is not initialized")
    return _READER


async def _logged_call(
    tool: str, arguments: dict[str, Any], action: Callable[[], Any]
) -> dict[str, Any]:
    meta = request_meta.get()
    started = time.perf_counter()
    payload: dict[str, Any] | None = None
    error_text: str | None = None
    error_kind: str | None = None
    try:
        payload = await action()
        return payload
    except ToolError as exc:
        error_text = str(exc)
        error_kind = tool_error_kind(exc)
        raise
    except (OSError, ValueError, yaml.YAMLError) as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        error_kind = "internal"
        raise ToolError(f"{tool} failed: {exc}") from exc
    finally:
        count = None
        hits = None
        scores = None
        card_sha256 = None
        total_lines = None
        returned_lines = None
        truncated = None
        response_sha256 = None
        response_bytes = None
        if payload is not None:
            if tool == "search":
                count = payload.get("count")
                hits = [item.get("path") for item in payload.get("results", [])]
                scores = [item.get("score") for item in payload.get("results", [])]
            elif tool == "discover":
                count = payload.get("cards")
            elif tool == "read_card":
                card_sha256 = payload.get("card_sha256")
                total_lines = payload.get("total_lines")
                returned_lines = payload.get("returned_lines")
                truncated = payload.get("truncated")
            response_sha256, response_bytes = _canonical_response_digest(
                _digest_view(payload, tool)
            )
        _LOGGER.log_call(
            transport=meta.transport,
            principal=meta.principal,
            tool=tool,
            arguments=arguments,
            ok=error_text is None,
            count=count,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            request_sha256=payload.get("request_sha256") if payload else None,
            index=payload.get("index") if payload else None,
            hits=hits,
            scores=scores,
            card_sha256=card_sha256,
            total_lines=total_lines,
            returned_lines=returned_lines,
            truncated=truncated,
            response_sha256=response_sha256,
            response_bytes=response_bytes,
            error=error_text,
            error_kind=error_kind,
            jsonrpc_id=meta.jsonrpc_id,
            boot_id=BOOT_ID,
        )


@mcp_server.tool(name="discover", annotations=ToolAnnotations(read_only_hint=True))
async def discover() -> dict[str, Any]:
    """Summarize what the cannbot-knowledge base covers before searching it.

    Returns real per-dimension coverage counts (domains, technologies, types,
    profiles, statuses) plus index provenance. Counts show registered coverage
    and do not prove that a specific combination exists. This is also the
    cheapest health check: a successful call proves the knowledge root and the
    search index are valid and fresh. Read-only.
    """
    return await _logged_call("discover", {}, lambda: _require_runner().run(["discover", "--json"]))


@mcp_server.tool(name="search", annotations=ToolAnnotations(read_only_hint=True))
async def search(
    query: str = Field(
        description=(
            "Search query; with match=literal the full string is matched as-is "
            "(not multi-word AND)."
        )
    ),
    decision: str | None = Field(
        default=None,
        description=(
            "Optional short statement of the decision this search supports; it "
            "is recorded in the audit payload but does not change ranking."
        ),
    ),
    domain: str | None = Field(
        default=None, description="Filter by knowledge domain, e.g. ops, model, common."
    ),
    technology: str | None = Field(
        default=None,
        description=(
            "Filter by technology or scope, e.g. ascendc, triton, tilelang, platforms."
        ),
    ),
    type: str | None = Field(
        default=None,
        description=(
            "Filter by knowledge type (path profile), e.g. apis, operators, "
            "guides, examples, optimizations, runbooks, glossaries."
        ),
    ),
    task: str | None = Field(
        default=None,
        description=(
            "Filter by task dimension: design, implementation, debugging, "
            "optimization, testing, migration or lookup."
        ),
    ),
    tag: list[str] | None = Field(
        default=None, description="Filter by registered topic tags; multiple tags are ANDed."
    ),
    platform: list[str] | None = Field(
        default=None,
        description=(
            "Target platform(s); legal values: "
            f"{PLATFORM_ENUM_TEXT}; multiple values are ANDed (a card must "
            "support all of them); unknown values are rejected. Optional by "
            "design: when omitted and no default platform is configured the "
            "search fails with guidance - confirm the platform, never guess it."
        ),
    ),
    include_unlocated: bool = Field(
        default=False,
        description=(
            "Include draft cards that declare no platform (requires status "
            "draft or all; cannot be combined with platform)."
        ),
    ),
    include_shared: bool = Field(
        default=False,
        description=(
            "Include cross-technology shared cards for the selected technology "
            "(requires a concrete technology)."
        ),
    ),
    source_technology: str | None = Field(
        default=None,
        description="Filter interoperability cards by their source technology.",
    ),
    target_technology: str | None = Field(
        default=None,
        description="Filter interoperability cards by their target technology.",
    ),
    status: str | None = Field(
        default=None,
        description="Card lifecycle filter: stable (default), draft, deprecated or all.",
    ),
    match: str | None = Field(
        default=None,
        description=(
            "Match mode: literal matches the full query string as-is "
            "(not multi-word AND); text (default) tokenizes and scores by "
            "lexical relevance with a phrase bonus."
        ),
    ),
    limit: int | None = Field(
        default=None,
        description=(
            "Maximum number of results; start small (5) and raise it only when "
            "the target is not found."
        ),
    ),
) -> dict[str, Any]:
    """Search the knowledge base and return ranked candidate cards.

    Returns locators (rank, path, title, description), not answers: read the
    full card with read_card before relying on any conclusion. Each result's
    path is the read_card handle. Platform handling is fail-closed: when
    platform is omitted and no default platform is configured, the call fails
    with guidance instead of silently mixing platforms - confirm the target
    platform and retry with it. Read-only.
    """
    arguments = {
        key: value
        for key, value in (
            ("query", query),
            ("decision", decision),
            ("domain", domain),
            ("technology", technology),
            ("type", type),
            ("task", task),
            ("tag", tag),
            ("platform", platform),
            ("include_unlocated", include_unlocated),
            ("include_shared", include_shared),
            ("source_technology", source_technology),
            ("target_technology", target_technology),
            ("status", status),
            ("match", match),
            ("limit", limit),
        )
        if value is not None and value is not False and value != []
    }

    def action() -> Any:
        cli: list[str] = ["search", "--json", "--query", query]
        if decision is not None:
            cli += ["--decision", decision]
        if domain is not None:
            cli += ["--domain", domain]
        if technology is not None:
            cli += ["--technology", technology]
        if type is not None:
            cli += ["--type", type]
        if task is not None:
            cli += ["--task", task]
        for item in tag or []:
            cli += ["--tag", item]
        for item in platform or []:
            cli += ["--platform", item]
        if include_unlocated:
            cli.append("--include-unlocated")
        if include_shared:
            cli.append("--include-shared")
        if source_technology is not None:
            cli += ["--source-technology", source_technology]
        if target_technology is not None:
            cli += ["--target-technology", target_technology]
        if status is not None:
            cli += ["--status", status]
        if match is not None:
            cli += ["--match", match]
        if limit is not None:
            cli += ["--limit", str(limit)]
        return _require_runner().run(cli)

    return await _logged_call("search", arguments, action)


@mcp_server.tool(name="read_card", annotations=ToolAnnotations(read_only_hint=True))
async def read_card(
    path: str = Field(
        description=(
            "Bundle-relative card path, exactly the path field returned by "
            "search (with or without the trailing .md)."
        )
    ),
    offset: int = Field(
        default=0,
        description=(
            "0-based line offset for pagination; frontmatter lines count. To "
            "continue a truncated read, pass the returned next_offset - it is "
            "a cursor, not a line number."
        ),
    ),
    limit: int = Field(
        default=READ_DEFAULT_LINES,
        description=(
            "Maximum lines to return this call; default 200, values above 500 "
            "are clamped to 500."
        ),
    ),
) -> dict[str, Any]:
    """Read one knowledge card: the full evidence behind a search result.

    Returns paginated raw content (frontmatter included, lines counted),
    the parsed frontmatter object, the complete sources list, Ascend C
    source_headers when present, in-bundle links resolved to read_card-ready
    paths, image references, and index provenance. Sources are reported, not
    fetched. Read-only.
    """
    arguments = {"path": path, "offset": offset, "limit": limit}

    def action() -> Any:
        reader = _require_reader()
        return asyncio.to_thread(reader.read, path, offset, limit)

    return await _logged_call("read_card", arguments, action)


def _http_headers(scope: dict[str, Any]) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


async def _send_json_response(
    send: Callable[..., Any],
    status: int,
    payload: dict[str, Any],
    extra_headers: list[tuple[bytes, bytes]] | None = None,
) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
        *(extra_headers or []),
    ]
    await send(
        {"type": "http.response.start", "status": status, "headers": headers}
    )
    await send({"type": "http.response.body", "body": body})


async def _drain_body(receive: Callable[..., Any], cap: int = 4 * 1024 * 1024) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        message = await receive()
        if message.get("type") != "http.request":
            break
        chunk = message.get("body", b"")
        chunks.append(chunk)
        total += len(chunk)
        if not message.get("more_body") or total > cap:
            break
    return b"".join(chunks)


def _replay_body(receive: Callable[..., Any], body: bytes) -> Callable[..., Any]:
    """Serve the drained request body to the inner ASGI app in one message."""
    state = {"delivered": False}

    async def replay_receive() -> dict[str, Any]:
        if not state["delivered"]:
            state["delivered"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await receive()

    return replay_receive


def _request_tool_name(body: bytes) -> str | None:
    try:
        message = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(message, dict) or message.get("method") != "tools/call":
        return None
    params = message.get("params")
    name = params.get("name") if isinstance(params, dict) else None
    return str(name) if name else None


def _request_jsonrpc_id(body: bytes) -> Any:
    """Extract the JSON-RPC id verbatim for call-log correlation."""
    try:
        message = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(message, dict):
        return message.get("id")
    return None


def build_http_app(
    knowledge_server: MCPServer,
    tokens: TokenList,
    limiter: RateLimiter,
    cooldown: IpCooldown,
    rate_limit: int,
    host: str,
) -> Callable[..., Any]:
    inner = knowledge_server.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=True, host=host
    )

    async def app(scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope["type"] == "http" and scope.get("path") == "/health":
            # Unauthenticated liveness probe for K8s/APISIX-style orchestrators:
            # answers before auth and rate limiting, never reaches the MCP app,
            # and is not written to the call log.
            await _drain_body(receive)
            await _send_json_response(send, 200, {"status": "ok"})
            return
        if scope["type"] != "http" or scope.get("path") != "/mcp":
            await inner(scope, receive, send)
            return
        client_ip = (scope.get("client") or ("unknown", 0))[0]
        blocked = cooldown.check(client_ip)
        if not blocked.allowed:
            _LOGGER.log_event(
                event="auth_failed",
                src_ip=client_ip,
                reason="ip_cooldown",
                retry_after_s=blocked.retry_after_s,
                boot_id=BOOT_ID,
            )
            await _drain_body(receive)
            await _send_json_response(
                send,
                429,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": (
                            "too many failed authentication attempts; "
                            f"retry after {blocked.retry_after_s}s"
                        ),
                    },
                },
                [(b"retry-after", str(blocked.retry_after_s).encode("ascii"))],
            )
            return
        headers = _http_headers(scope)
        presented = None
        authorization = headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            presented = authorization[7:].strip()
        if not presented:
            presented = headers.get("x-mcp-auth-token", "").strip() or None
        if not presented:
            cooldown.record_failure(client_ip)
            _LOGGER.log_event(
                event="auth_failed", src_ip=client_ip, reason="no_token", boot_id=BOOT_ID
            )
            await _drain_body(receive)
            await _send_json_response(
                send,
                401,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": "unauthorized: provide a valid bearer token",
                    },
                },
                [(b"www-authenticate", b"Bearer")],
            )
            return
        matched, principal = tokens.match(presented)
        if not matched:
            cooldown.record_failure(client_ip)
            _LOGGER.log_event(
                event="auth_failed", src_ip=client_ip, reason="no_match", boot_id=BOOT_ID
            )
            await _drain_body(receive)
            await _send_json_response(
                send,
                401,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": "unauthorized: provide a valid bearer token",
                    },
                },
                [(b"www-authenticate", b"Bearer")],
            )
            return
        cooldown.record_success(client_ip)
        decision = limiter.check(presented, limit=rate_limit)
        if not decision.allowed:
            body = await _drain_body(receive)
            _LOGGER.log_event(
                event="rate_limited",
                principal=principal,
                tool=_request_tool_name(body),
                retry_after_s=decision.retry_after_s,
                boot_id=BOOT_ID,
            )
            await _send_json_response(
                send,
                429,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32600,
                        "message": (
                            "rate limit exceeded; "
                            f"retry after {decision.retry_after_s}s"
                        ),
                    },
                },
                [(b"retry-after", str(decision.retry_after_s).encode("ascii"))],
            )
            return
        body = await _drain_body(receive)
        jsonrpc_id = _request_jsonrpc_id(body)
        request_meta.set(
            RequestMeta(transport="http", principal=principal, jsonrpc_id=jsonrpc_id)
        )
        await inner(
            scope,
            _replay_body(receive, body),
            send,
        )

    return app


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(
            f"cannbot-mcp: ignoring invalid {name}={raw!r}, using {default}",
            file=sys.stderr,
        )
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        print(
            f"cannbot-mcp: ignoring invalid {name}={raw!r}, using {default}",
            file=sys.stderr,
        )
        return default
    return value if value > 0 else default


def _log_enabled(transport: str) -> bool:
    value = (os.environ.get(LOG_ENV) or "auto").strip().lower()
    if value == "off":
        return False
    if value == "on":
        return True
    return transport == "http"


def _log_directory() -> Path:
    configured = os.environ.get(LOG_DIR_ENV, "").strip()
    return Path(configured) if configured else DEFAULT_LOG_DIR


def _upload_interval() -> int:
    return _env_int(LOG_UPLOAD_INTERVAL_ENV, 0)


def _upload_remote() -> str:
    return os.environ.get(LOG_UPLOAD_REMOTE_ENV, "").strip() or DEFAULT_UPLOAD_REMOTE


def _upload_branch() -> str:
    return os.environ.get(LOG_UPLOAD_BRANCH_ENV, "").strip() or "main"


def _start_uploader(transport: str, logging_enabled: bool, interval_s: int) -> bool:
    """The uploader thread runs only for served HTTP traffic worth sharing.

    stdio is single-machine by definition and stdio logging is off by default,
    so there is nothing to distribute; the interval gate keeps the default
    deployment byte-for-byte identical to a server without the feature.
    """
    return transport == "http" and logging_enabled and interval_s > 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transport", choices=["stdio", "http"], default=None)
    arguments = parser.parse_args(argv)
    transport = arguments.transport or os.environ.get(TRANSPORT_ENV, "").strip() or "stdio"
    root = resolve_root(os.environ.get(ENV_KEY), SKILL_SCRIPTS / "knowledge_query.py")
    cli_script = root / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
    if not cli_script.is_file():
        print(
            f"cannbot-mcp: knowledge CLI not found: {cli_script}", file=sys.stderr
        )
        return 2
    global _RUNNER, _READER
    _RUNNER = CliRunner(
        script=cli_script,
        root=root,
        max_subprocs=_env_int(MAX_SUBPROCS_ENV, os.cpu_count() or 1),
        timeout_s=_env_float(SUBPROC_TIMEOUT_ENV, 30.0),
    )
    _READER = CardReader(root=root, transport=transport)
    _LOGGER.configure(_log_directory(), _log_enabled(transport), REPO_ROOT)
    if transport == "http":
        tokens = TokenList.parse(os.environ.get(TOKENS_ENV))
        if not tokens:
            print(
                "cannbot-mcp: refusing to start HTTP transport: "
                f"{TOKENS_ENV} is empty; configure 'token:label' entries "
                "(comma-separated) or use stdio transport",
                file=sys.stderr,
            )
            return 2
        import uvicorn

        host = os.environ.get(HOST_ENV, "").strip() or "127.0.0.1"
        port = _env_int(PORT_ENV, 8090)
        rate_limit = _env_int(RATE_LIMIT_ENV, 0)
        app = build_http_app(
            mcp_server,
            tokens,
            SlidingWindowRateLimiter(),
            IpCooldown(),
            rate_limit,
            host,
        )
        uploader: LogUploader | None = None
        interval_s = _upload_interval()
        if _start_uploader("http", _LOGGER.enabled, interval_s):
            uploader = LogUploader(
                remote=_upload_remote(),
                branch=_upload_branch(),
                interval_s=interval_s,
                log_dir=_LOGGER.directory or _log_directory(),
                boot_id=BOOT_ID,
            )
            uploader.start()
        try:
            uvicorn.run(app, host=host, port=port, log_level="warning")
        finally:
            if uploader is not None:
                uploader.stop()
        return 0
    mcp_server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
