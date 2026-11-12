"""Windows compatibility shim for the Unix ``fcntl`` module (vendored dependency support).

The upstream skills target Linux/macOS agents and use ``fcntl.flock`` for
inter-process file locking. Windows Python has no ``fcntl``; this shim maps
``flock`` onto ``msvcrt.locking`` over a single byte at the file start so the
vendored scripts remain importable and keep cross-process locking semantics.

Known divergence from Unix ``flock``: ``msvcrt.LK_LOCK`` retries for about
10 seconds and then raises ``OSError``, where ``flock`` blocks indefinitely.
Callers must treat ``OSError`` from this shim as "lock contention", not as a
corrupt state file. ``LOCK_NB`` maps to ``LK_NBLCK``, which fails immediately.

Keep this module limited to the surface the vendored scripts use:
``flock``, ``LOCK_EX``, ``LOCK_SH``, ``LOCK_NB`` and ``LOCK_UN``.
"""

from __future__ import annotations

import os

import msvcrt

LOCK_SH = 1
LOCK_EX = 2
LOCK_NB = 4
LOCK_UN = 8


def flock(fd: int, operation: int) -> None:
    if operation & LOCK_UN:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        return
    mode = msvcrt.LK_NBLCK if operation & LOCK_NB else msvcrt.LK_LOCK
    os.lseek(fd, 0, os.SEEK_SET)
    msvcrt.locking(fd, mode, 1)
