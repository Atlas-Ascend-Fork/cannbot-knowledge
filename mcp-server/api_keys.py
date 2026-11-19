# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Self-service machine tokens for users authenticated via OAuth.

The server only persists a scrypt hash of each key's secret plus its
random salt — the full key is shown exactly once at creation time.
Verification recomputes the hash and compares it in constant time;
revocation is a one-way flag, never a delete, so audit rows survive.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
import threading
import time
from pathlib import Path


class ApiKeyStore:
    """Sqlite-backed store for self-issued API keys (scrypt-hashed)."""

    _PREFIX = "cbk_live_"
    _MAX_PER_OWNER = 10

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id     TEXT PRIMARY KEY,
                owner      TEXT NOT NULL,
                label      TEXT NOT NULL,
                key_hash   TEXT NOT NULL,
                salt       TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_used   REAL,
                revoked    INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _hash_secret(self, secret: str, salt: str) -> str:
        digest = hashlib.scrypt(
            secret.encode(), salt=salt.encode(), n=2 ** 14, r=8, p=1
        )
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def create(self, owner: str, label: str) -> tuple[str, str] | None:
        """Issue a key; returns ``(full_key, key_id)`` or None if rejected."""
        if not label or not label.strip() or len(label) > 32:
            return None
        with self._lock:
            row = self._connection.execute(
                "SELECT COUNT(*) FROM api_keys WHERE owner = ? AND revoked = 0",
                (owner,),
            ).fetchone()
            if row[0] >= self._MAX_PER_OWNER:
                return None
            # urlsafe alphabets include "_", so neither partition("_") nor
            # rpartition("_") can find the key_id/secret boundary reliably.
            # Use an underscore-free key_id so the FIRST underscore after
            # it is always the separator.
            key_id = "k" + secrets.token_hex(8)
            secret = secrets.token_urlsafe(32)
            salt = secrets.token_urlsafe(16)
            key_hash = self._hash_secret(secret, salt)
            self._connection.execute(
                """
                INSERT INTO api_keys
                    (key_id, owner, label, key_hash, salt, created_at)
                VALUES (?,?,?,?,?,?)
                """,
                (key_id, owner, label, key_hash, salt, time.time()),
            )
            self._connection.commit()
        return f"{self._PREFIX}{key_id}_{secret}", key_id

    def verify(self, presented: str) -> tuple[str, str] | None:
        """Check a presented key; returns ``(owner, label)`` or None."""
        if not presented.startswith(self._PREFIX):
            return None
        # key_id is hex (no underscores); the first underscore after it is
        # the key_id/secret separator.
        body = presented.removeprefix(self._PREFIX)
        key_id, sep, secret = body.partition("_")
        if not sep or not key_id or not secret:
            return None
        with self._lock:
            row = self._connection.execute(
                """
                SELECT owner, label, key_hash, salt, revoked
                FROM api_keys WHERE key_id = ?
                """,
                (key_id,),
            ).fetchone()
            if row is None or row[4]:
                return None
            owner, label, key_hash, salt = row[0], row[1], row[2], row[3]
            if not hmac.compare_digest(self._hash_secret(secret, salt), key_hash):
                return None
            try:
                self._connection.execute(
                    "UPDATE api_keys SET last_used = ? WHERE key_id = ?",
                    (time.time(), key_id),
                )
                self._connection.commit()
            except sqlite3.Error:
                pass
        return owner, label

    def list(self, owner: str) -> list[dict]:
        """List an owner's live keys (never key_hash/salt), newest first."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT key_id, label, created_at, last_used
                FROM api_keys WHERE owner = ? AND revoked = 0
                ORDER BY created_at DESC
                """,
                (owner,),
            ).fetchall()
        return [
            {
                "key_id": row[0],
                "label": row[1],
                "created_at": row[2],
                "last_used": row[3],
            }
            for row in rows
        ]

    def revoke(self, key_id: str, owner: str) -> bool:
        """Revoke a live key owned by ``owner``; returns True if it existed."""
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE api_keys SET revoked = 1
                WHERE key_id = ? AND owner = ? AND revoked = 0
                """,
                (key_id, owner),
            )
            self._connection.commit()
        return cursor.rowcount > 0

    def count(self, owner: str) -> int:
        """Number of live (non-revoked) keys owned by ``owner``."""
        with self._lock:
            row = self._connection.execute(
                "SELECT COUNT(*) FROM api_keys WHERE owner = ? AND revoked = 0",
                (owner,),
            ).fetchone()
        return int(row[0])
