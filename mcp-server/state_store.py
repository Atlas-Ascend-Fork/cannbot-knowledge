"""Unified short-TTL state abstraction with two interchangeable backends.

The MCP server keeps several small pieces of per-request state (device-code
sessions, authorization-code grants, PKCE pairings, rate-limit counters).
In single-process deployments each piece lives fine in process memory or a
local sqlite file; horizontal scaling needs them shared. StateStore is the
seam: one interface, a stdlib-only sqlite implementation (default, zero new
dependencies) and a Redis implementation selected by environment variable.
Callers stay backend-agnostic.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Protocol


class StateStore(Protocol):
    """Tiny TTL-keyed state contract shared by all auth surfaces.

    Values are plain strings; callers own serialization. ``take`` must be
    atomic: two concurrent takers see the value exactly once between them.
    """

    def put(self, key: str, value: str, ttl_s: float) -> None:
        """Store ``value`` under ``key``; expires after ``ttl_s`` seconds."""
        ...

    def get(self, key: str) -> str | None:
        """Read without deleting; expired entries read as missing."""
        ...

    def take(self, key: str) -> str | None:
        """Atomically read-and-delete; second take reads as missing."""
        ...

    def take_if_equal(self, key: str, expected: str) -> bool:
        """Atomically delete ``key`` only if its value equals ``expected``.

        Returns True when the key existed with that value and is now gone.
        """
        ...

    def count(self, prefix: str, window_s: float) -> int:
        """Sliding-window count of events recorded under ``prefix``.

        ``record`` below appends an event with the current timestamp;
        ``count`` returns how many landed inside the trailing window.
        """
        ...

    def record(self, prefix: str) -> None:
        """Append one event under ``prefix`` (feeds ``count``)."""
        ...

    def close(self) -> None:
        ...


class SqliteStateStore:
    """Default backend: one sqlite file, guarded by a single lock.

    Atomicity comes from SQLite itself — every mutating call is one
    statement inside the connection's implicit transaction, and the lock
    serializes threads within the process. TTL is a column, checked lazily
    (reads delete-on-sight of expired rows) plus a cheap opportunistgc.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS state (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                prefix TEXT NOT NULL,
                at     REAL NOT NULL
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_prefix ON events(prefix, at)"
        )
        self._connection.commit()

    def _purge(self, now: float) -> None:
        self._connection.execute(
            "DELETE FROM state WHERE expires_at < ?", (now,)
        )
        self._connection.execute(
            "DELETE FROM events WHERE at < ?", (now - 3600.0,)
        )

    def put(self, key: str, value: str, ttl_s: float) -> None:
        with self._lock:
            now = time.time()
            self._purge(now)
            self._connection.execute(
                "INSERT INTO state VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
                "expires_at=excluded.expires_at",
                (key, value, now + ttl_s),
            )
            self._connection.commit()

    def get(self, key: str) -> str | None:
        with self._lock:
            now = time.time()
            self._connection.execute(
                "DELETE FROM state WHERE expires_at < ?", (now,)
            )
            row = self._connection.execute(
                "SELECT value FROM state WHERE key = ?", (key,)
            ).fetchone()
            self._connection.commit()
        return row[0] if row is not None else None

    def take(self, key: str) -> str | None:
        with self._lock:
            now = time.time()
            self._connection.execute(
                "DELETE FROM state WHERE expires_at < ?", (now,)
            )
            row = self._connection.execute(
                "SELECT value FROM state WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                self._connection.commit()
                return None
            deleted = self._connection.execute(
                "DELETE FROM state WHERE key = ?", (key,)
            ).rowcount
            self._connection.commit()
            return row[0] if deleted else None

    def take_if_equal(self, key: str, expected: str) -> bool:
        with self._lock:
            now = time.time()
            row = self._connection.execute(
                "SELECT value FROM state WHERE key = ? AND expires_at >= ?",
                (key, now),
            ).fetchone()
            if row is None or row[0] != expected:
                self._connection.commit()
                return False
            deleted = self._connection.execute(
                "DELETE FROM state WHERE key = ?", (key,)
            ).rowcount
            self._connection.commit()
            return deleted > 0

    def record(self, prefix: str) -> None:
        with self._lock:
            self._connection.execute(
                "INSERT INTO events VALUES (?,?)", (prefix, time.time())
            )
            self._connection.commit()

    def count(self, prefix: str, window_s: float) -> int:
        with self._lock:
            now = time.time()
            row = self._connection.execute(
                "SELECT COUNT(*) FROM events WHERE prefix = ? AND at >= ?",
                (prefix, now - window_s),
            ).fetchone()
        return int(row[0])

    def close(self) -> None:
        with self._lock:
            self._connection.close()


class RedisStateStore:
    """Shared backend for multi-node deployments (opt-in).

    Selected via CANNBOT_MCP_STATE_BACKEND=redis; the redis client is
    imported lazily so default deployments pull no new dependency.
    Construction fails loudly when Redis is unreachable — auth state is
    fail-closed, never silently degraded to per-process memory.
    """

    _TAKE_IF_EQUAL_LUA = """
    local v = redis.call('GET', KEYS[1])
    if v == false then return 0 end
    if v ~= ARGV[1] then return 0 end
    redis.call('DEL', KEYS[1])
    return 1
    """

    def __init__(self, url: str) -> None:
        import redis  # lazy: only required for the redis backend

        self._client = redis.Redis.from_url(
            url, decode_responses=True, socket_connect_timeout=3.0
        )
        self._client.ping()  # fail closed at construction, not first use
        self._take_if_equal = self._client.register_script(
            self._TAKE_IF_EQUAL_LUA
        )

    def put(self, key: str, value: str, ttl_s: float) -> None:
        # psetex keeps millisecond precision: auth flows use sub-second
        # TTLs in tests (600s in production, but the contract is the same).
        self._client.psetex(key, max(1, int(round(ttl_s * 1000))), value)

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def take(self, key: str) -> str | None:
        return self._client.getdel(key)

    def take_if_equal(self, key: str, expected: str) -> bool:
        return bool(self._take_if_equal(keys=[key], args=[expected]))

    def record(self, prefix: str) -> None:
        member = uuid.uuid4().hex
        now = time.time()
        pipe = self._client.pipeline()
        pipe.zadd(f"events:{prefix}", {member: now})
        pipe.zremrangebyscore(
            f"events:{prefix}", 0, now - 3600.0
        )
        pipe.execute()

    def count(self, prefix: str, window_s: float) -> int:
        now = time.time()
        return int(
            self._client.zcount(
                f"events:{prefix}", now - window_s, now
            )
        )

    def close(self) -> None:
        self._client.close()


def open_state_store() -> StateStore:
    """Backend selector: sqlite (default) or redis via environment.

    Sqlite resolves its path exactly like the other auth stores: the
    CANNBOT_MCP_AUTH_DB environment variable's directory when set, else
    the default state directory under HOME.
    """
    backend = (os.environ.get("CANNBOT_MCP_STATE_BACKEND") or "").strip().lower()
    if backend == "redis":
        url = (os.environ.get("CANNBOT_MCP_STATE_REDIS_URL") or "").strip()
        if not url:
            raise RuntimeError(
                "cannbot-mcp: CANNBOT_MCP_STATE_BACKEND=redis requires "
                "CANNBOT_MCP_STATE_REDIS_URL"
            )
        return RedisStateStore(url)
    # Default: sqlite beside the other auth state.
    from server import DEFAULT_LOG_DIR

    db_env = (os.environ.get("CANNBOT_MCP_AUTH_DB") or "").strip()
    base = Path(db_env).parent if db_env else DEFAULT_LOG_DIR
    return SqliteStateStore(base / "state.db")
