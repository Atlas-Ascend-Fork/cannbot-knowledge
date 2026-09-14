#!/usr/bin/env python3
"""Deterministic trace normalization for ops-knowledge-trace-ingest.

Design (learned from ops-knowledge-trajectory-ingest):
- Any trajectory source -> canonical `trace.event.v1` event stream + manifest.
- Every event binds provenance: raw_source / raw_record / raw_sha256 / adapter.
- Secret redaction, coverage accounting (unknown/skipped/warnings), capabilities.
- `verify` re-checks schema, sequence contiguity and manifest consistency.

Inputs accepted:
  * a `trace_<ses>/` directory produced by scripts/parse.py  (adapter=trace_export)
  * any JSON/JSONL/NDJSON/text export of an agent session    (adapter=generic)
  * a CANNBot gateway `parsed/context/ses_*.md` readable transcript, single file
    or whole directory (adapter=markdown_transcript; supports `## Subagent Sessions`
    multi-session transcripts)
  * a .zip/.tar* archive, a single file, or `-` for stdin

Output:
  <out>/normalized_trace.jsonl   (one canonical event per line)
  <out>/session_manifest.json    (source hash / coverage / capabilities / warnings)
  <out>/attachments/             (filesystem tool payloads copied for evidence)

The script is intentionally stdlib-only and 0-LLM. Semantic mining on top of the
normalized stream is the mine stage's job, not this script's.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import sys
import tarfile
import tempfile
import zipfile

SCHEMA = "trace.event.v1"
CANONICAL_TYPES = {
    "session_start", "session_end", "user_message", "assistant_message",
    "reasoning", "system_message", "tool_call", "tool_result",
    "file_read", "file_write", "file_diff", "artifact", "metric", "error",
    "unknown",
}
ADAPTERS = ["trace_export", "generic", "markdown_transcript",
            "claude_code", "opencode", "codex"]
READ_SUFFIXES = {".json", ".jsonl", ".ndjson", ".log", ".txt", ".md"}
MAX_MEMBER_BYTES = 256 * 1024 * 1024

# Share the credential-name grammar between text assignments and JSON keys.
# Provider/business prefixes may contain words separated by underscores or
# hyphens; the sensitive name must still end the key (not token_count, etc.).
SECRET_NAME = (
    r"(?:[\w-]*[_-])?(?:password|passwd|(?:access[_-]?|auth[_-]?|refresh[_-]?)?token|"
    r"api[_-]?key|secret(?:[_-]?key)?)"
)
SECRET_PATTERNS = [
    re.compile(r"(?i)((?<![\w-])[\"']?authorization[\"']?\s*[=:]\s*)"
               r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"),
    re.compile(r"(?i)(authorization\s*:\s*(?:bearer|basic)\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        rf"(?i)((?<![\w-])[\"']?{SECRET_NAME}[\"']?\s*[=:]\s*)"
        r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s,;\"'<>]+)"
    ),
]
SECRET_KEY = re.compile(rf"(?i)^(?:{SECRET_NAME}|authorization)$")
HOME_PATH = re.compile(r"(?<![A-Za-z0-9_])(/home/)[^/\s]+")

FS_TOOL_HINTS = ("read", "write", "edit", "glob", "grep", "file", "patch", "ls")
SHELL_TOOL_HINTS = ("bash", "shell", "exec", "terminal", "command")
AGENT_TOOL_HINTS = ("task", "agent", "delegate")
EVAL_TOOL_HINTS = ("bench", "test", "eval", "profile", "verify")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


# ------------------------------------------------------------------ collection


class SourceCollector:
    """Gather readable blobs from a file/dir/archive/stdin with skip accounting."""

    def __init__(self):
        self.blobs: list[tuple[str, bytes]] = []
        self.warnings: list[str] = []
        self.skipped: list[dict] = []

    def _add(self, name: str, data: bytes):
        if len(data) > MAX_MEMBER_BYTES:
            self.skipped.append({"source": name, "reason": "oversize", "bytes": len(data)})
            return
        if b"\x00" in data:
            # A NUL byte is valid UTF-8 (U+0000) and reaches transcripts via
            # binary tool_result payloads. Only treat a source as genuinely
            # binary when it cannot decode as UTF-8; otherwise strip NULs so
            # the text parser recovers the real transcript (raw_sha256 is then
            # taken from the NUL-stripped bytes; the on-disk original remains
            # the canonical raw_source and the strip is recorded as a warning).
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                self.skipped.append({"source": name, "reason": "binary"})
                return
            nul = data.count(b"\x00")
            data = data.replace(b"\x00", b"")
            self.warnings.append(
                f"stripped {nul} NUL byte(s) from utf-8 text source: {name}")
        self.blobs.append((name, data))

    def collect(self, source: str):
        if source == "-":
            self._add("stdin", sys.stdin.buffer.read())
            return
        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"trace source does not exist: {path}")
        if path.is_dir():
            for item in sorted(p for p in path.rglob("*") if p.is_file()):
                rel = item.relative_to(path).as_posix()
                if item.suffix.lower() not in READ_SUFFIXES:
                    self.skipped.append({"source": rel, "reason": "unsupported_suffix"})
                    continue
                try:
                    self._add(rel, item.read_bytes())
                except OSError as exc:
                    self.warnings.append(f"cannot read {rel}: {exc}")
            return
        lower = path.name.lower()
        if lower.endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                for info in sorted(archive.infolist(), key=lambda x: x.filename):
                    if info.is_dir():
                        continue
                    if Path(info.filename).suffix.lower() not in READ_SUFFIXES:
                        self.skipped.append({"source": info.filename,
                                             "reason": "unsupported_suffix"})
                        continue
                    if info.file_size > MAX_MEMBER_BYTES:
                        self.skipped.append({"source": info.filename, "reason": "oversize",
                                             "bytes": info.file_size})
                        continue
                    self._add(info.filename, archive.read(info))
            return
        if lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
            with tarfile.open(path) as archive:
                for info in sorted(archive.getmembers(), key=lambda x: x.name):
                    if not info.isfile():
                        continue
                    if Path(info.name).suffix.lower() not in READ_SUFFIXES:
                        self.skipped.append({"source": info.name, "reason": "unsupported_suffix"})
                        continue
                    if info.size > MAX_MEMBER_BYTES:
                        self.skipped.append({"source": info.name, "reason": "oversize",
                                             "bytes": info.size})
                        continue
                    handle = archive.extractfile(info)
                    if handle:
                        self._add(info.name, handle.read())
            return
        self._add(path.name, path.read_bytes())

    def source_sha256(self) -> str:
        digest = hashlib.sha256()
        for name, data in sorted(self.blobs):
            digest.update(name.encode("utf-8", errors="surrogateescape"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(data).digest())
        return digest.hexdigest()


# ---------------------------------------------------------------- record layer


class RawRecord:
    __slots__ = ("source", "index", "value", "raw_sha256")

    def __init__(self, source: str, index: int, value, raw_sha256: str):
        self.source = source
        self.index = index
        self.value = value
        self.raw_sha256 = raw_sha256


def parse_records(blobs: list[tuple[str, bytes]], warnings: list[str]) -> list[RawRecord]:
    """Split blobs into records: whole JSON, JSONL lines, or plain text blocks."""
    records: list[RawRecord] = []
    for name, data in blobs:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
            warnings.append(f"decoded with replacement characters: {name}")
        stripped = text.strip()
        if not stripped:
            continue
        # A parsed/context markdown transcript must stay a single record even if
        # some lines inside parse as JSON (they would otherwise be split into
        # thousands of one-line records and defeat the markdown adapter).
        if _is_markdown_transcript(text):
            records.append(RawRecord(name, 1, {"text": text}, _sha(data)))
            continue
        try:
            whole = json.loads(stripped)
        except json.JSONDecodeError:
            whole = None
        if whole is not None:
            for index, value in enumerate(_unpack_json(whole), 1):
                records.append(RawRecord(name, index, value, _sha(_json_bytes(value))))
            continue
        parsed_any = False
        plain_chunks = []
        for index, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                plain_chunks.append((index, line))
                continue
            parsed_any = True
            records.append(RawRecord(name, index, value,
                                     _sha(line.encode("utf-8", errors="replace"))))
        if plain_chunks:
            if parsed_any:
                for index, line in plain_chunks:
                    records.append(RawRecord(name, index, {"text": line},
                                             _sha(line.encode("utf-8", errors="replace"))))
            else:
                records.append(RawRecord(name, 1, {"text": text}, _sha(data)))
    records.sort(key=lambda item: (item.source, item.index))
    return records


def _unpack_json(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if value.get("turns") is not None and value.get("summary") is not None:
            return [value]
        for key in ("events", "messages", "items", "records"):
            if isinstance(value.get(key), list):
                return value[key]
    return [value]


# ---------------------------------------------------------------- redaction


def _redact_string(value: str) -> tuple[str, int]:
    count = 0
    result = value
    for pattern in SECRET_PATTERNS:
        before = result
        result = pattern.sub(lambda m: (m.group(1) if m.lastindex else "") + "<redacted>",
                             result)
        count += result.count("<redacted>") - before.count("<redacted>")
    def replace_home(match):
        return match.group(1) + "<user>"
    result, n = HOME_PATH.subn(replace_home, result)
    count += n
    return result, count


def _redact(value):
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, list):
        out, count = [], 0
        for item in value:
            clean, found = _redact(item)
            out.append(clean)
            count += found
        return out, count
    if isinstance(value, dict):
        out, count = {}, 0
        for key, item in value.items():
            if isinstance(key, str) and SECRET_KEY.fullmatch(key) and item not in (None, "", "<redacted>"):
                out[key] = "<redacted>"
                count += 1
                continue
            clean, found = _redact(item)
            out[key] = clean
            count += found
        return out, count
    return value, 0


# ---------------------------------------------------------------- adapters


def _tool_family(name: str) -> str:
    lower = (name or "").lower()
    if any(token in lower for token in SHELL_TOOL_HINTS):
        return "shell"
    if any(token in lower for token in FS_TOOL_HINTS):
        return "filesystem"
    if any(token in lower for token in AGENT_TOOL_HINTS):
        return "agent"
    if any(token in lower for token in EVAL_TOOL_HINTS):
        return "evaluation"
    if any(token in lower for token in ("web", "fetch", "browser", "http")):
        return "web"
    return "unknown"


def _text_of(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "content", "output", "command"):
                    if key in item:
                        parts.append(_text_of(item[key]))
                        break
        return "\n".join(parts)
    if isinstance(value, dict):
        for key in ("text", "content", "output", "result", "command", "message"):
            if key in value:
                return _text_of(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _emit(events: list, session_id: str, seq_holder: list, actor: str, event_type: str,
          provenance: dict, text: str = "", tool=None):
    events.append({
        "schema_version": SCHEMA,
        "session_id": session_id,
        "sequence": len(events) + 1,
        "timestamp": None,
        "actor": actor,
        "event_type": event_type,
        "tool": tool,
        "content": {"text": text[:100_000]},
        "provenance": dict(provenance),
    })


def adapt_trace_export(record: RawRecord, fallback_session: str):
    """parse.py output: trace.json with {summary, turns[]} (+ attachments sidecar)."""
    value = record.value
    if not isinstance(value, dict) or not isinstance(value.get("turns"), list):
        return None, "trace_export requires {summary, turns[]}"
    summary = value.get("summary") or {}
    session_id = summary.get("session_id") or fallback_session
    events: list[dict] = []
    _emit(events, session_id, None, "system", "session_start",
          {"raw_source": record.source, "raw_record": record.index,
           "raw_sha256": record.raw_sha256, "adapter": "trace_export"},
          text=session_id)
    for turn in value["turns"]:
        role = turn.get("role", "unknown")
        text = _text_of(turn.get("content"))
        provenance = {"raw_source": record.source, "raw_record": record.index,
                      "raw_sha256": record.raw_sha256, "adapter": "trace_export"}
        if role == "user":
            _emit(events, session_id, None, "user", "user_message", provenance, text=text)
        elif role == "assistant":
            _emit(events, session_id, None, "assistant", "assistant_message", provenance,
                  text=text)
            reasoning = turn.get("reasoning")
            if reasoning:
                _emit(events, session_id, None, "assistant", "reasoning", provenance,
                      text=_text_of(reasoning))
            for tc in turn.get("tool_calls") or []:
                name = (tc.get("name") or "tool")
                args = tc.get("arguments")
                if args is None:
                    args = tc.get("arguments_raw")
                payload = _text_of(args)
                tool = {"family": _tool_family(name), "name": name, "call_id": tc.get("id")}
                _emit(events, session_id, None, "assistant", "tool_call", provenance,
                      text=payload, tool=tool)
        elif role == "tool":
            tool = {"family": _tool_family(turn.get("tool_name")),
                    "name": turn.get("tool_name"), "call_id": turn.get("tool_call_id")}
            _emit(events, session_id, None, "tool", "tool_result", provenance,
                  text=text, tool=tool)
        else:
            _emit(events, session_id, None, "system", "system_message", provenance, text=text)
    _emit(events, session_id, None, "system", "session_end",
          {"raw_source": record.source, "raw_record": record.index,
           "raw_sha256": record.raw_sha256, "adapter": "trace_export"})
    return events, None


def adapt_generic(record: RawRecord, fallback_session: str):
    """Best-effort mapping for arbitrary chat/event exports (claude/codex/opencode/...).

    Handles Claude Code native transcripts ({type, message:{role, content[block[]]}},
    sessionId): iterates the block array and emits reasoning / assistant_message /
    tool_call / tool_result events mirroring adapt_trace_export. Other generic
    exports (top-level content/role/actor) fall through to the simple path.
    """
    value = record.value
    if not isinstance(value, dict):
        return None, "generic requires a JSON object"
    session_id = (str(value.get("session_id") or value.get("sessionId")
                      or value.get("conversation_id") or value.get("thread_id"))
                  or fallback_session)
    events: list[dict] = []
    provenance = {"raw_source": record.source, "raw_record": record.index,
                  "raw_sha256": record.raw_sha256, "adapter": "generic"}

    # ---- Claude Code native transcript: block-array content under message ----
    msg = value.get("message")
    rec_type = value.get("type")
    if isinstance(msg, dict) and rec_type in ("user", "assistant", "system"):
        content = msg.get("content")
        role = msg.get("role") or rec_type
        if rec_type == "assistant" and isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "thinking":
                    _emit(events, session_id, None, "assistant", "reasoning",
                          provenance, text=_text_of(block.get("thinking")))
                elif btype == "text":
                    _emit(events, session_id, None, "assistant", "assistant_message",
                          provenance, text=_text_of(block.get("text")))
                elif btype == "tool_use":
                    name = block.get("name") or "tool"
                    # Serialize the full input dict so file_path + content
                    # (Write), command (Bash), old_string/new_string (Edit)
                    # are all preserved verbatim for code-first mining.
                    inp = block.get("input")
                    payload = (json.dumps(inp, ensure_ascii=False, sort_keys=True)
                               if isinstance(inp, (dict, list)) else _text_of(inp))
                    tool = {"family": _tool_family(name), "name": name,
                            "call_id": block.get("id")}
                    _emit(events, session_id, None, "assistant", "tool_call",
                          provenance, text=payload, tool=tool)
                # unknown block types: not silently dropped — surface as reasoning
                elif btype:
                    _emit(events, session_id, None, "assistant", "reasoning",
                          provenance, text=_text_of(block))
            return events, None
        if rec_type == "user":
            if isinstance(content, str):
                _emit(events, session_id, None, "user", "user_message",
                      provenance, text=content)
                return events, None
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result":
                        tid = block.get("tool_use_id")
                        tool = {"family": "unknown", "name": "unknown", "call_id": tid}
                        _emit(events, session_id, None, "tool", "tool_result",
                              provenance, text=_text_of(block.get("content")), tool=tool)
                    else:
                        _emit(events, session_id, None, "user", "user_message",
                              provenance, text=_text_of(block))
                return events, None
        # system record or scalar content: simple text emission
        _emit(events, session_id, None, role or "system", "system_message",
              provenance, text=_text_of(content))
        return events, None

    # ---- simple path: legacy generic exports (top-level content/role/actor) ----
    content = value.get("content")
    if content is None:
        content = value.get("text")
    text = _text_of(content)
    actor = value.get("actor") or value.get("role") or value.get("type") or "unknown"
    if actor == "assistant" or actor == "agent":
        _emit(events, session_id, None, "assistant", "assistant_message", provenance, text=text)
    elif actor == "user" or actor == "human":
        _emit(events, session_id, None, "user", "user_message", provenance, text=text)
    elif actor == "tool" or actor == "function":
        tool = {"family": "unknown", "name": value.get("name") or "tool",
                "call_id": value.get("call_id") or value.get("id")}
        _emit(events, session_id, None, "tool", "tool_result", provenance, text=text, tool=tool)
    else:
        _emit(events, session_id, None, "unknown", "unknown", provenance, text=text)
    return events, None


# ---------------------------------------------- claude code jsonl adapter (S-19/I-17)


# Claude Code session export: ~/.claude/projects/<project>/<session>.jsonl
#   modern: top-level `type` in {user, assistant, summary, system, ...}; records carry
#           sessionId/uuid/timestamp; `message.content` is a block array:
#             assistant: {type: text|thinking|tool_use} (tool_use has id/name/input)
#             user:      {type: tool_result} (has tool_use_id/content/is_error) [+ text]
#   legacy: top-level `type` directly in {user, assistant, summary, tool_call, tool_result}
CLAUDE_META_TYPES = {"mode", "permission-mode", "file-history-snapshot", "file-history-delta",
                     "ai-title", "last-prompt", "agent-name", "attachment"}


def _arg_text(value) -> str:
    """Tool-call arguments: keep the full JSON so file paths / write payloads survive."""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return _text_of(value)


def adapt_claude_code(record: RawRecord, fallback_session: str):
    """Claude Code ~/.claude/projects/**/<session>.jsonl (modern + legacy shapes)."""
    value = record.value
    if not isinstance(value, dict) or not isinstance(value.get("type"), str):
        return None, "claude_code requires a JSON object with top-level `type`"
    rtype = value["type"]
    session_id = str(value.get("sessionId") or value.get("session_id") or fallback_session)
    provenance = {"raw_source": record.source, "raw_record": record.index,
                  "raw_sha256": record.raw_sha256, "adapter": "claude_code"}
    events: list[dict] = []
    message = value.get("message")
    if rtype in ("user", "assistant") and isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    actor = "user" if rtype == "user" else "assistant"
                    _emit(events, session_id, None, actor,
                          "user_message" if actor == "user" else "assistant_message",
                          provenance, text=block.get("text"))
                elif btype == "thinking":
                    _emit(events, session_id, None, "assistant", "reasoning", provenance,
                          text=block.get("thinking") or block.get("text") or "")
                elif btype == "tool_use":
                    name = block.get("name") or "tool"
                    tool = {"family": _tool_family(name), "name": name,
                            "call_id": block.get("id")}
                    _emit(events, session_id, None, "assistant", "tool_call", provenance,
                          text=_arg_text(block.get("input")), tool=tool)
                elif btype == "tool_result":
                    tool = {"family": "unknown", "name": None,
                            "call_id": block.get("tool_use_id")}
                    text = _text_of(block.get("content"))
                    if block.get("is_error") or block.get("is_error_message"):
                        text = "[tool_error] " + text
                    _emit(events, session_id, None, "tool", "tool_result", provenance,
                          text=text, tool=tool)
        else:
            actor = "user" if rtype == "user" else "assistant"
            _emit(events, session_id, None, actor,
                  "user_message" if actor == "user" else "assistant_message",
                  provenance, text=_text_of(content))
        return events, None
    if rtype == "tool_call":  # legacy flat records
        name = value.get("name") or "tool"
        tool = {"family": _tool_family(name), "name": name,
                "call_id": value.get("tool_use_id") or value.get("id")}
        _emit(events, session_id, None, "assistant", "tool_call", provenance,
              text=_arg_text(value.get("input")), tool=tool)
        return events, None
    if rtype == "tool_result":  # legacy flat records
        tool = {"family": "unknown", "name": None,
                "call_id": value.get("tool_use_id")}
        _emit(events, session_id, None, "tool", "tool_result", provenance,
              text=_text_of(value.get("content")), tool=tool)
        return events, None
    if rtype == "summary":
        _emit(events, session_id, None, "system", "system_message", provenance,
              text=_text_of(value.get("summary")))
        return events, None
    if rtype == "system" or rtype in CLAUDE_META_TYPES:
        _emit(events, session_id, None, "system", "system_message", provenance,
              text="claude meta record type=%s" % rtype)
        return events, None
    _emit(events, session_id, None, "unknown", "unknown", provenance,
          text="claude record type=%s" % rtype)
    return events, None


# ------------------------------------------------- opencode session json adapter (S-19/I-17)


def _opencode_text(content) -> str:
    """opencode content: new dict form or legacy list-of-parts form."""
    if isinstance(content, dict):
        return _text_of(content.get("text") or content.get("content"))
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    parts.append(str(part.get("text", "")))
                else:
                    parts.append(_text_of(part))
            else:
                parts.append(str(part))
        return "\n".join(parts)
    return _text_of(content)


def adapt_opencode(record: RawRecord, fallback_session: str):
    """opencode session JSON (array or {messages:[...]}): message.info.role/tool + content."""
    value = record.value
    if not isinstance(value, dict):
        return None, "opencode requires a message object"
    info = value.get("info")
    if not isinstance(info, dict):
        info = {}
    role = info.get("role") or value.get("role") or "unknown"
    session_id = str(value.get("sessionID") or info.get("sessionID") or fallback_session)
    provenance = {"raw_source": record.source, "raw_record": record.index,
                  "raw_sha256": record.raw_sha256, "adapter": "opencode"}
    events: list[dict] = []
    content = value.get("content")
    if isinstance(content, dict) and (content.get("type") == "tool"
                                      or isinstance(content.get("tool"), dict)):
        tool_block = content.get("tool") or {}
        name = tool_block.get("name") or info.get("tool") or "tool"
        tool = {"family": _tool_family(name), "name": name,
                "call_id": tool_block.get("id") or value.get("id")}
        if role == "tool":
            _emit(events, session_id, None, "tool", "tool_result", provenance,
                  text=_text_of(content.get("output") or content.get("result")), tool=tool)
        else:
            _emit(events, session_id, None, "assistant", "tool_call", provenance,
                  text=_arg_text(content.get("input") or tool_block.get("input")), tool=tool)
        return events, None
    text = _opencode_text(content)
    if role == "user":
        _emit(events, session_id, None, "user", "user_message", provenance, text=text)
    elif role == "assistant":
        _emit(events, session_id, None, "assistant", "assistant_message", provenance, text=text)
    elif role == "tool":
        tool = {"family": _tool_family(info.get("tool")), "name": info.get("tool"),
                "call_id": value.get("id")}
        _emit(events, session_id, None, "tool", "tool_result", provenance, text=text, tool=tool)
    elif role == "system":
        _emit(events, session_id, None, "system", "system_message", provenance, text=text)
    else:
        _emit(events, session_id, None, "unknown", "unknown", provenance, text=text)
    return events, None


# ------------------------------------------------------- codex sessions adapter (S-19/I-17)


# Codex session rollout: ~/.codex/sessions/<date>/<session>.jsonl
#   line `type` in {session_meta, event_msg, turn_context, response_item}
#   response_item.payload.type in {message, function_call, function_call_output, reasoning, ...}
#     message: role + content block array (input_text/output_text) or legacy `blocks`
#     function_call: name + arguments (JSON string); function_call_output: call_id + output
#     session id lives in the session_meta payload (rolled into events via cache below)
_codex_session_ids: dict[str, str] = {}


def _codex_message_text(payload: dict) -> str:
    blocks = payload.get("content")
    if isinstance(blocks, list):
        parts = []
        for block in blocks:
            if isinstance(block, dict):
                if block.get("type") in ("input_text", "output_text", "text"):
                    parts.append(str(block.get("text", "")))
                else:
                    parts.append(_text_of(block))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return _text_of(payload.get("blocks") or payload.get("content"))


def adapt_codex(record: RawRecord, fallback_session: str):
    """Codex ~/.codex/sessions/**/<session>.jsonl rollout export."""
    value = record.value
    if not isinstance(value, dict) or not isinstance(value.get("type"), str):
        return None, "codex requires a JSON object with top-level `type`"
    rtype = value["type"]
    payload = value.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    session_id = _codex_session_ids.get(record.source, fallback_session)
    provenance = {"raw_source": record.source, "raw_record": record.index,
                  "raw_sha256": record.raw_sha256, "adapter": "codex"}
    events: list[dict] = []
    if rtype == "session_meta":
        rollout_id = payload.get("id")
        if isinstance(rollout_id, str):
            _codex_session_ids[record.source] = rollout_id
            session_id = rollout_id
        _emit(events, session_id, None, "system", "system_message", provenance,
              text="codex session_meta id=%s" % session_id)
        return events, None
    if rtype in ("event_msg", "turn_context"):
        _emit(events, session_id, None, "system", "system_message", provenance,
              text="codex meta record type=%s" % rtype)
        return events, None
    if rtype != "response_item":
        _emit(events, session_id, None, "unknown", "unknown", provenance,
              text="codex record type=%s" % rtype)
        return events, None
    ptype = payload.get("type")
    if ptype == "message":
        role = payload.get("role") or "assistant"
        text = _codex_message_text(payload)
        if role == "user":
            _emit(events, session_id, None, "user", "user_message", provenance, text=text)
        elif role == "assistant":
            _emit(events, session_id, None, "assistant", "assistant_message", provenance,
                  text=text)
        elif role == "tool":
            _emit(events, session_id, None, "tool", "tool_result", provenance, text=text)
        else:
            _emit(events, session_id, None, "system", "system_message", provenance, text=text)
        return events, None
    if ptype == "function_call":
        name = payload.get("name") or "tool"
        args = payload.get("arguments")
        tool = {"family": _tool_family(name), "name": name, "call_id": payload.get("call_id")}
        _emit(events, session_id, None, "assistant", "tool_call", provenance,
              text=_text_of(args), tool=tool)
        return events, None
    if ptype == "function_call_output":
        tool = {"family": "unknown", "name": None, "call_id": payload.get("call_id")}
        _emit(events, session_id, None, "tool", "tool_result", provenance,
              text=_text_of(payload.get("output")), tool=tool)
        return events, None
    if ptype in ("custom_tool_call", "web_search_call"):
        name = payload.get("name") or ptype
        tool = {"family": _tool_family(name), "name": name, "call_id": payload.get("call_id")}
        _emit(events, session_id, None, "assistant", "tool_call", provenance,
              text=_arg_text(payload.get("input") or payload.get("action")), tool=tool)
        return events, None
    if ptype == "custom_tool_call_output":
        tool = {"family": "unknown", "name": None, "call_id": payload.get("call_id")}
        _emit(events, session_id, None, "tool", "tool_result", provenance,
              text=_text_of(payload.get("output") or payload.get("stdout")), tool=tool)
        return events, None
    if ptype == "reasoning":
        summary = payload.get("summary")
        if isinstance(summary, list):
            text = "codex reasoning summary: " + " | ".join(str(s) for s in summary)
        else:
            text = "codex reasoning (payload encrypted/unavailable)"
        _emit(events, session_id, None, "assistant", "reasoning", provenance, text=text)
        return events, None
    _emit(events, session_id, None, "unknown", "unknown", provenance,
          text="codex response_item payload.type=%s" % ptype)
    return events, None


# ---------------------------------------------------------------- markdown transcript adapter


# Header line of the readable transcript: "# Session Transcript: <ses_id>"
MD_TRANSCRIPT_HEAD = re.compile(r"^# Session Transcript:\s*(\S+)")
# Subagent block header: "### <ses_id>  (agent_type: xxx)"
MD_SUBAGENT_HEAD = re.compile(r"^###\s+(ses_[A-Za-z0-9]+)\s*(?:\([^)]*\))?\s*$")
# Session header: "# Session Transcript: <ses_id>" (main) or "### Session Transcript: <id>" (subagent)
MD_SES_TRANSCRIPT = re.compile(r"^#{1,5}\s+Session Transcript:\s*(\S+)")
# Turn header: "## Turn N — <timestamp>" (parent) or "#### Turn N —" (subagent); also "## Turn N —" used inside subagent for nested
MD_TURN_HEAD = re.compile(r"^#{2,5}\s+Turn\s+(\d+)\s*[—-]?\s*(.*)$")
# Section header: "### User" / "### Reasoning" / "### Tool Calls" / "### Tool Results" / "### Assistant"
MD_SECTION_HEAD = re.compile(r"^#{3,6}\s+(User|Assistant|Reasoning|Tool Calls|Tool Results|System)$")
# Tool result block: "**<tool>** (call_<id>...):" inside a Tool Results section
MD_TOOL_RESULT_HEAD = re.compile(r"^\*\*(`?[^`*]+`?)\*\*\s*(?:\(([^)]*)\))?\s*:?\s*$")
# Tool call table row: "| 1 | read | `{...}` |"
MD_TOOL_CALL_ROW = re.compile(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$")
MD_BACKTICK_PAYLOAD = re.compile(r"^```(.*)$")
MD_BACKTICK_END = re.compile(r"^```\s*$")


def _strip_yaml_frontmatter(text: str) -> str:
    """Strip a leading `---\n...\n---\n` YAML frontmatter block if present."""
    if text.startswith("---\n"):
        match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
        if match:
            return text[match.end():]
    return text


def _is_markdown_transcript(text: str) -> bool:
    """Heuristic: parse output of the gateway 'parsed/context' markdown renderer.

    Real transcripts may carry a YAML frontmatter header (cannbot-obs
    parsed/transcripts/*.md), so detection strips it first (m3).
    """
    body = _strip_yaml_frontmatter(text)
    return bool(MD_TRANSCRIPT_HEAD.search(body)) and bool(re.search(r"^##\s+Turn ", body, re.MULTILINE))


def _adapt_markdown_text(text: str, source: str, raw_sha256: str) -> tuple[list[dict], list[str]]:
    """Parse a CANNBot parsed/context markdown transcript into trace.event.v1 events.

    Structure:
      # Session Transcript: <ses_id>
      ## Turn N — <ts>          (parent session turns)
        ### User / ### Reasoning / ### Tool Calls (table) / ### Tool Results (**tool** (call_id):) / ### Assistant
      ## Subagent Sessions of <parent> (N)
        ### <sub_ses_id> (agent_type: x)
          ### Session Transcript: <sub_ses_id>
          #### Turn N
            ##### User / ##### Tool Calls ...
    """
    warnings: list[str] = []
    body = _strip_yaml_frontmatter(text)
    events: list[dict] = []

    def emit(session: str, actor: str, etype: str, body: str = "", tool=None,
             record: int = 0):
        prov = {"raw_source": source, "raw_record": record,
                "raw_sha256": raw_sha256, "adapter": "markdown_transcript"}
        _emit(events, session, None, actor, etype, prov, text=body, tool=tool)

    # iterate lines; maintain a stack of (session_id, turn_index, section)
    # state machine:
    #   current_session, current_turn_idx, current_section
    # collect tool results waiting for their **tool** (call) header
    lines = body.splitlines()

    def emit_session_start(sid: str, record: int = 0):
        emit(sid, "system", "session_start", sid, record=record)

    def emit_session_end(sid: str, record: int = 0):
        emit(sid, "system", "session_end", record=record)

    # We'll track started sessions to emit session_end for each at the end.
    started: list[str] = []
    # state
    cur_session: str | None = None
    cur_turn: int | None = None
    cur_section: str | None = None
    # pending tool-result blocks: list of {tool, call_id, lines}
    pending_tool_result: dict | None = None
    # pending tool-call JSON rows that we convert on the fly
    in_tool_calls_table = False
    buf: list[str] = []          # current section body accumulator
    fenced = False               # inside ``` fence

    def flush_section():
        nonlocal buf, in_tool_calls_table, pending_tool_result
        if cur_section is None or cur_session is None:
            buf = []
            return
        body = "\n".join(buf).strip()
        if cur_section == "User":
            if body:
                emit(cur_session, "user", "user_message", body, record=cur_turn or 0)
        elif cur_section == "Assistant":
            if body:
                emit(cur_session, "assistant", "assistant_message", body, record=cur_turn or 0)
        elif cur_section == "Reasoning":
            if body:
                emit(cur_session, "assistant", "reasoning", body, record=cur_turn or 0)
        elif cur_section == "System":
            if body:
                emit(cur_session, "system", "system_message", body, record=cur_turn or 0)
        elif cur_section == "Tool Calls":
            # table rows already emitted inline; just clear buffer
            pass
        elif cur_section == "Tool Results":
            if pending_tool_result and buf:
                result_body = "\n".join(buf).strip()
                tool = {"family": _tool_family(pending_tool_result["tool"]),
                        "name": pending_tool_result["tool"],
                        "call_id": pending_tool_result["call_id"]}
                emit(cur_session, "tool", "tool_result", result_body, tool=tool,
                     record=cur_turn or 0)
            pending_tool_result = None
        buf = []
        in_tool_calls_table = False

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        # fence handling: keep everything inside fences verbatim
        if fenced:
            if MD_BACKTICK_END.match(stripped):
                buf.append(line)
                fenced = False
            else:
                buf.append(line)
            continue
        if MD_BACKTICK_PAYLOAD.match(stripped):
            buf.append(line)
            fenced = True
            continue

        # ---- structural headers ----
        m_turn = MD_TURN_HEAD.match(stripped)
        if m_turn and not stripped.startswith("### "):
            flush_section()
            cur_turn = int(m_turn.group(1))
            cur_section = None
            # a new Turn always belongs to the current session (parent or subagent)
            continue
        m_sub = MD_SUBAGENT_HEAD.match(stripped)
        if m_sub:
            flush_section()
            # entering a subagent block: switch to subagent session
            sub_id = m_sub.group(1)
            if sub_id not in started:
                emit_session_start(sub_id, record=cur_turn or 0)
                started.append(sub_id)
            cur_session = sub_id
            cur_turn = None
            cur_section = None
            continue
        m_ses = MD_SES_TRANSCRIPT.search(stripped)
        if m_ses:
            # "### Session Transcript: <id>" inside a subagent block; also the head line
            sid = m_ses.group(1)
            if sid not in started:
                emit_session_start(sid, record=cur_turn or 0)
                started.append(sid)
            cur_session = sid
            cur_turn = None
            cur_section = None
            continue
        m_section = MD_SECTION_HEAD.match(stripped)
        if m_section:
            flush_section()
            cur_section = m_section.group(1)
            if cur_section == "Tool Calls":
                in_tool_calls_table = True
            elif cur_section == "Tool Results":
                pending_tool_result = None
            continue

        # ---- tool result header: **<tool>** (call_xxx): ----
        m_tr = MD_TOOL_RESULT_HEAD.match(stripped)
        if m_tr and cur_section == "Tool Results":
            # flush previous pending result if any
            if pending_tool_result and buf:
                result_body = "\n".join(buf).strip()
                tool = {"family": _tool_family(pending_tool_result["tool"]),
                        "name": pending_tool_result["tool"],
                        "call_id": pending_tool_result["call_id"]}
                emit(cur_session, "tool", "tool_result", result_body, tool=tool,
                     record=cur_turn or 0)
            pending_tool_result = {"tool": m_tr.group(1).strip("`"),
                                   "call_id": m_tr.group(2) or None}
            buf = []
            continue

        # ---- tool call table row ----
        m_tc = MD_TOOL_CALL_ROW.match(stripped)
        if m_tc and in_tool_calls_table:
            name = m_tc.group(1).strip()
            args_raw = m_tc.group(2).strip()
            payload = args_raw.strip("`")
            tool = {"family": _tool_family(name), "name": name, "call_id": None}
            emit(cur_session, "assistant", "tool_call", payload, tool=tool,
                 record=cur_turn or 0)
            continue

        # ---- ordinary body line ----
        buf.append(line)

    flush_section()
    # close any tool result still pending
    if pending_tool_result and buf:
        result_body = "\n".join(buf).strip()
        tool = {"family": _tool_family(pending_tool_result["tool"]),
                "name": pending_tool_result["tool"],
                "call_id": pending_tool_result["call_id"]}
        emit(cur_session, "tool", "tool_result", result_body, tool=tool,
             record=cur_turn or 0)
    # close sessions (reverse order so parents end after children)
    for sid in reversed(started):
        emit_session_end(sid)
    return events, warnings


def adapt_markdown_transcript(record: RawRecord, fallback_session: str):
    """Gateway parsed/context markdown transcript (eadable session export)."""
    value = record.value
    if not isinstance(value, dict) or not isinstance(value.get("text"), str):
        return None, "markdown_transcript requires a text blob"
    events, warnings = _adapt_markdown_text(value["text"], record.source, record.raw_sha256)
    return events, warnings


def detect_adapter(records: list[RawRecord]) -> tuple[str, dict]:
    scores = {"trace_export": 0, "generic": 0, "markdown_transcript": 0,
              "claude_code": 0, "opencode": 0, "codex": 0}
    for record in records[:500]:
        value = record.value
        if not isinstance(value, dict):
            continue
        if value.get("turns") is not None and value.get("summary") is not None:
            scores["trace_export"] += 50
        elif value.get("turns") is not None or value.get("messages") is not None:
            scores["generic"] += 3
        elif "role" in value or "actor" in value or "event_type" in value:
            scores["generic"] += 1
        # Claude Code native transcript: top-level {type, message:{role,content,...}, sessionId}
        msg = value.get("message")
        if isinstance(msg, dict) and value.get("type") in ("user", "assistant", "system"):
            scores["generic"] += 3
        text = value.get("text")
        if isinstance(text, str) and _is_markdown_transcript(text):
            scores["markdown_transcript"] += 10
        rtype = value.get("type")
        if rtype in ("response_item", "session_meta", "turn_context", "event_msg"):
            scores["codex"] += 20
        if rtype in ("user", "assistant", "summary", "tool_call", "tool_result"):
            scores["claude_code"] += 10
        message = value.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), list):
            blocks = [b for b in message["content"] if isinstance(b, dict)]
            if blocks and any(b.get("type") in ("tool_use", "tool_result", "thinking")
                              for b in blocks):
                scores["claude_code"] += 10
        info = value.get("info")
        if isinstance(info, dict) and info.get("role") in ("user", "assistant", "tool", "system"):
            scores["opencode"] += 10
        content = value.get("content")
        if isinstance(content, dict) and isinstance(content.get("tool"), dict):
            scores["opencode"] += 8
    top = "generic"
    top_score = scores["generic"]
    for candidate in sorted(scores):
        if scores[candidate] > top_score:
            top, top_score = candidate, scores[candidate]
    if top_score <= 0:
        # No structural signal: never silently drop records through the
        # trace_export filter. generic keeps every record as an event.
        top = "generic"
    return top, scores


def normalize_source(collector: SourceCollector, records: list[RawRecord],
                     format_hint: str):
    detected, scores = detect_adapter(records)
    selected = format_hint if format_hint in ADAPTERS else detected
    adapters = {"trace_export": adapt_trace_export, "generic": adapt_generic,
                "markdown_transcript": adapt_markdown_transcript,
                "claude_code": adapt_claude_code, "opencode": adapt_opencode,
                "codex": adapt_codex}
    if selected == "trace_export":
        # trace.json already carries full turn content; sidecar files
        # (trace.md / summary.json / attachments/) only add noise.
        trace_records = [r for r in records if Path(r.source).name == "trace.json"]
        if trace_records:
            records = trace_records
        else:
            # Nothing looks like a trace.json after all: fall back to generic
            # instead of silently producing zero events (input may be plain text).
            selected = "generic"
    fallback_session = "session-" + collector.source_sha256()[:12]
    events: list[dict] = []
    failures = []
    for record in records:
        produced = None
        reason = None
        try:
            produced, reason = adapters[selected](record, fallback_session)
        except Exception as exc:
            failures.append({"source": record.source, "record": record.index,
                             "error": f"{type(exc).__name__}: {exc}"})
        if produced is None:
            if selected != "generic":
                produced, reason = adapt_generic(record, fallback_session)
                for event in produced or []:
                    event["provenance"]["adapter"] = selected + ":fallback-generic"
            elif reason:
                failures.append({"source": record.source, "record": record.index,
                                 "error": reason})
        if produced:
            for event in produced:
                event["sequence"] = len(events) + 1
                events.append(event)
    return selected, scores, events, failures


# ------------------------------------------------------------------- manifest


def build_manifest(collector, records, selected, scores, events, failures) -> dict:
    event_counts = collections.Counter(e["event_type"] for e in events)
    sessions = sorted({e["session_id"] for e in events})
    fs_events = [e for e in events
                 if e.get("tool") and e["tool"].get("family") == "filesystem"]
    capabilities = {
        "messages": bool(event_counts["user_message"] or event_counts["assistant_message"]),
        "tool_activity": bool(event_counts["tool_call"] or event_counts["tool_result"]),
        "file_changes": bool(event_counts["file_write"] or event_counts["file_diff"]
                             or fs_events),
        "metrics": bool(event_counts["metric"]),
        "errors": bool(event_counts["error"]),
        "reasoning": bool(event_counts["reasoning"]),
    }
    return {
        "schema_version": "trace.session.v1",
        "source": {
            "sha256": collector.source_sha256(),
            "adapter": selected,
            "detector_scores": scores,
            "raw_files": [name for name, _ in collector.blobs],
        },
        "sessions": sessions,
        "coverage": {
            "raw_records": len(records),
            "normalized_events": len(events),
            "unknown_events": event_counts["unknown"],
            "adapter_failures": len(failures),
            "skipped_sources": len(collector.skipped),
        },
        "event_types": dict(sorted(event_counts.items())),
        "capabilities": capabilities,
        "warnings": collector.warnings,
        "adapter_failure_details": failures,
        "skipped_source_details": collector.skipped,
    }


def _atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


# -------------------------------------------------------------------- verify


def verify(output: str) -> dict:
    root = Path(output).expanduser().resolve()
    trace_path = root / "normalized_trace.jsonl"
    manifest_path = root / "session_manifest.json"
    errors = []
    if not trace_path.is_file():
        errors.append("missing normalized_trace.jsonl")
    if not manifest_path.is_file():
        errors.append("missing session_manifest.json")
    if errors:
        return {"ok": False, "errors": errors, "events": 0}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "errors": [f"invalid manifest: {exc}"], "events": 0}
    required = {"schema_version", "session_id", "sequence", "timestamp", "actor",
                "event_type", "tool", "content", "provenance"}
    event_count = 0
    unknown = 0
    expected_sequence = 1
    sessions = set()
    with trace_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc}")
                continue
            missing = sorted(required - set(event))
            if missing:
                errors.append(f"line {line_number}: missing {','.join(missing)}")
            if event.get("schema_version") != SCHEMA:
                errors.append(f"line {line_number}: unsupported schema_version")
            if event.get("sequence") != expected_sequence:
                errors.append(f"line {line_number}: sequence is not contiguous")
            expected_sequence += 1
            if event.get("event_type") not in CANONICAL_TYPES:
                errors.append(f"line {line_number}: invalid event_type {event.get('event_type')!r}")
            provenance = event.get("provenance")
            if not isinstance(provenance, dict) or not all(
                    provenance.get(key) is not None
                    for key in ("raw_source", "raw_record", "raw_sha256", "adapter")):
                errors.append(f"line {line_number}: incomplete provenance")
            event_count += 1
            unknown += event.get("event_type") == "unknown"
            if event.get("session_id"):
                sessions.add(event["session_id"])
    coverage = manifest.get("coverage", {})
    if coverage.get("normalized_events") != event_count:
        errors.append("manifest normalized_events does not match trace")
    if coverage.get("unknown_events") != unknown:
        errors.append("manifest unknown_events does not match trace")
    if sorted(manifest.get("sessions", [])) != sorted(sessions):
        errors.append("manifest sessions do not match trace")
    return {"ok": not errors, "errors": errors, "events": event_count,
            "unknown_events": unknown, "sessions": len(sessions)}


# ---------------------------------------------------------------------- main


def _normalize_one(source: str, out_root: Path, fmt: str):
    """Single-source normalize (shared by `normalize` and `batch` workers).

    Returns (src_name, out_dir_rel, manifest, error). Idempotent: existing
    output dir is skipped (returns {"status": "skipped"}).
    """
    try:
        collector = SourceCollector()
        collector.collect(source)
        records = parse_records(collector.blobs, collector.warnings)
        if not records:
            return source, None, {"status": "error", "error": "no records"}, None
        out_dir = out_root / collector.source_sha256()[:12]
        if (out_dir / "normalized_trace.jsonl").exists() and (out_dir / "session_manifest.json").exists():
            return source, out_dir.name, {"status": "skipped"}, None
        selected, scores, events, failures = normalize_source(
            collector, records, fmt if fmt != "auto" else "auto")
        redactions = 0
        for index, event in enumerate(events):
            events[index], found = _redact(event)
            redactions += found
        manifest = build_manifest(collector, records, selected, scores, events, failures)
        manifest["coverage"]["redactions"] = redactions
        _atomic_write(out_dir / "normalized_trace.jsonl",
                      "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n"
                              for e in events))
        _atomic_write(out_dir / "session_manifest.json",
                      json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return source, out_dir.name, manifest, None
    except Exception as exc:  # keep batch resilient: one bad file cannot kill the run
        return source, None, {"status": "error", "error": "%s: %s" % (type(exc).__name__, exc)}, None


def cmd_batch(source_dir: str, out_root: Path, workers: int, fmt: str):
    """Normalize every *.md under a directory, in parallel, idempotently."""
    files = sorted(str(p) for p in Path(source_dir).expanduser().resolve().rglob("*.md"))
    if not files:
        raise SystemExit("batch: no *.md files under %s" % source_dir)
    ctx = multiprocessing.get_context("fork") if "fork" in multiprocessing.get_all_start_methods() else multiprocessing.get_context()
    n = workers if workers > 0 else max(1, (os.cpu_count() or 4) - 1)
    with ctx.Pool(n) as pool:
        results = pool.starmap(_normalize_one, [(f, out_root, fmt) for f in files])
    entries = []
    for src, out_name, manifest, _ in results:
        if out_name is None:
            entries.append({"src": src, "sha256": None, "status": "error",
                            "error": (manifest or {}).get("error")})
        elif manifest.get("status") == "skipped":
            entries.append({"src": src, "sha256": None, "status": "skipped"})
        else:
            entries.append({
                "src": src,
                "sha256": manifest["source"]["sha256"],
                "sha12": manifest["source"]["sha256"][:12],
                "output": str(out_root / out_name),
                "adapter": manifest["source"]["adapter"],
                "events": manifest["coverage"]["normalized_events"],
                "unknown": manifest["coverage"]["unknown_events"],
                "redactions": manifest["coverage"]["redactions"],
                "status": "ok",
            })
    out_root.mkdir(parents=True, exist_ok=True)
    _atomic_write(out_root / "batch_manifest.json",
                  json.dumps({"source_dir": str(Path(source_dir).expanduser().resolve()),
                              "total": len(entries),
                              "ok": sum(1 for e in entries if e["status"] == "ok"),
                              "skipped": sum(1 for e in entries if e["status"] == "skipped"),
                              "error": sum(1 for e in entries if e["status"] == "error"),
                              "entries": entries},
                             ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"output": str(out_root), "total": len(entries),
                      "ok": sum(1 for e in entries if e["status"] == "ok"),
                      "skipped": sum(1 for e in entries if e["status"] == "skipped"),
                      "error": sum(1 for e in entries if e["status"] == "error")},
                     ensure_ascii=False, indent=2, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic normalization of agent traces -> trace.event.v1")
    sub = parser.add_subparsers(dest="command", required=True)

    detect_cmd = sub.add_parser("detect", help="detect source adapter without writing output")
    detect_cmd.add_argument("source")
    detect_cmd.add_argument("--format", choices=ADAPTERS + ["auto"], default="auto")

    normalize_cmd = sub.add_parser("normalize", help="write normalized_trace.jsonl + manifest")
    normalize_cmd.add_argument("source")
    normalize_cmd.add_argument("--format", choices=ADAPTERS + ["auto"], default="auto")
    normalize_cmd.add_argument("--output", default=None,
                               help="default: <build>/trace-normalized/<source-sha12>")

    batch_cmd = sub.add_parser("batch", help="normalize all *.md under a directory (multiprocessing, idempotent)")
    batch_cmd.add_argument("source", help="directory containing ses_*.md transcripts")
    batch_cmd.add_argument("--output", default=None,
                           help="default: <build>/batch-<YYYY-MM-DD>/trace-normalized")
    batch_cmd.add_argument("--workers", type=int, default=0, help="0 = cpu_count-1")
    batch_cmd.add_argument("--format", choices=ADAPTERS + ["auto"], default="auto")

    verify_cmd = sub.add_parser("verify", help="verify a normalized output directory")
    verify_cmd.add_argument("output")

    args = parser.parse_args()
    if args.command == "batch":
        out_root = Path(args.output).expanduser().resolve() if args.output else (
            Path(__file__).resolve().parents[4] / ".build"
            / ("batch-" + __import__("datetime").date.today().isoformat()) / "trace-normalized")
        cmd_batch(args.source, out_root, args.workers, args.format)
        return
    if args.command == "detect":
        collector = SourceCollector()
        collector.collect(args.source)
        records = parse_records(collector.blobs, collector.warnings)
        selected, scores = detect_adapter(records)
        print(json.dumps({
            "source_sha256": collector.source_sha256(),
            "selected_adapter": selected,
            "format_hint": args.format,
            "detector_scores": scores,
            "raw_files": [name for name, _ in collector.blobs],
            "raw_records": len(records),
            "warnings": collector.warnings,
            "skipped_sources": collector.skipped,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.command == "normalize":
        collector = SourceCollector()
        collector.collect(args.source)
        records = parse_records(collector.blobs, collector.warnings)
        if not records:
            raise SystemExit("trace source contained no records")
        selected, scores, events, failures = normalize_source(
            collector, records, args.format if args.format != "auto" else "auto")
        redactions = 0
        for index, event in enumerate(events):
            events[index], found = _redact(event)
            redactions += found
        manifest = build_manifest(collector, records, selected, scores, events, failures)
        manifest["coverage"]["redactions"] = redactions
        out_dir = Path(args.output).expanduser().resolve() if args.output else (
            Path(__file__).resolve().parents[4] / ".build" / "trace-normalized"
            / collector.source_sha256()[:12])
        _atomic_write(out_dir / "normalized_trace.jsonl",
                      "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n"
                              for e in events))
        _atomic_write(out_dir / "session_manifest.json",
                      json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"output": str(out_dir), "source": manifest["source"],
                          "coverage": manifest["coverage"],
                          "capabilities": manifest["capabilities"]},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return
    result = verify(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
