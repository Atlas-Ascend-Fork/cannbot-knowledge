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
import base64
import binascii
import contextvars
import copy
import hashlib
import hmac
import json
import os
import re
import secrets
import uuid
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
import urllib.parse
from urllib.parse import unquote, unquote_plus

import httpx
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
SKILL_SCRIPTS = REPO_ROOT / ".agents/skills/knowledge-query/scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from pydantic import Field  # noqa: E402
from mcp.server.auth.provider import AccessToken, ProviderTokenVerifier  # noqa: E402
import api_keys  # noqa: E402
import state_store  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import HTMLResponse, JSONResponse, Response  # noqa: E402

from retrieval.index import open_index  # noqa: E402
from retrieval.root import ENV_KEY, resolve_root  # noqa: E402

from log_uploader import LogUploader  # noqa: E402

TRANSPORT_ENV = "CANNBOT_MCP_TRANSPORT"
HOST_ENV = "CANNBOT_MCP_HOST"
PORT_ENV = "CANNBOT_MCP_PORT"
TOKENS_ENV = "CANNBOT_MCP_TOKENS"
RATE_LIMIT_ENV = "CANNBOT_MCP_RATE_LIMIT"
RATE_KEY_ENV = "CANNBOT_MCP_RATE_KEY"
GITCODE_VERIFY_ENV = "CANNBOT_MCP_GITCODE_VERIFY"
GITCODE_API_ENV = "CANNBOT_MCP_GITCODE_API"
AUTH_SECRET_ENV = "CANNBOT_MCP_AUTH_SECRET"
PUBLIC_PATH_ENV = "CANNBOT_MCP_PUBLIC_PATH"
ACCESS_TTL_ENV = "CANNBOT_MCP_ACCESS_TTL_S"
REFRESH_TTL_ENV = "CANNBOT_MCP_REFRESH_TTL_S"
DEVICE_TTL_ENV = "CANNBOT_MCP_DEVICE_TTL_S"
DEVICE_INTERVAL_ENV = "CANNBOT_MCP_DEVICE_INTERVAL_S"
AUTH_DB_ENV = "CANNBOT_MCP_AUTH_DB"
AUTH_SERVER_ENV = "CANNBOT_MCP_AUTH_SERVER"
SDK_AUTH_ENV = "CANNBOT_MCP_SDK_AUTH"
GITCODE_AUTHORIZE_URL = "https://gitcode.com/oauth/authorize"
GITCODE_TOKEN_URL = "https://gitcode.com/oauth/token"
OAUTH_CLIENT_ID_ENV = "CANNBOT_MCP_OAUTH_CLIENT_ID"
OAUTH_CLIENT_SECRET_ENV = "CANNBOT_MCP_OAUTH_CLIENT_SECRET"
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
DEFAULT_AUTH_KEY_PATH = DEFAULT_LOG_DIR / "auth.key"
DEFAULT_AUTH_DB_PATH = DEFAULT_LOG_DIR / "auth.db"
# No default upload remote: the feature is opt-in. An empty remote means
# the uploader is not constructed unless the deployer sets
# CANNBOT_MCP_LOG_UPLOAD_REMOTE explicitly (checked in _start_uploader).
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

def _env_int(name: str, default: int) -> int:
    # Defined before the first construct-time consumer
    # (SelfIssuedTokenAuthority at import time in SDK-auth-on wiring);
    # pure helper over os.environ, no module-level dependencies.
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
    """Sliding-window limiter backed by the shared StateStore event stream.

    Every allowed request appends one event under ``rl:<key>`` and the
    decision counts the trailing window, so replicas share one global
    limit instead of one per process. As in the in-memory version this
    replaces, the count is checked before appending: a rejected request
    does not consume a slot. ``retry_after`` is the conservative
    full-window bound: the store exposes counts, not timestamps, so the
    exact time until the oldest event leaves the window is no longer
    known.
    """

    def __init__(self, store: state_store.StateStore) -> None:
        self._store = store

    def check(self, key: str, *, limit: int, window_s: float = 60.0) -> RateDecision:
        if limit <= 0:
            return RateDecision(True)
        if self._store.count(f"rl:{key}", window_s) >= limit:
            return RateDecision(False, max(1, int(window_s) + 1))
        self._store.record(f"rl:{key}")
        return RateDecision(True)

    def close(self) -> None:
        """No-op: the backing store is owned and closed by the caller."""

class IpCooldown:
    """Temporary block for source IPs with repeated authentication failures.

    Failure events accumulate in the shared StateStore under a
    generation-namespaced key ``cd:<ip>:<gen>`` (60-second window); when
    the count reaches the limit an explicit ban key ``cd:block:<ip>`` is
    written for the block duration. Replicas share one global cooldown
    instead of one per process, and the ban is a stored state, not a
    derived one, so it does not flicker as events age out mid-ban.

    ``record_success`` restores the observable semantics exactly: bumping
    the generation namespaces subsequent failures under a fresh key, so
    the old history stops counting immediately (the orphaned events
    simply age out of their own TTL) and the ban is lifted. It takes a
    fresh full set of failures to re-ban, same as before.
    """

    def __init__(self, store: state_store.StateStore) -> None:
        self._store = store

    def _generation_key(self, ip: str) -> str:
        return f"cd:gen:{ip}"

    def _current_key(self, ip: str) -> str:
        generation = self._store.get(self._generation_key(ip)) or "0"
        return f"cd:{ip}:{generation}"

    def check(self, ip: str) -> RateDecision:
        if self._store.get(f"cd:block:{ip}") is not None:
            return RateDecision(False, max(1, int(_AUTH_BLOCK_S)))
        return RateDecision(True)

    def record_failure(self, ip: str) -> None:
        key = self._current_key(ip)
        self._store.record(key)
        if (
            self._store.count(key, _AUTH_FAILURE_WINDOW_S)
            >= _AUTH_FAILURE_LIMIT
        ):
            self._store.put(f"cd:block:{ip}", "1", _AUTH_BLOCK_S)

    def record_success(self, ip: str) -> None:
        # Lift the current ban and namespace the failure history away:
        # bump the generation so the next failure starts counting fresh.
        self._store.take(f"cd:block:{ip}")
        generation = self._store.get(self._generation_key(ip)) or "0"
        try:
            next_generation = str(int(generation) + 1)
        except ValueError:
            next_generation = "0"
        self._store.put(
            self._generation_key(ip), next_generation, _AUTH_FAILURE_WINDOW_S
        )

    def close(self) -> None:
        """No-op: the backing store is owned and closed by the caller."""

class GitCodeTokenVerifier:
    """Verify GitCode access tokens against the public user API."""

    _CACHE_TTL_S = 60.0
    _DEFAULT_API_BASE = "https://api.gitcode.com"

    def __init__(self) -> None:
        api_base = (
            os.environ.get(GITCODE_API_ENV, "").strip().rstrip("/")
            or self._DEFAULT_API_BASE
        )
        self._user_url = f"{api_base}/api/v5/user"
        self._cache: dict[str, tuple[float, AccessToken | None]] = {}
        self._lock = threading.Lock()

    async def verify_token(self, token: str) -> AccessToken | None:
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(token)
            if cached is not None and cached[0] > now:
                return cached[1]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._user_url,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError:
            # Network errors are transient (gateway down, timeouts): do not
            # negatively cache them, or a brief outage would 401 human users
            # into the IP cooldown for a full window.
            return None

        verified: AccessToken | None = None
        cacheable = 200 <= response.status_code < 500
        if response.status_code == 200:
            try:
                login = response.json().get("login")
            except ValueError:
                login = None
            if login:
                verified = AccessToken(
                    token=token,
                    client_id=login,
                    scopes=["mcp"],
                    subject=login,
                )
        if not cacheable:
            # 5xx: server-side trouble, retry next request instead of locking
            # a None into the cache for the whole TTL.
            return verified

        with self._lock:
            self._cache[token] = (time.monotonic() + self._CACHE_TTL_S, verified)
        return verified


def _looks_like_jwt(token: str) -> bool:
    """True for compact JWS tokens (``header.payload.signature``)."""
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        return False
    return all(
        set(part) <= set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        )
        for part in parts
    )


def _is_self_issued_jwt(token: str) -> bool:
    """Structurally marks one of OUR JWTs, checked WITHOUT verification.

    Our tokens carry a custom payload claim ``typ`` with the value
    ``access`` or ``refresh`` (GitCode OAuth tokens do not). The /mcp auth
    chain uses this to route a JWT-shaped credential to local-only
    verification — including our refresh tokens, which fail the access
    check and are then rejected locally — so a self-issued credential can
    never be sent to GitCode in an outbound Authorization header. Foreign
    JWT-shaped tokens (e.g. GitCode OAuth access tokens) lack the marker
    and still take the GitCode track.
    """
    if not _looks_like_jwt(token):
        return False
    try:
        payload = json.loads(
            SelfIssuedTokenAuthority._b64url_decode(token.split(".")[1])
        )
    except (ValueError, binascii.Error):
        return False
    return isinstance(payload, dict) and payload.get("typ") in (
        SelfIssuedTokenAuthority._TYP_ACCESS,
        SelfIssuedTokenAuthority._TYP_REFRESH,
    )


class SelfIssuedTokenAuthority:
    """Signs and verifies HS256 JWTs for the self-hosted auth server leg.

    Tokens carry ``sub`` (username), ``typ`` (``access``/``refresh``),
    ``aud`` (this service's canonical URL, per MCP 2026-07-28 / RFC 8707
    audience binding), ``exp`` and ``iat``. The signing key comes from
    ``CANNBOT_MCP_AUTH_SECRET``; when unset, a random 32-byte key is
    generated once and persisted (mode 0600) under the state directory so
    tokens survive restarts. Rotating the key (setting the env var or
    deleting the file) invalidates all outstanding tokens. Implemented
    with the standard library only.
    """

    _TYP_ACCESS = "access"
    _TYP_REFRESH = "refresh"

    def __init__(self) -> None:
        self._secret = self._load_secret()
        self._access_ttl_s = _env_int(ACCESS_TTL_ENV, 7 * 24 * 3600)
        self._refresh_ttl_s = _env_int(REFRESH_TTL_ENV, 30 * 24 * 3600)

    def refresh_remaining_s(self, token: str) -> int:
        """Seconds until this (verified) refresh token expires; 0 if
        unreadable. Used to size the one-time-use ledger entry so an id is
        kept exactly as long as the token it voids could still be replayed.
        """
        parts = token.split(".")
        if len(parts) != 3:
            return 0
        try:
            payload = json.loads(self._b64url_decode(parts[1]))
        except (ValueError, binascii.Error):
            return 0
        if not isinstance(payload, dict):
            return 0
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)):
            return 0
        return max(0, int(exp - time.time()))

    @staticmethod
    def _load_secret() -> bytes:
        raw = (os.environ.get(AUTH_SECRET_ENV) or "").strip()
        if raw:
            return raw.encode()
        path = DEFAULT_AUTH_KEY_PATH
        try:
            data = path.read_bytes().strip()
            if data:
                return data
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(
                f"cannbot-mcp: cannot read auth key {path}: {exc}; "
                "falling back to an ephemeral key (tokens will not survive restarts)",
                file=sys.stderr,
            )
            return secrets.token_bytes(32)
        key = secrets.token_bytes(32)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as fh:
                fh.write(key)
        except OSError as exc:
            print(
                f"cannbot-mcp: cannot persist auth key {path}: {exc}; "
                "using an ephemeral key (tokens will not survive restarts)",
                file=sys.stderr,
            )
        return key

    def _ttl_for(self, token_type: str) -> int:
        if token_type == self._TYP_REFRESH:
            return self._refresh_ttl_s
        return self._access_ttl_s

    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    @staticmethod
    def _b64url_decode(part: str) -> bytes:
        padding = "=" * (-len(part) % 4)
        return base64.urlsafe_b64decode(part + padding)

    def _sign(self, signing_input: bytes) -> bytes:
        return hmac.new(self._secret, signing_input, hashlib.sha256).digest()

    def sign(
        self,
        username: str,
        token_type: str,
        audience: str = "",
        jti: str = "",
    ) -> tuple[str, int]:
        """Issue a JWT; returns ``(token, expires_in_seconds)``.

        ``audience`` empty falls back to ``CANNBOT_MCP_PUBLIC_URL`` or
        ``http://127.0.0.1:8090``; every token is audience-bound.
        ``jti`` (refresh tokens only): unique id enabling one-time-use
        bookkeeping by the caller. When empty a random one is generated —
        every token then differs even when minted in the same second.
        """
        if token_type not in (self._TYP_ACCESS, self._TYP_REFRESH):
            raise ValueError(f"unknown token type: {token_type!r}")
        now = int(time.time())
        ttl = self._ttl_for(token_type)
        aud = audience or self._default_audience()
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": username,
            "typ": token_type,
            "aud": aud,
            "iat": now,
            "exp": now + ttl,
            "jti": jti or uuid.uuid4().hex,
        }
        head_b = self._b64url(json.dumps(header, separators=(",", ":")).encode())
        body_b = self._b64url(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{head_b}.{body_b}".encode()
        sig_b = self._b64url(self._sign(signing_input))
        return f"{head_b}.{body_b}.{sig_b}", ttl

    @staticmethod
    def _default_audience(scope: dict[str, Any] | None = None) -> str:
        """Audience used when none is given.

        Mirrors ``_public_url``: PUBLIC_URL env, else the request's Host
        header, else ``http://localhost``. Keeping the same derivation
        means a token minted on a request (aud = _public_url(scope)) is
        verifiable on a later request whose scope carries the same Host.
        """
        public_url = os.environ.get("CANNBOT_MCP_PUBLIC_URL")
        if public_url:
            return public_url.strip().rstrip("/")
        if scope is not None:
            request_host = _http_headers(scope).get("host")
            if not request_host:
                request_host = (scope.get("server") or ("localhost",))[0]
            return f"http://{request_host}".rstrip("/")
        return "http://localhost"

    def verify(
        self,
        token: str,
        token_type: str | None = None,
        audience: str | None = None,
    ) -> tuple[str, str] | None:
        """Verify a JWT; returns ``(username, token_type)`` or ``None``.

        ``audience`` None checks against the default audience (this
        service); an explicit value must match the token's ``aud``. Tokens
        without an ``aud`` claim are rejected (audience binding is a MUST
        in MCP 2026-07-28).
        """
        parts = token.split(".")
        if len(parts) != 3:
            return None
        head_b, body_b, sig_b = parts
        try:
            header = json.loads(self._b64url_decode(head_b))
            payload = json.loads(self._b64url_decode(body_b))
            signature = self._b64url_decode(sig_b)
        except (ValueError, binascii.Error):
            return None
        if not isinstance(header, dict) or header.get("alg") != "HS256":
            return None
        expected = self._sign(f"{head_b}.{body_b}".encode())
        if not hmac.compare_digest(signature, expected):
            return None
        if not isinstance(payload, dict):
            return None
        sub = payload.get("sub")
        typ = payload.get("typ")
        aud = payload.get("aud")
        if not isinstance(sub, str) or not sub or not isinstance(typ, str):
            return None
        if not isinstance(aud, str) or not aud:
            return None  # audience binding is mandatory
        if token_type is not None and typ != token_type:
            return None
        if not hmac.compare_digest(aud, audience or self._default_audience()):
            return None
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)):
            return None
        if time.time() >= exp:
            return None
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            return None  # one-time bookkeeping requires a jti
        return sub, typ

    @staticmethod
    def token_jti(token: str) -> str | None:
        """Extract the ``jti`` claim without verification (helper for the
        one-time-use ledger: the caller verifies the signature first, then
        books the id)."""
        parts = token.split(".")
        if len(parts) != 3:
            return None
        try:
            payload = json.loads(SelfIssuedTokenAuthority._b64url_decode(parts[1]))
        except (ValueError, binascii.Error):
            return None
        jti = payload.get("jti") if isinstance(payload, dict) else None
        return jti if isinstance(jti, str) and jti else None

class DeviceCodeSession:
    """One device-authorization request (RFC 8628), from code to verdict."""

    def __init__(
        self, device_code: str, user_code: str, created_at: float, expires_at: float
    ) -> None:
        self.device_code = device_code
        self.user_code = user_code
        self.created_at = created_at
        self.expires_at = expires_at
        self.state = "pending"
        self.username: str | None = None

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


class AuthCodeSession:
    """One authorization-code grant against THIS server (RFC 6749 §4.1).

    Self-hosted mode serves browser clients (Claude Code style) that only
    speak the authorization-code flow. Unlike GitCode, WE implement RFC 8252
    §7.3: loopback redirect URIs match on scheme/host/path, any port.
    """

    def __init__(
        self,
        code: str,
        redirect_uri: str,
        code_challenge: str,
        state: str,
        created_at: float,
        expires_at: float,
        resource: str = "",
    ) -> None:
        self.code = code
        self.redirect_uri = redirect_uri
        self.code_challenge = code_challenge
        self.state = state
        self.created_at = created_at
        self.expires_at = expires_at
        self.resource = resource
        self.username: str | None = None

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


class AuthCodeStore:
    """StateStore-backed authorization-code grants (RFC 6749 §4.1).

    Each session is one JSON value under a single StateStore key
    ``ac:<code>`` — the code is a 32-byte ``token_urlsafe`` nonce, so no
    second index key is needed. The initial mint is stored with the
    full TTL and a re-publish uses the seconds remaining to the
    session's absolute ``expires_at``, so entries lapse with no
    background cleanup, and multi-node deployments share the store —
    authorize, approve and exchange may land on different nodes.
    Binding the confirmed identity is a compare-and-swap
    (``take_if_equal``) against the exact value just read: racing
    approvers race, exactly one wins. The token exchange is one-shot
    via ``take`` — the authorization code is a single-use nonce, so a
    repeat consume sees nothing. The store itself is owned (and
    closed) by the caller.
    """

    _TTL_S = 600.0

    def __init__(self, store: state_store.StateStore) -> None:
        self._store = store

    @staticmethod
    def _value(
        code: str,
        redirect_uri: str,
        code_challenge: str,
        state: str,
        username: str | None,
        created_at: float,
        expires_at: float,
        resource: str,
    ) -> str:
        """Serialize one session; ``username`` None round-trips as JSON null."""
        return json.dumps(
            {
                "code": code,
                "redirect_uri": redirect_uri,
                "code_challenge": code_challenge,
                "state": state,
                "username": username,
                "created_at": created_at,
                "expires_at": expires_at,
                "resource": resource,
            }
        )

    @staticmethod
    def _session_from_value(raw: str) -> AuthCodeSession | None:
        """Decode one stored value; ``None`` when it is unreadable."""
        try:
            data = json.loads(raw)
            session = AuthCodeSession(
                data["code"],
                data["redirect_uri"],
                data["code_challenge"],
                data["state"],
                data["created_at"],
                data["expires_at"],
                data["resource"] or "",
            )
            session.username = data["username"]
        except (ValueError, KeyError, TypeError):
            return None
        return session

    def create(
        self,
        redirect_uri: str,
        code_challenge: str,
        state: str,
        resource: str = "",
    ) -> AuthCodeSession:
        """Mint a pending grant; the code is a fresh single-use nonce."""
        code = secrets.token_urlsafe(32)
        now = time.time()
        session = AuthCodeSession(
            code,
            redirect_uri,
            code_challenge,
            state,
            now,
            now + self._TTL_S,
            resource,
        )
        self._store.put(
            "ac:" + code,
            self._value(
                code,
                redirect_uri,
                code_challenge,
                state,
                None,
                now,
                session.expires_at,
                resource,
            ),
            self._TTL_S,
        )
        return session

    def lookup(self, code: str) -> AuthCodeSession | None:
        """Authorize leg: find a still-usable session by code."""
        raw = self._store.get("ac:" + code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None or session.expired or session.username is not None:
            return None  # expired or already consumed (one-shot)
        return session

    def bind(self, code: str, username: str) -> AuthCodeSession | None:
        """Bind the confirmed identity; the code is consumed on exchange.

        ``take_if_equal`` against the exact value just read makes the
        binding atomic across nodes: only one binder wins, the loser
        gets None. The winner re-publishes the value with the username
        bound, under the TTL left to the session's absolute expiry.
        """
        raw = self._store.get("ac:" + code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None or session.expired or session.username is not None:
            return None
        updated = self._value(
            session.code,
            session.redirect_uri,
            session.code_challenge,
            session.state,
            username,
            session.created_at,
            session.expires_at,
            session.resource,
        )
        if not self._store.take_if_equal("ac:" + code, raw):
            return None  # another node bound or consumed first
        self._store.put("ac:" + code, updated, session.expires_at - time.time())
        session.username = username
        return session

    def consume(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> AuthCodeSession | None:
        """One-shot exchange: validates PKCE and redirect, removes the code.

        The token endpoint must hand out tokens exactly once per grant:
        ``take`` reads and removes the key in one atomic step, so a
        repeat consume sees nothing. An unbound or expired grant yields
        None — the identity binding is mandatory.
        """
        raw = self._store.take("ac:" + code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None:
            return None
        if session.expired or session.username is None:
            return None
        if not _loopback_redirect_match(session.redirect_uri, redirect_uri):
            return None
        # PKCE is enforced at mint time (the authorize endpoint rejects
        # grants without a challenge), so a missing challenge here means a
        # tampered/stale row rather than a pre-PKCE grant — fail closed.
        if not session.code_challenge:
            return None
        digest = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()
        if not hmac.compare_digest(digest, session.code_challenge):
            return None
        return session

    def close(self) -> None:
        """No-op: the StateStore is owned and closed by the caller."""

def _loopback_redirect_match(registered: str, presented: str) -> bool:
    """RFC 8252 §7.3: loopback redirects match ignoring the port."""
    try:
        a, b = urllib.parse.urlsplit(registered), urllib.parse.urlsplit(presented)
    except ValueError:
        return False
    if a.scheme != b.scheme or a.path != b.path or a.query != b.query:
        return False
    loopback = {"localhost", "127.0.0.1", "::1"}
    if a.hostname in loopback and b.hostname in loopback:
        return True
    return a.netloc == b.netloc

class DeviceCodeStore:
    """StateStore-backed device-authorization sessions (RFC 8628 §3.1-3.5).

    Each session is one JSON value double-written under two StateStore
    keys: ``dev:<device_code>`` serves the polling leg and ``devu:<user_code>``
    is the activation-leg index. Every put uses the seconds remaining to
    the session's absolute ``expires_at``, so both copies lapse together
    with no background cleanup, and multi-node deployments share the
    store — activation and polling may land on different nodes. The
    pending → allowed/denied transition is a compare-and-swap on the
    index key (``take_if_equal``): racing approvers race, exactly one
    wins. Token exchange is one-shot via ``take`` on the polling key.
    Codes are terminal: once ``allowed`` or ``denied`` the state never
    changes again, and expired codes are rejected on both legs. The
    store itself is owned (and closed) by the caller.
    """

    _ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I for readability

    def __init__(self, store: state_store.StateStore) -> None:
        self._store = store
        self._ttl_s = _env_int(DEVICE_TTL_ENV, 600)

    @staticmethod
    def _value(
        device_code: str,
        user_code: str,
        state: str,
        username: str | None,
        created_at: float,
        expires_at: float,
    ) -> str:
        """Serialize one session; ``username`` None round-trips as JSON null."""
        return json.dumps(
            {
                "device_code": device_code,
                "user_code": user_code,
                "state": state,
                "username": username,
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

    @staticmethod
    def _session_from_value(raw: str) -> DeviceCodeSession | None:
        """Decode one stored value; ``None`` when it is unreadable."""
        try:
            data = json.loads(raw)
            session = DeviceCodeSession(
                data["device_code"],
                data["user_code"],
                data["created_at"],
                data["expires_at"],
            )
            session.state = data["state"]
            session.username = data["username"]
        except (ValueError, KeyError, TypeError):
            return None
        return session

    def create(self) -> tuple[str, str]:
        """Create a pending session; returns ``(device_code, user_code)``."""
        while True:
            device_code = secrets.token_urlsafe(32)
            user_code = "-".join(
                "".join(secrets.choice(self._ALPHABET) for _ in range(4))
                for _ in range(2)
            )
            if self._store.get("devu:" + user_code) is not None:
                continue  # live user_code collision: regenerate (rare)
            now = time.time()
            expires_at = now + self._ttl_s
            value = self._value(
                device_code, user_code, "pending", None, now, expires_at
            )
            ttl_s = expires_at - now
            self._store.put("devu:" + user_code, value, ttl_s)
            self._store.put("dev:" + device_code, value, ttl_s)
            return device_code, user_code

    def lookup(self, user_code: str) -> DeviceCodeSession | None:
        """Activation leg: find a still-usable session by user code."""
        raw = self._store.get("devu:" + user_code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None or session.expired or session.state != "pending":
            return None
        return session

    def allow(self, user_code: str, username: str) -> DeviceCodeSession | None:
        """Bind a username and mark allowed; terminal unless already decided."""
        return self._decide(user_code, "allowed", username)

    def deny(self, user_code: str) -> DeviceCodeSession | None:
        """Mark denied; terminal unless already decided."""
        return self._decide(user_code, "denied", None)

    def _decide(
        self, user_code: str, state: str, username: str | None
    ) -> DeviceCodeSession | None:
        """CAS the pending index entry into a terminal state, then re-publish.

        ``take_if_equal`` against the exact value just read makes the
        transition atomic across nodes: only one decider wins, the loser
        gets None. The winner double-writes the updated value to both
        keys with the TTL left to the session's absolute expiry.
        """
        raw = self._store.get("devu:" + user_code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None or session.expired or session.state != "pending":
            return None
        updated = self._value(
            session.device_code,
            session.user_code,
            state,
            username,
            session.created_at,
            session.expires_at,
        )
        if not self._store.take_if_equal("devu:" + user_code, raw):
            return None  # another node decided or consumed first
        ttl_s = session.expires_at - time.time()
        self._store.put("devu:" + user_code, updated, ttl_s)
        self._store.put("dev:" + session.device_code, updated, ttl_s)
        session.state = state
        session.username = username
        return session

    def poll(self, device_code: str) -> DeviceCodeSession | None:
        """Polling leg by device code; terminal states still resolve."""
        raw = self._store.get("dev:" + device_code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None or session.expired:
            return None
        return session

    def consume(self, device_code: str) -> DeviceCodeSession | None:
        """Atomically take out an allowed session (RFC 8628 one-shot tokens).

        The token endpoint must hand out tokens exactly once per device
        authorization: ``take`` reads and removes the polling-leg key in
        one atomic step, so a repeat consume sees nothing. A session that
        is not ``allowed`` or is expired yields None; its activation-leg
        index then lingers only until its own TTL lapses (lookup filters
        it by state). A successful consume also clears the index with a
        compare-and-delete — but only when the entry still holds this
        exact session; a mismatched entry (user-code reuse after an
        expiry boundary) belongs to another live session and stays.
        """
        raw = self._store.take("dev:" + device_code)
        if raw is None:
            return None
        session = self._session_from_value(raw)
        if session is None or session.expired or session.state != "allowed":
            return None
        self._store.take_if_equal("devu:" + session.user_code, raw)
        return session

    def close(self) -> None:
        """No-op: the StateStore is owned and closed by the caller."""

    @property
    def ttl_s(self) -> int:
        return self._ttl_s

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

def _gitcode_verify_enabled() -> bool:
    """CANNBOT_MCP_GITCODE_VERIFY: 'off' disables the GitCode auth track."""
    return (os.environ.get(GITCODE_VERIFY_ENV) or "").strip().lower() != "off"

def _sdk_auth_enabled() -> bool:
    """CANNBOT_MCP_SDK_AUTH: 'on' mounts the official MCP SDK auth stack.

    Empty (default) keeps the handwritten auth chain exactly as it is
    today: this is the phase-1 rollout switch of
    the SDK_AUTH flag, so a deployment reverts by unsetting
    the env and restarting (no data migration, no dual write).
    """
    return (os.environ.get(SDK_AUTH_ENV) or "").strip().lower() == "on"

# Shared auth-stack singletons, populated at import time only when
# CANNBOT_MCP_SDK_AUTH=on (all None otherwise, i.e. the default legacy
# wiring). The token authority is the one build_http_app used to create
# per call, promoted to module level because the SDK verifier must exist
# BEFORE the MCPServer constructor below runs; build_http_app reuses it so
# the handwritten AS legs and the SDK middleware sign and verify against
# one key. Ticket 6 (AS wiring) promotes the authorization-code store and
# its StateStore the same way: the SDK provider must exist before the
# MCPServer constructor too, and its ledgers must be the very ledgers the
# handwritten confirm/activate legs and the SDK AS routes (/authorize
# /token /register) share, or the human consent page would mint codes the
# SDK token exchange cannot consume.
_SDK_TOKEN_AUTHORITY = None
_SDK_AUTH_SETTINGS = None
_SDK_TOKEN_VERIFIER = None
_SDK_TOKEN_STORE = None
_SDK_AUTH_CODE_STORE = None
_SDK_AUTH_PROVIDER = None
_SDK_AUTHORIZE_PAGE = None
# Ticket 7 (feature endpoints): the device-code / activate / GitCode-login
# endpoint handlers registered as custom_starlette_routes on the MCPServer
# (streamable_http_app merges them with lowest matching precedence), plus
# the path set build_http_app forwards to that inner (SDK) app while the
# gate is on. Both stay empty in the default SDK-off wiring, so the
# handwritten dispatcher keeps serving every path itself and the surface
# is byte-identical to before this ticket.
_SDK_FEATURE_ENDPOINTS: tuple[Callable[..., Any], ...] = ()
_SDK_FEATURE_PATHS: frozenset[str] = frozenset()

if _sdk_auth_enabled():
    _sdk_public_url = (os.environ.get("CANNBOT_MCP_PUBLIC_URL") or "").strip().rstrip("/")
    if not _sdk_public_url:
        # AuthSettings needs a concrete issuer/resource identity and the
        # import-time wiring has no request Host to derive one from; a
        # guessed URL would silently mis-bind every token audience. Fail
        # closed to the handwritten chain instead.
        print(
            "cannbot-mcp: CANNBOT_MCP_SDK_AUTH=on requires "
            "CANNBOT_MCP_PUBLIC_URL (the SDK AuthSettings issuer/resource "
            "identity is derived from it); staying on the handwritten auth "
            "chain.",
            file=sys.stderr,
        )
    else:
        from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions

        # Script-launch alias: `python server.py` (the platform-start.sh
        # and docker-entrypoint.sh launch path) executes this file as
        # __main__, so 'server' is not in sys.modules when the imports
        # below run. sdk_auth_provider/sdk_auth_verifier both
        # `import server` at module top; without this alias that import
        # re-executes the whole file a second time as module 'server',
        # whose own SDK-auth block then hits the partially initialized
        # sdk_auth_provider and crashes (AttributeError on
        # CannbotAuthProvider). Aliasing the module under execution to
        # 'server' gives those imports the same partially-initialized
        # module the in-process path (import server first) always saw;
        # they only resolve server attributes at call time, after this
        # module has finished executing. No-op when imported as 'server'.
        sys.modules.setdefault("server", sys.modules[__name__])
        # Import order note: sdk_auth_verifier and sdk_auth_provider both
        # import server, so neither may be imported standalone-first in an
        # SDK-auth-on process.
        import sdk_auth_provider
        import sdk_auth_verifier

        _sdk_resource_url = _sdk_public_url + "/mcp"
        _SDK_TOKEN_AUTHORITY = SelfIssuedTokenAuthority()
        _SDK_AUTH_SETTINGS = AuthSettings(
            issuer_url=_sdk_public_url,
            resource_server_url=_sdk_resource_url,
            validate_token_resource=True,
            # Ticket 6 (AS wiring): dynamic client registration on, so the
            # SDK mounts POST /register against
            # provider.register_client/get_client (the fixed public
            # client semantics of the handwritten /register handler).
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )
        _SDK_TOKEN_STORE = state_store.open_state_store()
        _SDK_AUTH_CODE_STORE = AuthCodeStore(_SDK_TOKEN_STORE)
        _SDK_AUTH_PROVIDER = sdk_auth_provider.CannbotAuthProvider(
            _SDK_AUTH_CODE_STORE,
            _SDK_TOKEN_STORE,
            _SDK_TOKEN_AUTHORITY,
            resource_server_url=_sdk_resource_url,
        )
        _SDK_TOKEN_VERIFIER = sdk_auth_verifier.CannbotTokenVerifier(
            _SDK_TOKEN_AUTHORITY,
            GitCodeTokenVerifier() if _gitcode_verify_enabled() else None,
            resource_server_url=_sdk_resource_url,
        )

class CannbotProviderTokenVerifier(ProviderTokenVerifier):
    """ProviderTokenVerifier carrying the four-track CannbotTokenVerifier.

    SDK constraint: MCPServer takes auth_server_provider XOR
    token_verifier; mounting the provider makes the constructor auto-wrap
    it in the SDK's ProviderTokenVerifier, whose verify_token routes to
    provider.load_access_token — a later ticket's NotImplementedError
    stub. This subclass keeps the ProviderTokenVerifier type the bearer
    middleware consumes but delegates the actual verification to the
    ticket-2 CannbotTokenVerifier, so /mcp admission keeps the ticket-3
    semantics (four-track routing, resource_server_url audience binding)
    while the AS routes ride the provider.
    """

    def __init__(self, provider: Any, verifier: Any) -> None:
        super().__init__(provider)
        self._verifier = verifier

    async def verify_token(self, token: str) -> AccessToken | None:
        return await self._verifier.verify_token(token)

mcp_server = MCPServer(
    "cannbot-knowledge",
    instructions=(
        "Read-only access to the cannbot-knowledge base: call discover to see "
        "what is covered, search to rank candidate cards, read_card to read "
        "one card with its sources and links. Confirm the target platform "
        "before searching; searches without a platform fail closed."
    ),
    version=_repository_version(),
    # None (default) leaves the SDK auth stack unmounted, which is
    # byte-identical to the previous constructor: streamable_http_app then
    # mounts no middleware and no RFC 9728 route.
    auth=_SDK_AUTH_SETTINGS,
    # Ticket 6 (AS wiring): with the provider mounted,
    # streamable_http_app() auto-mounts the SDK AS route set (/authorize
    # /token /register + RFC 8414) behind this same CANNBOT_MCP_SDK_AUTH
    # gate. Passing token_verifier here too would violate the SDK's
    # either/or constraint; the constructor auto-wraps the provider in the
    # SDK's ProviderTokenVerifier, and the assignment right below swaps
    # that auto-created verifier for a ProviderTokenVerifier subclass that
    # keeps the ticket-2 four-track CannbotTokenVerifier logic.
    auth_server_provider=_SDK_AUTH_PROVIDER,
)

if _SDK_AUTH_PROVIDER is not None:
    mcp_server._token_verifier = CannbotProviderTokenVerifier(
        _SDK_AUTH_PROVIDER, _SDK_TOKEN_VERIFIER
    )

    async def _sdk_authorize_page(request: Request) -> HTMLResponse:
        """Human consent page on the SDK /authorize path (ticket 6).

        The SDK's /authorize route speaks programmatic JSON/redirect
        semantics; a browser needs THIS HTML page. It is registered as a
        custom starlette route (GET only) and lifted ahead of the SDK's
        own /authorize route by build_http_app: the SDK appends custom
        routes with the LOWEST matching precedence, so without the lift
        its route would shadow this page — on the conflict the custom
        route wins, and the GET-only registration leaves POST /authorize
        to the SDK route (Starlette keeps scanning past a method-partial
        match). The path is root-absolute, exactly the SDK route's own
        path: this deployment has no PUBLIC_PATH prefix mechanism — the
        SDK stack derives every path from the single
        CANNBOT_MCP_PUBLIC_URL fact source (the RFC's fix for the
        PUBLIC_URL/PUBLIC_PATH dual-variable problem). Rendering reuses
        auth_pages.authorize_page and the page's form posts back to the
        handwritten /oauth/authorize/confirm leg, so the grant mints in
        the same AuthCodeStore the SDK /token exchange consumes. The
        GitCode-login reentry (code + server-side binding token st) keeps
        the handwritten /oauth/authorize contract.
        """
        if not _auth_server_enabled():
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32601, "message": "Method not found"},
                },
                status_code=404,
            )
        query = request.query_params
        redirect_uri = (query.get("redirect_uri") or "").strip()
        response_type = (query.get("response_type") or "").strip()
        code_param = (query.get("code") or "").strip()
        binding_token = (query.get("st") or "").strip()
        signed_in = ""
        if code_param:
            # Returning from the GitCode login leg with the same grant:
            # re-render the consent page instead of minting a new code. The
            # session carries the original redirect_uri, and the verified
            # identity comes from the server-side binding (st).
            session = _SDK_AUTH_CODE_STORE.lookup(code_param)
            if session is None:
                return HTMLResponse(
                    _render_auth_pages().error_page(
                        "授权请求已过期或已使用，请回到客户端重新发起。"
                    )
                )
            redirect_uri = session.redirect_uri
            if binding_token:
                # VerifiedIdentityBinding is defined further down this
                # module, so it is resolved at request time, not at the
                # import-time wiring; the wrapper is stateless over the
                # shared StateStore, so per-request construction is exact.
                bound = VerifiedIdentityBinding(_SDK_TOKEN_STORE).peek(
                    binding_token
                )
                if bound is None or bound[0] != code_param:
                    return HTMLResponse(
                        _render_auth_pages().error_page(
                            "登录会话已过期或无效，请重新通过 GitCode 登录。"
                        )
                    )
                signed_in = bound[1]
        else:
            # PKCE is mandatory for this public-client grant (RFC 7636
            # §4.4.1, MCP spec authorization requirements): every
            # authorization code is bound to a challenge at mint time.
            code_challenge = (query.get("code_challenge") or "").strip()
            challenge_method = (query.get("code_challenge_method") or "").strip()
            if not code_challenge or challenge_method != "S256":
                return HTMLResponse(
                    _render_auth_pages().error_page(
                        "授权请求缺少 code_challenge 或未使用 S256 方法；"
                        "本服务要求公共客户端强制 PKCE。"
                    )
                )
            if response_type != "code" or not redirect_uri:
                return HTMLResponse(
                    _render_auth_pages().error_page(
                        "授权请求缺少 redirect_uri 或 response_type 不是 code。"
                    )
                )
            state = query.get("state") or ""
            # RFC 8707 resource indicator: canonical form matches the
            # handwritten authorize endpoint (trailing slash stripped).
            resource = (query.get("resource") or "").strip().rstrip("/")
            session = _SDK_AUTH_CODE_STORE.create(
                redirect_uri, code_challenge, state, resource
            )
        return HTMLResponse(
            _render_auth_pages().authorize_page(
                session.code,
                signed_in=signed_in,
                gitcode_available=bool(_oauth_client_id()),
                session_token=binding_token if signed_in else "",
                path_prefix=_public_path(),
            )
        )

    mcp_server.custom_route("/authorize", methods=["GET"])(_sdk_authorize_page)
    _SDK_AUTHORIZE_PAGE = _sdk_authorize_page

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


def _query_params(scope: dict[str, Any]) -> dict[str, str]:
    """Decoded query string of an ASGI HTTP scope."""
    raw = scope.get("query_string") or b""
    if isinstance(raw, bytes):
        raw = raw.decode("latin-1")
    return {
        key: value[0]
        for key, value in urllib.parse.parse_qs(raw).items()
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


_DISCOVERY_CORS_HEADERS: list[tuple[bytes, bytes]] = [
    # Same CORS posture the SDK's own 9728/8414 routes carry (their
    # cors_middleware wraps handlers with allow_origins="*"): browser-based
    # MCP clients (MCP Inspector and friends) fetch the discovery
    # documents cross-origin, and without Access-Control-Allow-Origin the
    # browser refuses to hand the JSON to the page even though the server
    # answered 200. Both GET and the OPTIONS preflight go through the same
    # path-matched discovery blocks, so one header set covers both.
    # allow-headers mirrors the SDK posture too: Starlette's CORSMiddleware
    # auto-joins the CORS-safelisted request headers (accept,
    # accept-language, content-language, content-type) to whatever the
    # wrapper names, and some fetch wrappers send content-type on GET —
    # without it in the allowlist a passing preflight still gets the
    # actual cross-origin request blocked.
    (b"access-control-allow-origin", b"*"),
    (
        b"access-control-allow-headers",
        b"MCP-Protocol-Version, accept, accept-language, "
        b"content-language, content-type",
    ),
    (b"access-control-allow-methods", b"GET, OPTIONS"),
]

async def _send_404(send: Callable[..., Any]) -> None:
    """Uniform 404 for endpoints disabled by configuration."""
    await _send_json_response(
        send,
        404,
        {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32601, "message": "Method not found"},
        },
    )

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

def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

def _activation_page(prefill: str) -> str:
    """Manual code-entry page (fallback when no GitCode app is configured).

    Redesigned (frontend-design): the CANN-marked card carries the code
    entry; with GitCode configured the terminal link normally bypasses
    this page via /activate?code=… → GitCode login.
    """
    return _render_auth_pages().activation_page(
        prefill,
        gitcode_available=bool(_oauth_client_id()),
        path_prefix=_public_path(),
    )


def _activation_confirm_page(
    user_code: str, signed_in: str = "", session_token: str = ""
) -> str:
    """Confirmation page: GitCode-bound identity or manual username."""
    return _render_auth_pages().confirm_page(
        user_code,
        signed_in,
        gitcode_available=bool(_oauth_client_id()),
        session_token=session_token,
        path_prefix=_public_path(),
    )


def _activation_error_page(message: str) -> str:
    return _render_auth_pages().error_page(message)


_AUTH_PAGES_MODULE: Any = None


def _render_auth_pages() -> Any:
    """Load the auth page renderer (auth_pages.py, same directory)."""
    global _AUTH_PAGES_MODULE
    if _AUTH_PAGES_MODULE is None:
        import importlib.util

        path = Path(__file__).with_name("auth_pages.py")
        spec = importlib.util.spec_from_file_location("auth_pages", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _AUTH_PAGES_MODULE = module
    return _AUTH_PAGES_MODULE

async def _send_html_response(
    send: Callable[..., Any], status: int, html: str
) -> None:
    body = html.encode("utf-8")
    headers = [
        (b"content-type", b"text/html; charset=utf-8"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]
    await send(
        {"type": "http.response.start", "status": status, "headers": headers}
    )
    await send({"type": "http.response.body", "body": body})

def _device_code_ip_gate(
    limit: int = 30, window_s: float = 60.0
) -> "SlidingWindowRateLimiter":
    """Coarse per-IP throttle for the open device endpoints.

    Deliberately stays process-local: it exists to shield a single open
    endpoint from hammering, and making it global would let one shared
    StateStore quorum throttle all replicas' health probing. Shares the
    SlidingWindowRateLimiter TYPE (call sites only use .check), but keeps
    its own in-memory window.
    """

    class _FixedWindow(SlidingWindowRateLimiter):
        def __init__(self) -> None:
            self._hits: dict[str, deque[float]] = {}
            self._lock = threading.Lock()

        def check(self, key: str) -> RateDecision:  # type: ignore[override]
            now = time.monotonic()
            with self._lock:
                hits = self._hits.setdefault(key, deque())
                while hits and hits[0] <= now - window_s:
                    hits.popleft()
                if len(hits) >= limit:
                    return RateDecision(
                        False, max(1, int(window_s - (now - hits[0])) + 1)
                    )
                hits.append(now)
                return RateDecision(True)

    return _FixedWindow()  # type: ignore[return-value]

_DEVICE_ENDPOINT_GATE: "SlidingWindowRateLimiter | None" = None
_DEVICE_POLL_GATE: "SlidingWindowRateLimiter | None" = None

def device_endpoint_gate() -> "SlidingWindowRateLimiter":
    global _DEVICE_ENDPOINT_GATE
    if _DEVICE_ENDPOINT_GATE is None:
        _DEVICE_ENDPOINT_GATE = _device_code_ip_gate()
    return _DEVICE_ENDPOINT_GATE

def device_poll_gate() -> "SlidingWindowRateLimiter":
    global _DEVICE_POLL_GATE
    if _DEVICE_POLL_GATE is None:
        _DEVICE_POLL_GATE = _device_code_ip_gate()
    return _DEVICE_POLL_GATE

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

@dataclass
class _AuthLegDeps:
    """Dependencies the device-code / activate / GitCode-login legs run on.

    One value serves both registrations of the same handler bodies
    (ticket 7): the handwritten dispatcher inside build_http_app (the
    SDK-off default, behaviour identical to before) and the
    custom_starlette_routes the SDK-on wiring mounts on the MCPServer.
    The stores, broker, binding and authority are the shared ledgers of
    whichever wiring built them, so a grant minted through one
    registration is consumable through the other. ``device_audience``
    selects the resource identity the device-flow pair mints for (None
    keeps the handwritten ``_public_url(scope)`` derivation; the SDK-on
    legs pass the SDK resource identity the /mcp bearer comparison
    requires), and ``sdk_as_active`` carries the ticket-6 routing
    decisions embedded in the shared bodies (the auth-code/refresh
    grants yield to the SDK /token endpoint; the GitCode callback
    reenters the custom /authorize consent page).
    """

    device_store: DeviceCodeStore
    auth_code_store: AuthCodeStore
    gitcode_login: GitCodeLoginBroker
    identity_binding: VerifiedIdentityBinding
    token_authority: SelfIssuedTokenAuthority
    token_store: state_store.StateStore
    device_audience: str | None = None
    sdk_as_active: bool = False


async def _asgi_leg_response(
    request: Request, leg: Callable[..., Any]
) -> Response:
    """Serve one handwritten ASGI auth leg behind a Starlette custom route.

    Ticket 7 reuses the existing handler bodies verbatim (logic
    unchanged, registration method changed), so the custom route bridges
    Starlette back down to raw ASGI: the drained request body is replayed
    to the leg in one message (the _replay_body shape), the leg's
    http.response messages are captured, and they are rebuilt into the
    Response Starlette sends. The leg keeps reading the same ASGI scope,
    so every URL derivation inside it (_public_url over PUBLIC_URL/Host,
    root-relative redirect Locations) answers exactly as on the
    handwritten registration — no PUBLIC_PATH prefix mechanism exists and
    none is introduced.
    """
    body = await request.body()
    replayed = {"delivered": False}

    async def receive() -> dict[str, Any]:
        if not replayed["delivered"]:
            replayed["delivered"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    start: dict[str, Any] = {}
    chunks: list[bytes] = []

    async def send(message: dict[str, Any]) -> None:
        if message.get("type") == "http.response.start":
            start.update(message)
        elif message.get("type") == "http.response.body":
            chunks.append(message.get("body", b""))

    await leg(request.scope, receive, send)
    headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    return Response(
        content=b"".join(chunks),
        status_code=start.get("status", 200),
        headers=headers,
    )


async def _handle_device_code(
    scope: dict[str, Any],
    receive: Callable[..., Any],
    send: Callable[..., Any],
    legs: _AuthLegDeps,
) -> None:
    """RFC 8628 §3.1 device authorization endpoint (ticket 7: extracted
    verbatim from the build_http_app dispatcher so the custom-route
    registration reuses it).

    Bare path like /health: no auth, no rate limiting by principal, no
    call log — but a coarse per-IP throttle so the open endpoint cannot
    be hammered (30 requests/IP/minute, reusing the cooldown gate).
    """
    if not _auth_server_enabled():
        await _drain_body(receive)
        await _send_404(send)
        return
    client_ip = (scope.get("client") or ("unknown", 0))[0]
    if not device_endpoint_gate().check(client_ip).allowed:
        await _drain_body(receive)
        await _send_json_response(
            send,
            429,
            {"error": "slow_down_permanent", "retry_after_s": 60},
            [(b"retry-after", b"60")],
        )
        return
    await _drain_body(receive)
    device_code, user_code = legs.device_store.create()
    await _send_json_response(
        send,
        200,
        {
            "device_code": device_code,
            "user_code": user_code,
            "verification_uri": f"{_public_url(scope)}/activate",
            "verification_uri_complete": (
                f"{_public_url(scope)}/activate?code={user_code}"
            ),
            "expires_in": legs.device_store.ttl_s,
            "interval": _env_int(DEVICE_INTERVAL_ENV, 5),
        },
    )


async def _handle_device_token(
    scope: dict[str, Any],
    receive: Callable[..., Any],
    send: Callable[..., Any],
    legs: _AuthLegDeps,
) -> None:
    """RFC 8628 §3.4/3.5 token polling (ticket 7: extracted verbatim from
    the build_http_app dispatcher). Same bare-path treatment as the
    device authorization endpoint.
    """
    if not _auth_server_enabled():
        await _drain_body(receive)
        await _send_404(send)
        return
    body = await _drain_body(receive)
    fields: dict[str, str] = {}
    for pair in body.decode("utf-8", "replace").split("&"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            fields[unquote_plus(key)] = unquote_plus(value)
    grant_type = fields.get("grant_type", "")
    if grant_type == "authorization_code":
        if legs.sdk_as_active:
            # SDK AS mode (ticket 6): the SDK /token route inside
            # `inner` owns the authorization-code exchange, so this
            # handwritten grant yields here. Ticket 8 re-scoped the
            # RFC's phase-3 deletion: the body below stays as the
            # SDK_AUTH=off (fallback) implementation, so reverting
            # the env keeps the full legacy grant set. The
            # device-code grant further down stays on this endpoint
            # in BOTH modes (the SDK mounts no device flow; RFC §2.4
            # keeps that leg self-managed).
            await _send_json_response(
                send,
                400,
                {
                    "error": "unsupported_grant_type",
                    "hint": "SDK 模式下授权码换发走 /token 端点。",
                },
            )
            return
        # Self-hosted authorization-code exchange (RFC 6749 §4.1.3).
        # The client proves itself with PKCE (public client, no
        # secret); the redirect must loopback-match the stored one.
        code = fields.get("code", "").strip()
        redirect_uri = fields.get("redirect_uri", "").strip()
        code_verifier = fields.get("code_verifier", "").strip()
        session = legs.auth_code_store.consume(
            code, redirect_uri, code_verifier
        )
        if session is None:
            await _send_json_response(
                send, 400, {"error": "invalid_grant"}
            )
            return
        assert session.username is not None
        # RFC 8707: the aud of the minted pair is the resource the
        # client named at authorize time (or this server's URL).
        token_audience = session.resource or _public_url(scope)
        access, expires_in = legs.token_authority.sign(
            session.username, "access", token_audience
        )
        refresh, _ = legs.token_authority.sign(
            session.username, "refresh", token_audience
        )
        # One-time-use ledger (13b): register the fresh refresh id.
        refresh_jti = SelfIssuedTokenAuthority.token_jti(refresh)
        assert refresh_jti is not None
        legs.token_store.put(
            f"jti:{refresh_jti}", "live",
            legs.token_authority.refresh_remaining_s(refresh),
        )
        await _send_json_response(
            send,
            200,
            {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "Bearer",
                "expires_in": expires_in,
                "scope": "mcp",
            },
        )
        return
    if grant_type == "refresh_token":
        if legs.sdk_as_active:
            # SDK AS mode (ticket 6): the SDK /token route owns the
            # refresh grant, so this handwritten grant yields here.
            # Ticket 8 keeps the body below as the SDK_AUTH=off
            # (fallback) implementation — same re-scope as the
            # authorization-code grant above.
            await _send_json_response(
                send,
                400,
                {
                    "error": "unsupported_grant_type",
                    "hint": "SDK 模式下刷新换发走 /token 端点。",
                },
            )
            return
        refresh_token = fields.get("refresh_token", "")
        # RFC 8707: the refresh grant may carry a resource
        # indicator; when present it must match the token's aud.
        # Absent defaults to this server (legacy clients).
        # Trailing-slash canonicalization matches the authorize
        # endpoint's (clients derive the resource from their URL).
        requested_resource = (
            (fields.get("resource") or "").strip().rstrip("/")
        )
        verified = legs.token_authority.verify(
            refresh_token,
            "refresh",
            requested_resource
            or SelfIssuedTokenAuthority._default_audience(scope),
        )
        if verified is None:
            await _send_json_response(
                send, 400, {"error": "invalid_grant"}
            )
            return
        username, _typ = verified
        # One-time-use ledger (13b): a refresh token is consumed by
        # the refresh itself. The take() is atomic — replaying an
        # old (possibly leaked) refresh finds the id gone and gets
        # invalid_grant instead of a second token pair.
        old_jti = SelfIssuedTokenAuthority.token_jti(refresh_token)
        if old_jti is None or legs.token_store.take(f"jti:{old_jti}") is None:
            await _send_json_response(
                send, 400, {"error": "invalid_grant"}
            )
            return
        # Keep the refresh pair on the SAME audience the old token
        # carried. With no explicit resource, that is this
        # server's URL; with one, verify() already enforced it.
        token_aud = requested_resource or _public_url(scope)
        access, expires_in = legs.token_authority.sign(
            username, "access", token_aud
        )
        # Book the new refresh's id for its whole lifetime: the
        # next refresh that presents it must find it here.
        new_refresh, _ = legs.token_authority.sign(
            username, "refresh", token_aud
        )
        new_jti = SelfIssuedTokenAuthority.token_jti(new_refresh)
        assert new_jti is not None
        legs.token_store.put(
            f"jti:{new_jti}", "live",
            legs.token_authority.refresh_remaining_s(new_refresh),
        )
        await _send_json_response(
            send,
            200,
            {
                "access_token": access,
                "refresh_token": new_refresh,
                "token_type": "Bearer",
                "expires_in": expires_in,
            },
        )
        return
    if grant_type != "urn:ietf:params:oauth:grant-type:device_code":
        await _send_json_response(
            send, 400, {"error": "unsupported_grant_type"}
        )
        return
    device_code = fields.get("device_code", "")
    session = legs.device_store.poll(device_code)
    if session is None:
        # Unknown or expired: RFC 8628 expired_token.
        await _send_json_response(
            send, 400, {"error": "expired_token"}
        )
        return
    if session.state == "pending":
        # Poll faster than the advertised interval gets slow_down.
        gate = device_poll_gate()
        client_ip = (scope.get("client") or ("unknown", 0))[0]
        if not gate.check(client_ip).allowed:
            await _send_json_response(
                send,
                429,
                {"error": "slow_down"},
                [(b"retry-after", b"5")],
            )
            return
        await _send_json_response(
            send, 400, {"error": "authorization_pending"}
        )
        return
    if session.state == "denied":
        await _send_json_response(
            send, 400, {"error": "access_denied"}
        )
        return
    # allowed: mint the token pair for the bound username, then
    # consume the session so tokens are handed out exactly once —
    # a repeat poll sees unknown/expired (RFC 8628 one-shot).
    allowed = legs.device_store.consume(device_code)
    if allowed is None:
        await _send_json_response(
            send, 400, {"error": "expired_token"}
        )
        return
    assert allowed.username is not None
    # RFC 8707: device-flow tokens are audience-bound to this
    # server (device flow has no redirect, so this server IS the
    # resource the client wants). The SDK-on legs pin
    # device_audience to the SDK resource identity (the full
    # endpoint URL the /mcp bearer comparison accepts); the
    # handwritten wiring leaves it None and keeps the
    # _public_url derivation.
    token_aud = legs.device_audience or _public_url(scope)
    access, expires_in = legs.token_authority.sign(
        allowed.username, "access", token_aud
    )
    refresh, _ = legs.token_authority.sign(
        allowed.username, "refresh", token_aud
    )
    # One-time-use ledger (13b): register the fresh refresh id so
    # the first refresh grant that presents it can consume it.
    refresh_jti = SelfIssuedTokenAuthority.token_jti(refresh)
    assert refresh_jti is not None
    legs.token_store.put(
        f"jti:{refresh_jti}", "live",
        legs.token_authority.refresh_remaining_s(refresh),
    )
    await _send_json_response(
        send,
        200,
        {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": "mcp",
        },
    )


async def _handle_gitcode_login(
    scope: dict[str, Any],
    receive: Callable[..., Any],
    send: Callable[..., Any],
    legs: _AuthLegDeps,
) -> None:
    """GitCode identity source for the activation page (ticket 7:
    extracted verbatim from the build_http_app dispatcher).

    The redirect_uri below is OUR fixed address, registered on the
    GitCode application — the loopback-ephemeral-port problem of
    the MCP client flow does not exist on this leg.
    The state carries either a device user_code ("ABCD-EFGH") or
    an authcode grant marker ("authcode:<code>"); the callback
    routes back accordingly.
    """
    if not _auth_server_enabled():
        await _drain_body(receive)
        await _send_404(send)
        return
    query = _query_params(scope)
    raw_state = (query.get("state") or "").strip()
    authcode_mode = raw_state.startswith("authcode:")
    # device user_codes are uppercased (XXXX-XXXX form); authcode
    # session codes are token_urlsafe and MUST stay case-exact.
    user_code = (
        raw_state.removeprefix("authcode:").strip().upper()
        if not authcode_mode
        else raw_state.removeprefix("authcode:").strip()
    )
    client_id = _oauth_client_id()
    session = (
        legs.device_store.lookup(user_code)
        if (user_code and not authcode_mode)
        else None
    )
    authcode_session = (
        legs.auth_code_store.lookup(user_code) if authcode_mode else None
    )
    if not client_id:
        await _drain_body(receive)
        await _send_html_response(
            send,
            200,
            _activation_error_page(
                "服务器未配置 GitCode 登录（CANNBOT_MCP_OAUTH_CLIENT_ID）；"
                "请回到上一页使用用户名方式确认。"
            ),
        )
        return
    if not authcode_mode and session is None:
        await _drain_body(receive)
        await _send_html_response(
            send,
            200,
            _activation_error_page("未知或已过期的设备码，请回到终端重新发起。"),
        )
        return
    if authcode_mode and authcode_session is None:
        await _drain_body(receive)
        await _send_html_response(
            send,
            200,
            _render_auth_pages().error_page(
                "授权请求已过期或已使用，请回到客户端重新发起。"
            ),
        )
        return
    _verifier, challenge = legs.gitcode_login.begin(raw_state) or ("", "")
    authorize_url = (
        GITCODE_AUTHORIZE_URL
        + "?"
        + urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": f"{_public_url(scope)}/oauth/gitcode/callback",
                "state": raw_state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
    )
    await _drain_body(receive)
    await send(
        {
            "type": "http.response.start",
            "status": 302,
            "headers": [(b"location", authorize_url.encode())],
        }
    )
    await send({"type": "http.response.body", "body": b""})


async def _handle_gitcode_callback(
    scope: dict[str, Any],
    receive: Callable[..., Any],
    send: Callable[..., Any],
    legs: _AuthLegDeps,
) -> None:
    """Consume the code, exchange for the GitCode username (ticket 7:
    extracted verbatim from the build_http_app dispatcher), then bounce
    back to the activation confirmation (device flow) or the authorize
    consent page (authorization-code flow) with it.
    """
    if not _auth_server_enabled():
        await _drain_body(receive)
        await _send_404(send)
        return
    query = _query_params(scope)
    code = (query.get("code") or "").strip()
    raw_state = (query.get("state") or "").strip()
    authcode_mode = raw_state.startswith("authcode:")
    # device user_codes are uppercased (XXXX-XXXX form); authcode
    # session codes are token_urlsafe and MUST stay case-exact.
    user_code = (
        raw_state.removeprefix("authcode:").strip().upper()
        if not authcode_mode
        else raw_state.removeprefix("authcode:").strip()
    )
    error = (query.get("error") or "").strip()
    if error:
        await _drain_body(receive)
        await _send_html_response(
            send, 200, _activation_error_page(f"GitCode 返回错误：{error}")
        )
        return
    pkce_verifier = (
        legs.gitcode_login.take_verifier(raw_state) if raw_state else None
    )
    if not code or not raw_state or pkce_verifier is None:
        await _drain_body(receive)
        await _send_html_response(
            send,
            200,
            _activation_error_page("登录会话已过期或无效，请回到终端重新发起。"),
        )
        return
    username = await _gitcode_exchange_login(
        code, pkce_verifier, f"{_public_url(scope)}/oauth/gitcode/callback"
    )
    if username is None:
        await _drain_body(receive)
        await _send_html_response(
            send,
            200,
            _render_auth_pages().error_page(
                "GitCode 登录失败（服务不可达或已拒绝）。",
                retry_url=_public_path()
                        + "/oauth/gitcode/login?state="
                + _html_escape(raw_state),
            ),
        )
        return
    # The verified identity lands in a SERVER-SIDE binding keyed by
    # an unguessable token; the username itself never appears in
    # the redirect URL (or any later form field).
    binding_token = legs.identity_binding.create(user_code, username)
    if authcode_mode:
        # SDK AS mode reenters the custom /authorize consent page
        # (the handwritten /oauth/authorize handler is skipped
        # there); the legacy path stays for the SDK-off wiring.
        back_to = (
            _public_path()
            + ("/authorize" if legs.sdk_as_active else "/oauth/authorize")
            + "?code="
            + urllib.parse.quote(user_code)
            + "&st="
            + urllib.parse.quote(binding_token)
        )
    else:
        back_to = (
            _public_path()
            + "/activate?code="
            + urllib.parse.quote(user_code)
            + "&st="
            + urllib.parse.quote(binding_token)
        )
    await _drain_body(receive)
    await send(
        {
            "type": "http.response.start",
            "status": 302,
            "headers": [(b"location", back_to.encode())],
        }
    )
    await send({"type": "http.response.body", "body": b""})


async def _handle_activate(
    scope: dict[str, Any],
    receive: Callable[..., Any],
    send: Callable[..., Any],
    legs: _AuthLegDeps,
) -> None:
    """RFC 8628 §3.3 user interaction (ticket 7: extracted verbatim from
    the build_http_app dispatcher). UX contract:

    with a GitCode application configured, opening /activate goes
    STRAIGHT to the GitCode login (the user never types a device
    code — the terminal link /activate?code=… carries it in the
    query, the one-click direct connect). After the login the flow
    returns with a server-side identity binding token (st), and one
    click on 允许 finishes it. The manual code-entry form only
    appears when no client_id is configured — with GitCode
    configured the username is ALWAYS the server-stored verified
    identity, never a form field.
    """
    if not _auth_server_enabled():
        await _drain_body(receive)
        await _send_404(send)
        return
    query = _query_params(scope)
    binding_token = (query.get("st") or "").strip()
    code_param = (query.get("code") or "").strip().upper()
    if scope.get("method") == "GET" and code_param and _oauth_client_id():
        if not binding_token:
            # Straight to GitCode: /activate?code=XXXX-XXXX becomes a
            # one-link experience (the terminal prints exactly this).
            login_url = (
                "/oauth/gitcode/login?state="
                + urllib.parse.quote(code_param)
            )
            await _drain_body(receive)
            await send(
                {
                    "type": "http.response.start",
                    "status": 302,
                    "headers": [(b"location", login_url.encode())],
                }
            )
            await send({"type": "http.response.body", "body": b""})
            return
        # Returning from the GitCode login: the binding holds the
        # verified identity for THIS grant.
        bound = legs.identity_binding.peek(binding_token)
        if bound is None or bound[0] != code_param:
            await _drain_body(receive)
            await _send_html_response(
                send,
                200,
                _activation_error_page(
                    "登录会话已过期或无效，请回到终端重新发起。"
                ),
            )
            return
        await _drain_body(receive)
        await _send_html_response(
            send,
            200,
            _activation_confirm_page(
                code_param,
                signed_in=bound[1],
                session_token=binding_token,
            ),
        )
        return
    body = await _drain_body(receive)
    fields: dict[str, str] = {}
    for pair in body.decode("utf-8", "replace").split("&"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            fields[unquote_plus(key)] = unquote_plus(value)
    if scope.get("method") != "POST":
        await _send_html_response(
            send,
            200,
            _activation_page((query.get("code") or "").strip()),
        )
        return
    user_code = fields.get("user_code", "").strip().upper()
    session = legs.device_store.lookup(user_code)
    if session is None:
        await _send_html_response(
            send, 200, _activation_error_page("未知或已过期的设备码，请回到终端重新发起。")
        )
        return
    action = fields.get("action", "")
    if action == "allow":
        if _oauth_client_id():
            # GitCode configured: the username comes ONLY from the
            # server-side verified binding (one-shot); any username
            # value in the form is ignored.
            form_binding = (fields.get("st") or "").strip()
            bound = (
                legs.identity_binding.take(form_binding)
                if form_binding
                else None
            )
            if bound is None or bound[0] != user_code:
                await _send_html_response(
                    send,
                    200,
                    _activation_error_page(
                        "缺少有效的登录会话，请通过 GitCode 登录后再确认。"
                    ),
                )
                return
            username = bound[1]
        else:
            # No GitCode application configured: manual username
            # bootstrap (trusted-network deployments only).
            username = fields.get("username", "").strip()
            if not username:
                await _send_html_response(
                    send, 200, _activation_error_page("请填写用户名。")
                )
                return
        allowed = legs.device_store.allow(user_code, username)
        if allowed is None:
            await _send_html_response(
                send, 200, _activation_error_page("设备码已失效（可能刚被使用或过期）。")
            )
            return
        await _send_html_response(
            send,
            200,
            _render_auth_pages().success_page(username),
        )
        return
    if action == "deny":
        legs.device_store.deny(user_code)
        await _send_html_response(
            send,
            200,
            _render_auth_pages().denied_page(),
        )
        return
    await _send_html_response(
        send,
        200,
        _activation_confirm_page(user_code),
    )


if _SDK_AUTH_PROVIDER is not None:
    # Ticket 7 (feature endpoints): the SDK auth stack has no device-code
    # flow, no RFC 8628 user-interaction page and no GitCode login leg,
    # so those endpoints are mounted back onto the SDK stack as custom
    # routes (MCPServer.custom_route appends to custom_starlette_routes;
    # streamable_http_app merges them, and no SDK route claims these
    # paths). The handler bodies are the very ones the handwritten
    # build_http_app dispatcher runs — extracted to module level above
    # and shared through _AuthLegDeps — so the logic is unchanged and
    # only the registration method differs. Page URLs keep the
    # handwritten derivation on both registrations (_public_url over
    # CANNBOT_MCP_PUBLIC_URL / Host, root-relative redirect Locations);
    # this deployment has no PUBLIC_PATH prefix mechanism, and none is
    # introduced here. This block sits AFTER the extracted handler
    # definitions (a fresh SDK_AUTH=on import evaluates
    # _sdk_leg_endpoint(_handle_...) at import time — a reload-only
    # placement above them would NameError on the production path, the
    # same masking ticket 6 fixed for _env_int).

    def _sdk_feature_legs() -> "_AuthLegDeps":
        """Legs for the custom-route feature endpoints, per request.

        Constructed lazily like the VerifiedIdentityBinding in
        _sdk_authorize_page: every component is a stateless wrapper over
        the module-level shared ledgers (DeviceCodeStore reads only its
        env-derived TTL), so a per-request build is exact. Reusing
        _SDK_TOKEN_STORE/_SDK_AUTH_CODE_STORE/_SDK_TOKEN_AUTHORITY keeps
        one ledger set across the custom-route legs, the SDK AS routes
        and the handwritten confirm leg.
        """
        return _AuthLegDeps(
            device_store=DeviceCodeStore(_SDK_TOKEN_STORE),
            auth_code_store=_SDK_AUTH_CODE_STORE,
            gitcode_login=GitCodeLoginBroker(_SDK_TOKEN_STORE),
            identity_binding=VerifiedIdentityBinding(_SDK_TOKEN_STORE),
            token_authority=_SDK_TOKEN_AUTHORITY,
            token_store=_SDK_TOKEN_STORE,
            # RFC 8707 on the SDK stack: the resource identity is
            # resource_server_url (the full endpoint URL), so the device
            # pair mints audience-bound to exactly what the ticket-3
            # bearer comparison on /mcp accepts. None would keep the
            # handwritten _public_url(scope) derivation, which that
            # strict resource check rejects.
            device_audience=_sdk_resource_url,
            sdk_as_active=True,
        )

    def _sdk_leg_endpoint(leg: Callable[..., Any]) -> Callable[[Request], Any]:
        """Wrap one extracted handwritten leg as a custom-route endpoint.

        The leg body runs unchanged behind the ASGI bridge over the
        shared SDK ledgers; only the registration method (custom route
        merged into the SDK app) differs from the handwritten dispatch.
        """

        async def endpoint(request: Request) -> Response:
            return await _asgi_leg_response(
                request,
                lambda scope, receive, send: leg(
                    scope, receive, send, _sdk_feature_legs()
                ),
            )

        return endpoint

    _sdk_device_code_endpoint = _sdk_leg_endpoint(_handle_device_code)
    _sdk_device_token_endpoint = _sdk_leg_endpoint(_handle_device_token)
    _sdk_activate_endpoint = _sdk_leg_endpoint(_handle_activate)
    _sdk_gitcode_login_endpoint = _sdk_leg_endpoint(_handle_gitcode_login)
    _sdk_gitcode_callback_endpoint = _sdk_leg_endpoint(_handle_gitcode_callback)
    # GET+POST covers every method the handwritten no-method-check
    # surface ever answered in practice; beyond that the router answers
    # 405 — a registration-level difference the handwritten legs never
    # produced, and the behavioural proof (in the wiring test) that a
    # request took the custom-route path.
    mcp_server.custom_route("/oauth/device/code", methods=["GET", "POST"])(
        _sdk_device_code_endpoint
    )
    mcp_server.custom_route("/oauth/device/token", methods=["GET", "POST"])(
        _sdk_device_token_endpoint
    )
    mcp_server.custom_route("/activate", methods=["GET", "POST"])(
        _sdk_activate_endpoint
    )
    mcp_server.custom_route("/oauth/gitcode/login", methods=["GET", "POST"])(
        _sdk_gitcode_login_endpoint
    )
    mcp_server.custom_route("/oauth/gitcode/callback", methods=["GET", "POST"])(
        _sdk_gitcode_callback_endpoint
    )
    _SDK_FEATURE_ENDPOINTS = (
        _sdk_device_code_endpoint,
        _sdk_device_token_endpoint,
        _sdk_activate_endpoint,
        _sdk_gitcode_login_endpoint,
        _sdk_gitcode_callback_endpoint,
    )
    _SDK_FEATURE_PATHS = frozenset(
        (
            "/oauth/device/code",
            "/oauth/device/token",
            "/activate",
            "/oauth/gitcode/login",
            "/oauth/gitcode/callback",
        )
    )


def build_http_app(
    knowledge_server: MCPServer,
    tokens: TokenList,
    limiter: RateLimiter,
    cooldown: IpCooldown,
    rate_limit: int,
    host: str,
    verifier: GitCodeTokenVerifier | None = None,
) -> Callable[..., Any]:
    inner = knowledge_server.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=True, host=host
    )

    # SDK auth stack: a
    # knowledge_server constructed with AuthSettings + a TokenVerifier (the
    # CANNBOT_MCP_SDK_AUTH=on wiring at module level) has already mounted
    # the SDK bearer middleware and the RFC 9728 route inside
    # streamable_http_app() above. Detect it off the server itself so stub
    # servers in tests keep the handwritten chain, and mirror the SDK's
    # 9728 declaration for the bare well-known path the SDK does not
    # route (its metadata URL is resource_server_url-derived, i.e.
    # /mcp-suffixed).
    _server_auth = getattr(
        getattr(knowledge_server, "settings", None), "auth", None
    )
    sdk_rs_active = _server_auth is not None and getattr(
        knowledge_server, "_token_verifier", None
    ) is not None
    # SDK AS wiring (ticket 6): the same gate, one level up — a server
    # constructed with auth_server_provider has the SDK AS route set
    # (/authorize /token /register + RFC 8414) mounted inside `inner`,
    # served by the module-level CannbotAuthProvider.
    sdk_as_active = getattr(knowledge_server, "_auth_server_provider", None) is not None
    # Ticket 7 (feature endpoints): the device-code/activate/GitCode-login
    # legs are custom routes on the SDK stack when the wiring mounted them.
    # Detected off the server's own custom_starlette_routes (the
    # registration the SDK-on wiring made), so stub servers in tests keep
    # the handwritten dispatcher serving those paths.
    sdk_feature_endpoints = any(
        getattr(route, "endpoint", None) in _SDK_FEATURE_ENDPOINTS
        for route in (
            getattr(knowledge_server, "_custom_starlette_routes", None) or []
        )
    )
    if sdk_as_active and _SDK_AUTHORIZE_PAGE is not None:
        # The custom /authorize consent page rides custom_starlette_routes,
        # which the SDK appends with the LOWEST matching precedence — its
        # own /authorize route would shadow the page. Resolve the conflict
        # in the custom route's favour: lift it to the front of THIS app's
        # route list (a per-app copy, so the shared registration is
        # untouched). The GET-only registration keeps the SDK's /authorize
        # serving programmatic POST calls — Starlette keeps scanning past a
        # method-partial match.
        routes = inner.routes
        ours = [
            route
            for route in routes
            if getattr(route, "endpoint", None) is _SDK_AUTHORIZE_PAGE
        ]
        for route in ours:
            routes.remove(route)
            routes.insert(0, route)
    _sdk_pr_metadata: dict[str, Any] | None = None
    if sdk_rs_active:
        from mcp.server.auth.routes import ProtectedResourceMetadata

        _sdk_pr_metadata = ProtectedResourceMetadata(
            resource=_server_auth.resource_server_url,
            authorization_servers=[_server_auth.issuer_url],
            scopes_supported=_server_auth.required_scopes,
        ).model_dump(mode="json", exclude_none=True)

    token_authority = _SDK_TOKEN_AUTHORITY or SelfIssuedTokenAuthority()
    # Shared state backend (sqlite default / Redis opt-in). Device-code
    # sessions, PKCE pairings and the refresh one-time-use ledger live
    # here so multi-node deployments share them. In SDK AS mode the
    # module-level singleton (the provider's ledgers) is reused so the
    # handwritten confirm/activate legs and the SDK AS routes share one
    # AuthCodeStore/jti ledger.
    token_store = _SDK_TOKEN_STORE or state_store.open_state_store()
    device_store = DeviceCodeStore(token_store)
    gitcode_login = GitCodeLoginBroker(token_store)
    identity_binding = VerifiedIdentityBinding(token_store)
    # AuthCodeStore and ApiKeyStore still own sqlite tables (a StateStore
    # migration is planned); resolve their directory from the auth-db env
    # or the default state directory like DeviceCodeStore used to.
    _auth_state_dir = (
        Path((os.environ.get(AUTH_DB_ENV) or "").strip()).parent
        if (os.environ.get(AUTH_DB_ENV) or "").strip()
        else DEFAULT_LOG_DIR
    )
    auth_code_store = _SDK_AUTH_CODE_STORE or AuthCodeStore(token_store)
    # Self-service machine tokens. Same state directory and same
    # discipline as the other auth stores (never inside the repo).
    api_key_store = api_keys.ApiKeyStore(_auth_state_dir / "apikeys.db")
    # Ticket 7: the shared handler bodies (extracted to module level) run
    # with THESE legs on the handwritten dispatch — the same stores and
    # authority the branches closed over before the extraction.
    # device_audience None keeps the handwritten device-flow audience
    # derivation (_public_url(scope)); the SDK-on custom-route legs pass
    # the SDK resource identity instead (see _sdk_feature_legs).
    auth_legs = _AuthLegDeps(
        device_store=device_store,
        auth_code_store=auth_code_store,
        gitcode_login=gitcode_login,
        identity_binding=identity_binding,
        token_authority=token_authority,
        token_store=token_store,
        device_audience=None,
        sdk_as_active=sdk_as_active,
    )

    async def app(scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope["type"] == "http" and scope.get("path") == "/health":
            # Unauthenticated liveness probe for K8s/APISIX-style orchestrators:
            # answers before auth and rate limiting, never reaches the MCP app,
            # and is not written to the call log.
            await _drain_body(receive)
            await _send_json_response(send, 200, {"status": "ok"})
            return
        if scope["type"] == "http" and scope.get("path") == "/api/keys":
            # Self-service machine tokens. Authenticated by a self-issued
            # access JWT only (never a refresh token, never an API key —
            # keys are consume-only credentials for /mcp). The JWT subject
            # becomes the key owner; the plaintext key is returned exactly
            # once at creation and never stored.
            if not _auth_server_enabled():
                await _drain_body(receive)
                await _send_404(send)
                return
            headers = _http_headers(scope)
            authorization = headers.get("authorization", "")
            bearer = (
                authorization[7:].strip()
                if authorization.lower().startswith("bearer ")
                else None
            )
            identity = (
                token_authority.verify(
                    bearer, "access", SelfIssuedTokenAuthority._default_audience(scope)
                )
                if bearer
                else None
            )
            if identity is None:
                await _drain_body(receive)
                _LOGGER.log_event(
                    event="auth_failed",
                    src_ip=(scope.get("client") or ("unknown", 0))[0],
                    reason="api_keys_no_jwt",
                    boot_id=BOOT_ID,
                )
                await _send_json_response(
                    send,
                    401,
                    {"error": "unauthorized", "hint": "登录后携带 access token 调用。"},
                )
                return
            owner = identity[0]
            method = scope.get("method", "")
            if method == "POST":
                body = await _drain_body(receive)
                fields: dict[str, str] = {}
                for pair in body.decode("utf-8", "replace").split("&"):
                    if "=" in pair:
                        key, _, value = pair.partition("=")
                        fields[unquote_plus(key)] = unquote_plus(value)
                label = fields.get("label", "").strip()
                created = api_key_store.create(owner, label)
                if created is None:
                    await _send_json_response(
                        send,
                        400,
                        {
                            "error": "invalid_request",
                            "hint": "label 必填（≤32 字符），每用户最多 10 把有效 key。",
                        },
                    )
                    return
                full_key, key_id = created
                _LOGGER.log_event(
                    event="api_key_created",
                    src_ip=(scope.get("client") or ("unknown", 0))[0],
                    principal=owner,
                    key_id=key_id,
                    boot_id=BOOT_ID,
                )
                await _send_json_response(
                    send,
                    200,
                    {
                        "key": full_key,
                        "key_id": key_id,
                        "label": label,
                        "hint": "完整 key 仅此一次返回，请立即保存。",
                    },
                )
                return
            if method == "GET":
                await _drain_body(receive)
                await _send_json_response(
                    send,
                    200,
                    {"keys": api_key_store.list(owner)},
                )
                return
            if method == "DELETE":
                query = _query_params(scope)
                key_id = (query.get("key_id") or "").strip()
                if not key_id:
                    await _drain_body(receive)
                    await _send_json_response(
                        send, 400, {"error": "invalid_request", "hint": "缺少 key_id。"}
                    )
                    return
                # Other owners' key_ids are indistinguishable from missing
                # ones: revoke is scoped by owner, so this returns False for
                # both and we answer 404 either way.
                revoked = api_key_store.revoke(key_id, owner)
                if not revoked:
                    await _send_json_response(
                        send, 404, {"error": "not_found"}
                    )
                    return
                _LOGGER.log_event(
                    event="api_key_revoked",
                    src_ip=(scope.get("client") or ("unknown", 0))[0],
                    principal=owner,
                    key_id=key_id,
                    boot_id=BOOT_ID,
                )
                await _send_json_response(send, 200, {"revoked": key_id})
                return
            await _drain_body(receive)
            await _send_json_response(send, 405, {"error": "method_not_allowed"})
            return
        if scope["type"] == "http" and scope.get("path") == "/oauth/authorize":
            # Self-hosted authorization-code grant (RFC 6749 §4.1) for
            # browser-capable MCP clients (Claude Code style) that only
            # speak this flow. WE implement the redirect matching, so
            # RFC 8252 §7.3 applies: loopback redirects match on any
            # port — the exact rule GitCode lacks. The consent page is
            # our own (identity via the GitCode login leg when
            # configured, manual username otherwise).
            if sdk_as_active:
                # SDK AS mode (ticket 6): the authorize surface is the
                # custom /authorize human consent page (mounted ahead of
                # the SDK's own /authorize route inside `inner`), and the
                # GitCode-login reentry from the callback targets
                # /authorize accordingly. Ticket 8 keeps this handler as
                # the SDK_AUTH=off (fallback) implementation: the SDK-off
                # wiring has no custom /authorize page, so this branch
                # remains the only authorize surface in that mode.
                await _drain_body(receive)
                await _send_404(send)
                return
            if not _auth_server_enabled():
                await _drain_body(receive)
                await _send_404(send)
                return
            query = _query_params(scope)
            redirect_uri = (query.get("redirect_uri") or "").strip()
            response_type = (query.get("response_type") or "").strip()
            code_param = (query.get("code") or "").strip()
            binding_token = (query.get("st") or "").strip()
            signed_in = ""
            if code_param:
                # Returning from the GitCode login leg with the same grant:
                # re-render the consent page instead of minting a new code.
                # The session carries the original redirect_uri, so the
                # reentry link does not need to repeat it. The verified
                # identity comes from the server-side binding (st).
                session = auth_code_store.lookup(code_param)
                if session is None:
                    await _drain_body(receive)
                    await _send_html_response(
                        send,
                        200,
                        _render_auth_pages().error_page(
                            "授权请求已过期或已使用，请回到客户端重新发起。"
                        ),
                    )
                    return
                redirect_uri = session.redirect_uri
                if binding_token:
                    bound = identity_binding.peek(binding_token)
                    if bound is None or bound[0] != code_param:
                        await _drain_body(receive)
                        await _send_html_response(
                            send,
                            200,
                            _render_auth_pages().error_page(
                                "登录会话已过期或无效，请重新通过 GitCode 登录。"
                            ),
                        )
                        return
                    signed_in = bound[1]
            else:
                # PKCE is mandatory for this public-client grant (RFC 7636
                # §4.4.1, MCP spec authorization requirements): every
                # authorization code is bound to a challenge at mint time,
                # so an intercepted code is worthless without the verifier.
                code_challenge = (query.get("code_challenge") or "").strip()
                challenge_method = (query.get("code_challenge_method") or "").strip()
                if not code_challenge or challenge_method != "S256":
                    await _drain_body(receive)
                    await _send_html_response(
                        send,
                        200,
                        _render_auth_pages().error_page(
                            "授权请求缺少 code_challenge 或未使用 S256 方法；"
                            "本服务要求公共客户端强制 PKCE。"
                        ),
                    )
                    return
                if response_type != "code" or not redirect_uri:
                    await _drain_body(receive)
                    await _send_html_response(
                        send,
                        200,
                        _render_auth_pages().error_page(
                            "授权请求缺少 redirect_uri 或 response_type 不是 code。"
                        ),
                    )
                    return
                state = (query.get("state") or "")
                # RFC 8707 resource indicator: the client names the target
                # service; it becomes the aud of the minted tokens. Absent
                # means this server itself (legacy clients stay compatible).
                # Canonical form: strip a trailing slash — clients derive
                # the resource from their server URL ("http://h:p/mcp" →
                # "http://h:p/") while our Host-derived default carries no
                # slash; both forms mean the same resource.
                resource = (query.get("resource") or "").strip().rstrip("/")
                session = auth_code_store.create(
                    redirect_uri, code_challenge, state, resource
                )
            await _drain_body(receive)
            await _send_html_response(
                send,
                200,
                _render_auth_pages().authorize_page(
                    session.code,
                    signed_in=signed_in,
                    gitcode_available=bool(_oauth_client_id()),
                    session_token=binding_token if signed_in else "",
                ),
            )
            return
        if scope["type"] == "http" and scope.get("path") == "/oauth/authorize/confirm":
            # POST from the authorize consent page. Ticket 7 choice, kept
            # as-is: this leg writes the bound identity straight into the
            # shared AuthCodeStore (auth_code_store.bind) instead of
            # calling CannbotAuthProvider.authorize/exchange — the SDK
            # /token exchange consumes the very same store session
            # (provider load/exchange over _SDK_AUTH_CODE_STORE), the
            # ticket-6 wiring suite locks that closed loop end to end,
            # and provider.authorize is the SDK's programmatic
            # /authorize backend whose redirect-echo contract does not
            # fit this HTML form POST. The endpoint itself stays on this
            # handwritten dispatcher in both modes: the ticket mounts
            # only the five feature endpoints as custom routes.
            if not _auth_server_enabled():
                await _drain_body(receive)
                await _send_404(send)
                return
            body = await _drain_body(receive)
            fields: dict[str, str] = {}
            for pair in body.decode("utf-8", "replace").split("&"):
                if "=" in pair:
                    key, _, value = pair.partition("=")
                    fields[unquote_plus(key)] = unquote_plus(value)
            code = fields.get("code", "").strip()
            action = fields.get("action", "")
            if action == "gitcode":
                # Send the browser through the GitCode login leg, coming
                # back to /oauth/authorize with a binding token and the
                # same code.
                await send(
                    {
                        "type": "http.response.start",
                        "status": 302,
                        "headers": [
                            (
                                b"location",
                                (
                                    _public_path()
                                    + "/oauth/gitcode/login?state="
                                    + urllib.parse.quote("authcode:" + code)
                                ).encode(),
                            )
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return
            if action == "allow":
                if _oauth_client_id():
                    # GitCode configured: the username comes ONLY from the
                    # server-side verified binding (one-shot); any username
                    # value in the form is ignored.
                    form_binding = (fields.get("st") or "").strip()
                    verified = (
                        identity_binding.take(form_binding)
                        if form_binding
                        else None
                    )
                    if verified is None or verified[0] != code:
                        await _send_html_response(
                            send,
                            200,
                            _render_auth_pages().error_page(
                                "缺少有效的登录会话，请通过 GitCode 登录后再确认。"
                            ),
                        )
                        return
                    username = verified[1]
                else:
                    # No GitCode application configured: manual username
                    # bootstrap (trusted-network deployments only).
                    username = fields.get("username", "").strip()
                    if not username:
                        await _send_html_response(
                            send,
                            200,
                            _render_auth_pages().error_page("请填写用户名。"),
                        )
                        return
                bound = auth_code_store.bind(code, username)
                if bound is None:
                    await _send_html_response(
                        send,
                        200,
                        _render_auth_pages().error_page(
                            "授权请求已过期或已使用，请回到客户端重新发起。"
                        ),
                    )
                    return
                # Bounce back to the client's redirect_uri with code+state.
                params = {"code": code}
                if bound.state:
                    params["state"] = bound.state
                back = urllib.parse.urlsplit(bound.redirect_uri)
                target = back._replace(
                    query=urllib.parse.urlencode(params)
                ).geturl()
                await send(
                    {
                        "type": "http.response.start",
                        "status": 302,
                        "headers": [(b"location", target.encode())],
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return
            if action == "deny":
                # Atomic compare-and-delete: revoke the grant only when the
                # stored session still matches this code, so a concurrent
                # exchange on another node wins cleanly either way.
                raw = auth_code_store._store.get("ac:" + code)
                session = (
                    auth_code_store._session_from_value(raw) if raw else None
                )
                if session is not None:
                    auth_code_store._store.take_if_equal("ac:" + code, raw)
                params = {"error": "access_denied"}
                if session is not None:
                    if session.state:
                        params["state"] = session.state
                    back = urllib.parse.urlsplit(session.redirect_uri)
                    target = back._replace(
                        query=urllib.parse.urlencode(params)
                    ).geturl()
                else:
                    target = _public_path() + "/activate"
                await send(
                    {
                        "type": "http.response.start",
                        "status": 302,
                        "headers": [(b"location", target.encode())],
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return
            await _send_html_response(
                send,
                200,
                _render_auth_pages().error_page("未知操作。"),
            )
            return
        if (
            scope["type"] == "http"
            and sdk_feature_endpoints
            and scope.get("path") in _SDK_FEATURE_PATHS
        ):
            # Ticket 7 (feature endpoints): in SDK-auth mode the device
            # code/token, activate and GitCode-login legs ride the SDK
            # stack — custom_starlette_routes merged into `inner` by
            # streamable_http_app (lowest matching precedence, and no SDK
            # route claims these paths, so ours serve). The handler bodies
            # are the very ones the branches below run (extracted to
            # module level and shared through _AuthLegDeps), so the
            # per-mode difference is the registration, not the logic. The
            # SDK-off default never enters here (empty path set) and
            # keeps the handwritten dispatch unchanged.
            await inner(scope, receive, send)
            return
        if scope["type"] == "http" and scope.get("path") == "/oauth/device/code":
            # RFC 8628 §3.1 device authorization endpoint (shared body:
            # _handle_device_code).
            await _handle_device_code(scope, receive, send, auth_legs)
            return
        if scope["type"] == "http" and scope.get("path") == "/oauth/device/token":
            # RFC 8628 §3.4/3.5 token polling (shared body:
            # _handle_device_token). Same bare-path treatment.
            await _handle_device_token(scope, receive, send, auth_legs)
            return
        if scope["type"] == "http" and scope.get("path") == "/oauth/gitcode/login":
            # GitCode identity source for the activation page (shared
            # body: _handle_gitcode_login).
            await _handle_gitcode_login(scope, receive, send, auth_legs)
            return
        if scope["type"] == "http" and scope.get("path") == "/oauth/gitcode/callback":
            # Consume the code, exchange for the GitCode username, then
            # bounce back to the activation confirmation (device flow) or
            # the authorize consent page (authorization-code flow) with it
            # (shared body: _handle_gitcode_callback).
            await _handle_gitcode_callback(scope, receive, send, auth_legs)
            return
        if scope["type"] == "http" and scope.get("path") == "/activate":
            # RFC 8628 §3.3 user interaction, including the
            # /activate?code=… one-click direct connect (shared body:
            # _handle_activate).
            await _handle_activate(scope, receive, send, auth_legs)
            return
        if scope["type"] == "http" and scope.get("path") in _discovery_paths(
            "/.well-known/oauth-authorization-server"
        ):
            # RFC 8414 Authorization Server metadata. GitCode itself does not
            # serve this document (its /.well-known path returns the SPA HTML
            # page), so this server acts as the discovery front-end: the 9728
            # document above lists this host in authorization_servers, and
            # this document republishes GitCode's real OAuth endpoints.
            # Clients (OpenCode/cannbot, Claude Code style) walk 9728 -> 8414
            # during the 401 bootstrap; without this document they die with a
            # JSON parse error on GitCode's HTML before ever reaching
            # gitcode.com/oauth/authorize.
            #
            # Dual existence (ticket 8 note): with CANNBOT_MCP_SDK_AUTH=on
            # the SDK mounts its own 8414 route inside `inner`, but this
            # outer handler stays authoritative even in that mode — the
            # SDK's OAuthMetadata has no field for the device
            # authorization endpoint this document must declare (RFC
            # §2.4), so the outer doc shadows the SDK route; with the gate
            # off this block is the whole 8414 surface. It stays.
            await _drain_body(receive)
            public_url = _public_url(scope)
            if _auth_server_enabled():
                if sdk_as_active:
                    # SDK AS mode (ticket 6): the AS route set is the SDK's
                    # (/authorize /token /register, mounted inside `inner`)
                    # plus the self-managed device-code legs (RFC §2.4: the
                    # device authorization endpoint stays declared here —
                    # the SDK's OAuthMetadata has no field for it, so this
                    # document is the authoritative one and the SDK's own
                    # 8414 route stays shadowed by this outer handler).
                    # Known transitional gap: the single token_endpoint
                    # cannot serve the device grant (the SDK handler
                    # rejects it), so metadata-driven device clients keep
                    # using the SDK-off mode. Ticket 8 closed the audit
                    # WITHOUT adding a /token device-grant alias — the
                    # off mode stays the documented answer for those
                    # clients, and TROUBLESHOOTING.md carries the note.
                    await _send_json_response(
                        send,
                        200,
                        {
                            "issuer": public_url,
                            "authorization_endpoint": f"{public_url}/authorize",
                            "token_endpoint": f"{public_url}/token",
                            "device_authorization_endpoint": (
                                f"{public_url}/oauth/device/code"
                            ),
                            "registration_endpoint": f"{public_url}/register",
                            "response_types_supported": ["code"],
                            "grant_types_supported": [
                                "authorization_code",
                                "urn:ietf:params:oauth:grant-type:device_code",
                                "refresh_token",
                            ],
                            "code_challenge_methods_supported": ["S256"],
                            "token_endpoint_auth_methods_supported": ["none"],
                        },
                        _DISCOVERY_CORS_HEADERS,
                    )
                    return
                # Self-hosted authorization server: THIS service
                # is the AS. The device-code grant (RFC 8628) is the primary
                # human flow; no redirect_uri matching is involved, so the
                # GitCode loopback-port dead end does not exist on this leg.
                # Clients discover everything below without any manual
                # client_id: /register hands out a public-client registration
                # (PKCE, no secret). Independent of the GitCode verification
                # track: turning CANNBOT_MCP_GITCODE_VERIFY=off must not
                # take the self-hosted AS's own discovery document down.
                await _send_json_response(
                    send,
                    200,
                    {
                        "issuer": public_url,
                        "authorization_endpoint": f"{public_url}/oauth/authorize",
                        "token_endpoint": f"{public_url}/oauth/device/token",
                        "device_authorization_endpoint": (
                            f"{public_url}/oauth/device/code"
                        ),
                        "registration_endpoint": f"{public_url}/register",
                        "response_types_supported": ["code"],
                        "grant_types_supported": [
                            "authorization_code",
                            "urn:ietf:params:oauth:grant-type:device_code",
                            "refresh_token",
                        ],
                        "code_challenge_methods_supported": ["S256"],
                        "token_endpoint_auth_methods_supported": ["none"],
                    },
                    _DISCOVERY_CORS_HEADERS,
                )
                return
            if not _gitcode_verify_enabled():
                # Forwarding mode republishes GitCode's endpoints; without
                # the GitCode track there is nothing to republish.
                await _send_404(send)
                return
            as_metadata: dict[str, Any] = {
                "issuer": "https://gitcode.com",
                "authorization_endpoint": "https://gitcode.com/oauth/authorize",
                "token_endpoint": "https://gitcode.com/oauth/token",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": ["S256"],
            }
            # No registration_endpoint here: forwarding-mode /register is
            # closed (see below) because it could only return the shared
            # application secret. Clients in this legacy mode obtain the
            # pre-registered application credentials from the administrator
            # out of band; zero-config registration is served by the
            # self-hosted default above.
            await _send_json_response(
                send, 200, as_metadata, _DISCOVERY_CORS_HEADERS
            )
            return
        if scope["type"] == "http" and scope.get("path") == "/register":
            # RFC 7591 dynamic client registration. In self-hosted mode the
            # registration describes OUR auth server: a public client using
            # the device-code grant with PKCE — no secret is needed or sent,
            # and the redirect_uris are informational only (device flow has
            # no redirect). In GitCode-forwarding mode /register is CLOSED:
            # the only credentials it could hand out are the shared
            # pre-registered application id/secret, and returning those to
            # anonymous callers would leak a server-side secret that can
            # mint GitCode authorization grants (clients in forwarding mode
            # get the application credentials from the administrator out of
            # band). The POST body is accepted and ignored. Unauthenticated
            # like the metadata endpoints.
            if sdk_as_active:
                # SDK AS mode (ticket 6): the SDK's RegistrationHandler
                # inside `inner` owns /register — provider.register_client
                # and get_client carry the fixed-public-client semantics,
                # and the SDK route answers with its own RFC 7591 §3.2.1
                # 201 Created registration echo. The handwritten response
                # below yields in this mode and stays as the SDK_AUTH=off
                # (fallback) implementation (ticket 8 keeps it).
                await inner(scope, receive, send)
                return
            await _drain_body(receive)
            if _auth_server_enabled():
                # Independent of the GitCode verification track (see the
                # 8414 metadata above).
                await _send_json_response(
                    send,
                    200,
                    {
                        "client_id": "cannbot-knowledge-public",
                        "client_id_issued_at": int(time.time()),
                        "redirect_uris": [],
                        "grant_types": [
                            "authorization_code",
                            "urn:ietf:params:oauth:grant-type:device_code",
                            "refresh_token",
                        ],
                        "token_endpoint_auth_method": "none",
                        "client_name": "cannbot-knowledge",
                    },
                )
                return
            # Forwarding mode: no dynamic registration. 404 regardless of
            # whether an application is configured.
            await _send_404(send)
            return
        if scope["type"] == "http" and scope.get("path") in _discovery_paths(
            "/.well-known/oauth-protected-resource"
        ):
            # RFC 9728 Protected Resource Metadata (plus the /mcp-suffixed
            # variant some clients probe). Unauthenticated on purpose so MCP
            # clients can discover the authorization server before the first
            # handshake; like /health it bypasses auth, rate limiting and
            # the call log, and 404s only when EVERY dynamic auth track is
            # off (static-token-only mode has no AS to advertise).
            #
            # Why this 9728 surface exists ALONGSIDE the SDK's (the
            # dual existence is deliberate two-phase design):
            # CANNBOT_MCP_SDK_AUTH=on
            # mounts the SDK's own 9728 route inside `inner` for the
            # /mcp-suffixed path only — create_protected_resource_routes
            # with the metadata URL build_resource_metadata_url derives
            # from resource_server_url — and the branch right below passes
            # that one path through. The SDK registers NO route for the
            # bare well-known path, which clients also probe, so THIS
            # handler answers it in both modes (mirroring the SDK metadata
            # built from the same AuthSettings). With the gate off the SDK
            # route does not exist at all and this block is the whole 9728
            # surface. Deleting the block would break the bare path in
            # BOTH modes and the off mode entirely; it stays.
            #
            # authorization_servers must point at a host that actually serves
            # RFC 8414 metadata. Pointing it directly at https://gitcode.com
            # makes clients fetch gitcode.com/.well-known/oauth-authorization-server,
            # which GitCode answers with its SPA HTML — the client dies with a
            # JSON parse error before ever reaching /oauth/authorize (verified
            # against cannbot v1.1.2 and Claude Code 2.1.317). So this server
            # advertises itself as the discovery front-end and republishes
            # GitCode's endpoints via its own 8414 document above.
            #
            # SDK mode serves every 9728 path from _sdk_pr_metadata (the
            # branch below). The earlier pass-through of the bare
            # /mcp-suffixed path to `inner` was a route mismatch, not a
            # hand-off: create_protected_resource_routes registers the
            # SDK route at /.well-known/oauth-protected-resource +
            # urlparse(resource_server_url).path — WITH the PUBLIC_URL
            # prefix — so `inner` answers only that prefixed form, never
            # the bare suffixed one. A gateway that rewrites RFC 9728
            # insertion URLs by stripping only its own prefix delivers
            # the suffixed request here as bare+/mcp; forwarding it into
            # `inner` hit no route and surfaced as a Starlette 404 —
            # Claude Code dies at discovery ("Dynamic Client Registration
            # rejected") because the 401's resource_metadata points at
            # that very URL. The prefixed form is still matched one
            # branch up by _discovery_paths and lands here too, so this
            # block is the single 9728 responder in SDK mode; with the
            # gate off the handwritten variant below is the whole
            # surface.
            await _drain_body(receive)
            if sdk_rs_active:
                # SDK mode, every probed path (bare, bare+/mcp, prefixed
                # insertion forms): answer with the metadata the SDK route
                # serves, built from the same AuthSettings, so all 9728
                # variants agree on the resource identity (the full
                # endpoint URL, the fix for RFC defect 1.3).
                await _send_json_response(
                    send, 200, _sdk_pr_metadata, _DISCOVERY_CORS_HEADERS
                )
                return
            if not _gitcode_verify_enabled() and not _auth_server_enabled():
                await _send_404(send)
                return
            public_url = _public_url(scope)
            await _send_json_response(
                send,
                200,
                {
                    "resource": public_url,
                    "authorization_servers": [public_url],
                    "scopes_supported": [],
                    "resource_name": "cannbot-knowledge",
                    "bearer_methods_supported": ["header"],
                },
                _DISCOVERY_CORS_HEADERS,
            )
            return
        if scope["type"] != "http" or scope.get("path") != "/mcp":
            await inner(scope, receive, send)
            return
        if sdk_rs_active:
            # SDK mode: BearerAuthBackend (over the ticket-2
            # CannbotTokenVerifier) and RequireAuthMiddleware inside
            # `inner` own /mcp admission. The handwritten four-track chain
            # below would reject exactly the full-endpoint-audience tokens
            # that stack accepts (RFC 8707: the resource identity is
            # resource_server_url now), so it yields here; ticket 8 keeps
            # it as the SDK_AUTH=off (fallback) implementation. Phase-1
            # gaps to be rebuilt on the SDK stack: IP cooldown,
            # per-principal rate limiting and principal attribution in the
            # call log. Call logging itself stays on via the meta below.
            body = await _drain_body(receive)
            request_meta.set(
                RequestMeta(
                    transport="http",
                    principal=None,
                    jsonrpc_id=_request_jsonrpc_id(body),
                )
            )
            await inner(
                scope,
                _replay_body(receive, body),
                send,
            )
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
                [_www_authenticate_challenge(scope)],
            )
            return
        matched, principal = tokens.match(presented)
        if not matched:
            # Credential routing: local credentials (self-service API keys,
            # self-issued JWTs) are verified locally ONLY and never sent to
            # GitCode — a cross-track fallback would leak them in an
            # outbound Authorization header. Opaque tokens (GitCode PATs or
            # access tokens) go to the GitCode track only; a failed local
            # verification never falls back to external verification.
            if presented.startswith("cbk_live_"):
                # Self-service machine keys. scrypt verification keyed by the
                # embedded key_id (O(1) row lookup); principal is
                # "owner/label" so audit and rate limiting both answer who
                # provisioned the machine AND which slot it uses. Like the
                # JWT track, gated on the self-hosted AS: keys can only be
                # minted through an AS-issued JWT, so closing the AS closes
                # them end to end.
                if api_key_store is not None and _auth_server_enabled():
                    api_key_hit = api_key_store.verify(presented)
                    if api_key_hit is not None:
                        matched = True
                        principal = f"{api_key_hit[0]}/{api_key_hit[1]}"
            elif _is_self_issued_jwt(presented):
                # Self-issued tokens. Local signature check, no outbound
                # call; the username from the JWT sub becomes the principal
                # for rate limiting and the log. Audience: this request's
                # view of the server URL (RFC 8707). The whole track is
                # closed when the self-hosted authorization server is off
                # (CANNBOT_MCP_AUTH_SERVER=off): closing the AS must close
                # both issuance AND acceptance.
                if token_authority is not None and _auth_server_enabled():
                    self_issued = token_authority.verify(
                        presented,
                        "access",
                        SelfIssuedTokenAuthority._default_audience(scope),
                    )
                    if self_issued is not None:
                        matched = True
                        principal = self_issued[0]
            elif verifier is not None and _gitcode_verify_enabled():
                # GitCode track: a token absent from the static list may
                # still be a valid GitCode access token; verify it against
                # the GitCode user API before rejecting it as no_match.
                verified = await verifier.verify_token(presented)
                if verified is not None:
                    matched = True
                    principal = verified.subject
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
                [_www_authenticate_challenge(scope)],
            )
            return
        cooldown.record_success(client_ip)
        decision = limiter.check(_rate_limit_key(presented, principal), limit=rate_limit)
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

def _rate_limit_key(presented: str, principal: str | None) -> str:
    """Rate-limit key: principal when known, otherwise the raw token.

    CANNBOT_MCP_RATE_KEY=token restores the legacy per-token keying.
    """
    if (os.environ.get(RATE_KEY_ENV) or "").strip().lower() == "token":
        return presented
    return principal or presented


def _auth_server_enabled() -> bool:
    """CANNBOT_MCP_AUTH_SERVER: self-hosted AS (default on).

    'off' closes the self-hosted authorization server END TO END: the
    issuance endpoints (device code/token, authorize, activate, api-keys,
    GitCode login legs) 404, and the /mcp acceptance of self-issued JWTs
    and API keys stops. What remains is the GitCode-forwarding behaviour
    of the dual-track era: 8414 republishes GitCode's endpoints and
    /register no longer hands out credentials.
    """
    return (os.environ.get(AUTH_SERVER_ENV) or "").strip().lower() != "off"

def _oauth_client_id() -> str | None:
    """Pre-registered GitCode OAuth application id (enables the DCR proxy)."""
    raw = (os.environ.get(OAUTH_CLIENT_ID_ENV) or "").strip()
    return raw or None

def _oauth_client_secret() -> str | None:
    """Pre-registered GitCode OAuth application secret, if configured."""
    raw = (os.environ.get(OAUTH_CLIENT_SECRET_ENV) or "").strip()
    return raw or None


class GitCodeLoginBroker:
    """PKCE verifier side-channel storage on the shared StateStore.

    The pairing (state → verifier) is exactly one round trip: begin()
    writes it with a 600s TTL, take_verifier() atomically consumes it
    (StateStore.take). Multi-node deployments share the same store, so the
    login may start on one node and complete on another. The state key is
    either a device user_code ("ABCD-EFGH") or an authcode marker
    ("authcode:<token_urlsafe>") — the pkce: prefix namespaces both.
    """

    _STATE_TTL_S = 600.0

    def __init__(self, store: state_store.StateStore) -> None:
        self._store = store

    def begin(self, user_code: str) -> tuple[str, str] | None:
        """Start a login for a state; returns (verifier, challenge)."""
        verifier = secrets.token_urlsafe(48)[:64]
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        self._store.put("pkce:" + user_code, verifier, self._STATE_TTL_S)
        return verifier, challenge

    def take_verifier(self, user_code: str) -> str | None:
        """Consume the PKCE verifier for a callback (one-shot)."""
        return self._store.take("pkce:" + user_code)


class VerifiedIdentityBinding:
    """Server-side binding of a GitCode-verified login to a pending grant.

    After the GitCode callback exchanges the authorization code for a
    username, the username is stored HERE under an unguessable random
    token — never in a URL or a form field. Confirmation pages peek at
    the binding to render the identity card; the final allow POST
    consumes it (one-shot) and binds the stored username to the grant.
    A crafted link or a forged form field can no longer impersonate: the
    confirmation only trusts what the server itself stored after the
    authenticated GitCode exchange. Shared StateStore → multi-node safe.
    """

    _TTL_S = 600.0

    def __init__(self, store: state_store.StateStore) -> None:
        self._store = store

    def create(self, grant_code: str, username: str) -> str:
        token = secrets.token_urlsafe(32)
        payload = json.dumps({"code": grant_code, "username": username})
        self._store.put("actsession:" + token, payload, self._TTL_S)
        return token

    def _decode(self, raw: str | None) -> tuple[str, str] | None:
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(data, dict):
            return None
        code = data.get("code")
        username = data.get("username")
        if not isinstance(code, str) or not isinstance(username, str):
            return None
        return code, username

    def peek(self, token: str) -> tuple[str, str] | None:
        """Read the binding without consuming it (page rendering)."""
        return self._decode(self._store.get("actsession:" + token))

    def take(self, token: str) -> tuple[str, str] | None:
        """Consume the binding (final allow — one-shot)."""
        return self._decode(self._store.take("actsession:" + token))


async def _gitcode_exchange_login(
    code: str, verifier: str, redirect_uri: str
) -> str | None:
    """Exchange an authorization code for the GitCode username (login)."""
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": _oauth_client_id() or "",
        "client_secret": _oauth_client_secret() or "",
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }
    api_base = (
        os.environ.get(GITCODE_API_ENV, "").strip().rstrip("/")
        or "https://api.gitcode.com"
    )
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GITCODE_TOKEN_URL,
                data=form,
                headers={"Accept": "application/json"},
            )
            if token_response.status_code != 200:
                return None
            token = token_response.json().get("access_token")
            if not token:
                return None
            user_response = await client.get(
                f"{api_base}/api/v5/user",
                headers={"Authorization": f"Bearer {token}"},
            )
            if user_response.status_code != 200:
                return None
            login = user_response.json().get("login")
            return login if isinstance(login, str) and login else None
    except httpx.HTTPError:
        return None

def _www_authenticate_challenge(scope: dict[str, Any]) -> tuple[bytes, bytes]:
    """WWW-Authenticate header for 401s, with the RFC 6750 + RFC 9728 hint.

    MCP 2026-07-28 recommends pointing clients straight at the protected
    resource metadata so the discovery round-trip is one hop.
    """
    metadata_url = (
        f"{_public_url(scope)}/.well-known/oauth-protected-resource"
    )
    value = f'Bearer resource_metadata="{metadata_url}"'
    return b"www-authenticate", value.encode("ascii")


def _public_path() -> str:
    """Path prefix a reverse proxy strips before proxying to this service.

    ``CANNBOT_MCP_PUBLIC_PATH`` declares that prefix (for example
    ``/mcp/gateway/mcp-server``). RFC 8414/9728 discovery inserts
    ``/.well-known/...`` between the origin and the path, so standard
    clients probe ``/.well-known/<doc>/<prefix>`` relative to the proxy
    host; the proxy forwards those root-level URLs verbatim, so this
    service must answer them relative to its own root. Empty (default)
    keeps the bare discovery paths only. Restored by the E2E bug-1 fix:
    ticket 8 wrongly removed the whole mechanism, regressing sub-path
    gateway deployments (where the production service actually runs) in
    BOTH auth modes.
    """
    raw = (os.environ.get(PUBLIC_PATH_ENV) or "").strip()
    if raw and not raw.startswith("/"):
        raw = "/" + raw
    return raw.rstrip("/")


def _discovery_paths(base: str) -> tuple[str, ...]:
    """Route paths serving the ``base`` discovery document.

    Bare path and its ``/mcp`` variant always serve; with
    ``CANNBOT_MCP_PUBLIC_PATH`` set, the RFC 8414 insertion forms with
    the proxy prefix (with and without a trailing ``/mcp``) serve too -
    clients derive both from the issuer and from the MCP endpoint URL.
    """
    paths = [base, f"{base}/mcp"]
    prefix = _public_path()
    if prefix:
        paths.append(f"{base}{prefix}")
        paths.append(f"{base}{prefix}/mcp")
    return tuple(paths)


def _public_url(scope: dict[str, Any]) -> str:
    """The URL clients use to reach this server, as used in metadata.

    Dual existence (ticket 8 note): CANNBOT_MCP_SDK_AUTH=on derives the
    resource identity from CANNBOT_MCP_PUBLIC_URL once at import time
    (AuthSettings.resource_server_url; the SDK's
    build_resource_metadata_url then derives every metadata path from
    that single value). THIS per-request derivation is what the
    SDK_AUTH=off handwritten chain still needs — 8414/9728 documents,
    JWT audiences and redirect bases all call it — so both mechanisms
    stay. No PUBLIC_PATH prefix mechanism exists in either mode: every
    path this server emits is root-absolute, and the RFC's
    PUBLIC_URL/PUBLIC_PATH dual-variable problem is solved by the
    single-variable derivation, not by a second prefix knob.
    """
    public_url = os.environ.get("CANNBOT_MCP_PUBLIC_URL")
    if not public_url:
        request_host = _http_headers(scope).get("host")
        if not request_host:
            request_host = (scope.get("server") or ("localhost",))[0]
        public_url = f"http://{request_host}"
    return public_url.rstrip("/")

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
    return os.environ.get(LOG_UPLOAD_REMOTE_ENV, "").strip()

def _upload_branch() -> str:
    return os.environ.get(LOG_UPLOAD_BRANCH_ENV, "").strip() or "main"

def _start_uploader(transport: str, logging_enabled: bool, interval_s: int) -> bool:
    """The uploader thread runs only for served HTTP traffic worth sharing.

    stdio is single-machine by definition and stdio logging is off by default,
    so there is nothing to distribute; the interval gate keeps the default
    deployment byte-for-byte identical to a server without the feature.
    A remote must be configured explicitly: with no default remote the
    feature never pushes anywhere unless the deployer opts in.
    """
    return (
        transport == "http"
        and logging_enabled
        and interval_s > 0
        and _upload_remote() != ""
    )

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
        # Static tokens are now an optional bootstrap channel. The service
        # is safe to start with an empty list as long as ANY auth track is
        # live: GitCode verification, the self-hosted
        # authorization server (device/authcode grants → JWTs), or the
        # static list itself. All three off means the /mcp endpoint would
        # accept nothing but the OAuth endpoints would still mint tokens
        # for anyone who can reach the service — refuse instead.
        gitcode_track = _gitcode_verify_enabled()
        as_track = _auth_server_enabled()
        if not tokens and not gitcode_track and not as_track:
            print(
                "cannbot-mcp: refusing to start HTTP transport: no auth "
                "track is available. Configure at least one of: "
                f"{TOKENS_ENV} (static tokens), CANNBOT_MCP_GITCODE_VERIFY "
                "(default on), or CANNBOT_MCP_AUTH_SERVER (default on). "
                "Set the last two to 'off' only together with a static "
                "token list.",
                file=sys.stderr,
            )
            return 2
        if not tokens:
            print(
                "cannbot-mcp: static token list is empty; machine clients "
                "should use self-service API keys (log in via OAuth, then "
                "POST /api/keys). Continuing with GitCode/self-issued "
                "authentication only.",
                file=sys.stderr,
            )
        import uvicorn

        host = os.environ.get(HOST_ENV, "").strip() or "127.0.0.1"
        port = _env_int(PORT_ENV, 8090)
        rate_limit = _env_int(RATE_LIMIT_ENV, 0)
        shared_store = state_store.open_state_store()
        app = build_http_app(
            mcp_server,
            tokens,
            SlidingWindowRateLimiter(shared_store),
            IpCooldown(shared_store),
            rate_limit,
            host,
            GitCodeTokenVerifier() if _gitcode_verify_enabled() else None,
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
