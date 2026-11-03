# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Unit tests for log_uploader.LogUploader against local bare-repo remotes."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import log_uploader  # noqa: E402


def run_git(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


def make_bare_remote(path: Path) -> Path:
    completed = run_git("init", "--bare", str(path))
    assert completed.returncode == 0, completed.stderr
    completed = run_git("-C", str(path), "symbolic-ref", "HEAD", "refs/heads/main")
    assert completed.returncode == 0, completed.stderr
    return path


def clone_remote(bare: Path, target: Path) -> Path:
    completed = run_git("clone", "--branch", "main", str(bare), str(target))
    assert completed.returncode == 0, completed.stderr
    return target


def write_calls_file(log_dir: Path, name: str, rows: list[dict]) -> Path:
    target = log_dir / name
    target.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return target


def call_row(tool: str = "discover", boot_id: str = "ab12cd34") -> dict:
    return {
        "schema": "mcp-call-log.v2",
        "ts": "2026-10-29T08:00:00.123Z",
        "boot_id": boot_id,
        "transport": "http",
        "principal": "zhangsan",
        "tool": tool,
        "args": {},
        "ok": True,
        "count": 1,
        "latency_ms": 12.0,
    }


class LogUploaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.log_dir = self.base / "logs"
        self.log_dir.mkdir()
        self.bare = make_bare_remote(self.base / "remote.git")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_uploader(self, **overrides) -> log_uploader.LogUploader:
        fields = dict(
            remote=str(self.bare),
            branch="main",
            interval_s=60,
            log_dir=self.log_dir,
            boot_id="ab12cd34",
        )
        fields.update(overrides)
        return log_uploader.LogUploader(**fields)

    def commit_count(self) -> int:
        completed = run_git("-C", str(self.bare), "rev-list", "--all", "--count")
        assert completed.returncode == 0, completed.stderr
        return int(completed.stdout.strip())

    def test_upload_pushes_calls_files_and_marks_their_source(self) -> None:
        rows = [call_row(), call_row(tool="search")]
        write_calls_file(self.log_dir, "calls-2026-10-29.jsonl", rows)
        self.make_uploader().run_once()
        clone = clone_remote(self.bare, self.base / "clone")
        uploaded = clone / "calls-2026-10-29.jsonl"
        self.assertTrue(uploaded.is_file())
        self.assertEqual(
            rows,
            [
                json.loads(line)
                for line in uploaded.read_text(encoding="utf-8").splitlines()
            ],
        )
        completed = run_git("-C", str(clone), "log", "-1", "--format=%s")
        message = completed.stdout.strip()
        self.assertIn("ab12cd34", message)

    def test_zero_interval_starts_no_thread(self) -> None:
        uploader = self.make_uploader(interval_s=0)
        uploader.start()
        try:
            self.assertIsNone(uploader.thread)
        finally:
            uploader.stop()

    def test_reports_directory_is_ignored(self) -> None:
        write_calls_file(self.log_dir, "calls-2026-10-29.jsonl", [call_row()])
        (self.log_dir / "reports").mkdir()
        (self.log_dir / "reports" / "report.json").write_text("{}", encoding="utf-8")
        self.make_uploader().run_once()
        clone = clone_remote(self.bare, self.base / "clone")
        self.assertFalse((clone / "reports").exists())
        completed = run_git("-C", str(clone), "ls-files")
        self.assertNotIn("reports/report.json", completed.stdout.splitlines())

    def test_idle_round_creates_no_new_commit(self) -> None:
        write_calls_file(self.log_dir, "calls-2026-10-29.jsonl", [call_row()])
        uploader = self.make_uploader()
        uploader.run_once()
        self.assertEqual(1, self.commit_count())
        uploader.run_once()
        self.assertEqual(1, self.commit_count())

    def test_failed_push_is_retried_on_the_next_idle_round(self) -> None:
        rows = [call_row(), call_row(tool="search")]
        write_calls_file(self.log_dir, "calls-2026-10-29.jsonl", rows)
        broken = self.make_uploader(remote=str(self.base / "dead" / "remote.git"))
        sink = io.StringIO()
        with contextlib.redirect_stderr(sink):
            broken.run_once()
        self.assertEqual(1, len(sink.getvalue().strip().splitlines()))
        self.assertEqual(0, self.commit_count())
        completed = run_git("-C", str(self.log_dir), "rev-list", "--count", "HEAD")
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(1, int(completed.stdout.strip()))
        # no new log files: the next round only retries the pending push
        recovered = self.make_uploader()
        sink = io.StringIO()
        with contextlib.redirect_stderr(sink):
            recovered.run_once()
        self.assertEqual("", sink.getvalue())
        self.assertEqual(1, self.commit_count())
        completed = run_git("-C", str(self.log_dir), "rev-list", "--count", "HEAD")
        self.assertEqual(1, int(completed.stdout.strip()))
        clone = clone_remote(self.bare, self.base / "clone")
        uploaded = clone / "calls-2026-10-29.jsonl"
        self.assertTrue(uploaded.is_file())
        self.assertEqual(
            rows,
            [
                json.loads(line)
                for line in uploaded.read_text(encoding="utf-8").splitlines()
            ],
        )

    def test_missing_log_dir_is_a_quiet_noop(self) -> None:
        sink = io.StringIO()
        with contextlib.redirect_stderr(sink):
            self.make_uploader(log_dir=self.base / "absent").run_once()
        self.assertEqual("", sink.getvalue())
        self.assertFalse((self.base / "absent").exists())

    def test_unreachable_remote_is_diagnosed_and_survived(self) -> None:
        write_calls_file(self.log_dir, "calls-2026-10-29.jsonl", [call_row()])
        uploader = self.make_uploader(remote=str(self.base / "dead" / "remote.git"))
        sink = io.StringIO()
        with contextlib.redirect_stderr(sink):
            uploader.run_once()
        self.assertEqual(1, len(sink.getvalue().strip().splitlines()))
        uploader = self.make_uploader(
            remote=str(self.base / "dead" / "remote.git"), interval_s=0.2
        )
        sink = io.StringIO()
        try:
            with contextlib.redirect_stderr(sink):
                uploader.start()
                time.sleep(0.8)
                self.assertTrue(uploader.thread is not None and uploader.thread.is_alive())
        finally:
            uploader.stop()
            time.sleep(0.1)

    def test_stop_is_idempotent(self) -> None:
        write_calls_file(self.log_dir, "calls-2026-10-29.jsonl", [call_row()])
        uploader = self.make_uploader(interval_s=1)
        uploader.start()
        thread = uploader.thread
        self.assertIsNotNone(thread)
        uploader.stop()
        uploader.stop()
        self.assertFalse(thread.is_alive())

    def test_second_instance_converges_via_union_merge(self) -> None:
        other_dir = self.base / "logs-b"
        other_dir.mkdir()
        write_calls_file(
            self.log_dir, "calls-2026-10-29.jsonl", [call_row(boot_id="11111111")]
        )
        write_calls_file(
            other_dir, "calls-2026-10-29.jsonl", [call_row(tool="search", boot_id="22222222")]
        )
        self.make_uploader().run_once()
        self.make_uploader(log_dir=other_dir, boot_id="22222222").run_once()
        clone = clone_remote(self.bare, self.base / "clone")
        merged = [
            json.loads(line)
            for line in (clone / "calls-2026-10-29.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual({"11111111", "22222222"}, {row["boot_id"] for row in merged})


if __name__ == "__main__":
    unittest.main()
