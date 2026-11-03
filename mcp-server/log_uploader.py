# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Periodic in-process upload of call logs to a configured git remote.

The log directory itself doubles as a git worktree: the first round turns it
into a repository (git init + remote), every later round stages calls-*.jsonl,
commits when anything changed and pushes to the configured branch. Multiple
instances push per-day files into the same remote; same-day collisions are
merged line-wise (union driver), and identical rows are deduplicated again by
analyze_logs' call_id idempotency key (legacy rows without call_id keep the
historical ts/tool/principal tuple), so the remote converges without loss.

Everything here is best effort: a failing push costs one stderr line and is
retried on the next round; no exception ever escapes into the request path.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_GIT_TIMEOUT_S = 60.0
_GITIGNORE_LINES = ("reports/\n",)
_GITATTRIBUTES_TEXT = "calls-*.jsonl merge=union\n"


class LogUploader:
    """Daemon thread that periodically pushes calls-*.jsonl to a git remote."""

    def __init__(
        self,
        *,
        remote: str,
        branch: str,
        interval_s: float,
        log_dir: Path,
        boot_id: str,
    ) -> None:
        self.remote = remote
        self.branch = branch
        self.interval_s = interval_s
        self.log_dir = Path(log_dir)
        self.boot_id = boot_id
        self.thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self.interval_s <= 0 or self.thread is not None:
            return
        self._stop_event.clear()
        self.thread = threading.Thread(
            target=self._loop, name="cannbot-mcp-log-uploader", daemon=True
        )
        self.thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self.thread
        if thread is not None:
            thread.join(timeout=_GIT_TIMEOUT_S)
            self.thread = None

    def _loop(self) -> None:
        while not self._stop_event.wait(self.interval_s):
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001 - never escape the thread
                print(
                    f"cannbot-mcp: log upload round failed: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )

    def _git(self, *arguments: str) -> tuple[int, str, str]:
        try:
            completed = subprocess.run(
                ["git", "-C", str(self.log_dir), *arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"git {arguments[0]} failed: {exc}") from exc
        return completed.returncode, completed.stdout, completed.stderr

    def _ensure_worktree(self) -> None:
        """Idempotently make the log dir a git worktree bound to self.remote."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if not (self.log_dir / ".git").exists():
            code, _out, err = self._git("init")
            if code != 0:
                raise RuntimeError(f"git init failed: {err}")
        self._write_control_files()
        code, out, _err = self._git("remote", "get-url", "origin")
        if code != 0 or out.strip() != self.remote:
            self._git("remote", "remove", "origin")
            code, _out, err = self._git("remote", "add", "origin", self.remote)
            if code != 0:
                raise RuntimeError(f"git remote add failed: {err}")
        if not self._has_identity():
            self._git("config", "user.name", f"cannbot-mcp-{self.boot_id}")
            self._git(
                "config", "user.email", f"cannbot-mcp-{self.boot_id}@{socket.gethostname()}"
            )

    def _write_control_files(self) -> None:
        gitignore = self.log_dir / ".gitignore"
        text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        if "reports/" not in text:
            gitignore.write_text(text + "".join(_GITIGNORE_LINES), encoding="utf-8")
        gitattributes = self.log_dir / ".gitattributes"
        stored = (
            gitattributes.read_text(encoding="utf-8")
            if gitattributes.exists()
            else ""
        )
        if "merge=union" not in stored:
            gitattributes.write_text(
                stored + _GITATTRIBUTES_TEXT, encoding="utf-8"
            )

    def _has_identity(self) -> bool:
        code, out, _err = self._git("config", "user.email")
        return code == 0 and bool(out.strip())

    def _commit_message(self) -> str:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        host = socket.gethostname()
        return f"mcp logs {date}: {host} boot {self.boot_id}"

    def _recover_with_rebase(self) -> bool:
        """Pull the remote branch (union merge) after a rejected push.

        The worktree is clean at this point (everything is committed), so a
        rebase is safe; the union driver keeps both instances' lines when the
        same day file diverged.
        """
        code, _out, err = self._git(
            "pull", "--rebase", "origin", f"refs/heads/{self.branch}"
        )
        if code != 0:
            self._git("rebase", "--abort")
            print(
                f"cannbot-mcp: log upload pull failed: {err.strip()[:400]}",
                file=sys.stderr,
            )
            return False
        return True

    def run_once(self) -> None:
        """One upload round; never raises for expected operational failures."""
        if not self.log_dir.is_dir() or not list(self.log_dir.glob("calls-*.jsonl")):
            return
        try:
            self._ensure_worktree()
            code, _out, err = self._git("add", "--", "calls-*.jsonl")
            if code != 0:
                raise RuntimeError(f"git add failed: {err}")
            code, _out, _err = self._git("diff", "--cached", "--quiet")
            if code == 0:
                # Nothing new staged, but an earlier round may have committed
                # and failed to push; without this retry that local commit
                # would never reach the remote.
                self._push_unpushed_commits()
                return
            code, _out, err = self._git("commit", "-m", self._commit_message())
            if code != 0:
                raise RuntimeError(f"git commit failed: {err}")
            self._push_or_recover()
        except RuntimeError as exc:
            print(f"cannbot-mcp: log upload failed: {exc}", file=sys.stderr)

    def _push_unpushed_commits(self) -> None:
        """Best-effort retry for commits a previous round failed to push.

        Local-only check (no fetch): commits on HEAD that no remote-tracking
        ref knows about. A just-initialized repository without commits makes
        rev-list fail; that simply means nothing to retry.
        """
        code, out, _err = self._git(
            "rev-list", "--count", "HEAD", "--not", "--remotes"
        )
        if code != 0:
            return
        try:
            unpushed = int(out.strip() or "0")
        except ValueError:
            return
        if unpushed > 0:
            self._push_or_recover()

    def _push_or_recover(self) -> None:
        code, _out, err = self._git(
            "push", "origin", f"HEAD:refs/heads/{self.branch}"
        )
        if code == 0:
            return
        # A rejected push means the remote moved (another instance pushed the
        # same day file). Try to converge via rebase; anything else (network,
        # credentials, missing remote) is a diagnostic for the next round.
        remote_tip = subprocess.run(
            ["git", "ls-remote", "--exit-code", "--heads", self.remote,
             f"refs/heads/{self.branch}"],
            check=False, capture_output=True, text=True, timeout=_GIT_TIMEOUT_S,
        )
        if remote_tip.returncode != 0:
            print(
                f"cannbot-mcp: log upload push failed: remote unreachable or "
                f"branch absent; retrying next round",
                file=sys.stderr,
            )
            return
        if not self._recover_with_rebase():
            return
        code, _out, err = self._git(
            "push", "origin", f"HEAD:refs/heads/{self.branch}"
        )
        if code != 0:
            print(
                f"cannbot-mcp: log upload push failed: {err.strip()[:400]}",
                file=sys.stderr,
            )
