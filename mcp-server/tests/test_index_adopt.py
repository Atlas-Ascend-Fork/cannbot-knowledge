# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""index_adopt.py contract: adopt only byte-identical indexes, refuse drift."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))

from test_server import (  # noqa: E402
    CARD_FIXTURE,
    build_fixture_index,
    make_fixture_root,
)

INDEX_TOOL = REPO_ROOT / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
ADOPT_TOOL = REPO_ROOT / "mcp-server/index_adopt.py"


class IndexAdoptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = make_fixture_root(Path(self.temporary.name))
        card = self.root / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        card.write_text(CARD_FIXTURE, encoding="utf-8")
        build_fixture_index(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_adopt(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ADOPT_TOOL), "--knowledge-root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_verify(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INDEX_TOOL), "--knowledge-root", str(self.root), "verify"],
            check=False,
            capture_output=True,
            text=True,
        )

    def simulate_fresh_clone(self) -> None:
        """A fresh git clone rewrites every file's mtime while content stays."""
        for card in (self.root / "knowledge").rglob("*.md"):
            stamp = time.time_ns()
            os.utime(card, ns=(stamp, stamp))

    def test_adopt_after_fresh_clone_restores_validity(self) -> None:
        self.assertEqual(0, self.run_verify().returncode)
        self.simulate_fresh_clone()
        stale = self.run_verify()
        self.assertNotEqual(0, stale.returncode)
        self.assertIn("changed after index build", stale.stderr + stale.stdout)
        adopted = self.run_adopt()
        self.assertEqual(0, adopted.returncode, adopted.stderr)
        self.assertEqual(0, self.run_verify().returncode)

    def test_adopt_is_noop_when_already_valid(self) -> None:
        adopted = self.run_adopt()
        self.assertEqual(0, adopted.returncode, adopted.stderr)
        self.assertIn("0 mtimes restored", adopted.stdout)
        self.assertEqual(0, self.run_verify().returncode)

    def test_adopt_refuses_same_size_content_change(self) -> None:
        card = self.root / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        card.write_text(
            CARD_FIXTURE.replace("between GM and UB", "between GM and UZ"),
            encoding="utf-8",
        )
        adopted = self.run_adopt()
        self.assertEqual(1, adopted.returncode)
        self.assertIn("content differs", adopted.stderr)
        self.assertNotEqual(0, self.run_verify().returncode)

    def test_adopt_refuses_size_change(self) -> None:
        card = self.root / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        card.write_text(CARD_FIXTURE + "\nextra line\n", encoding="utf-8")
        adopted = self.run_adopt()
        self.assertEqual(1, adopted.returncode)
        self.assertIn("size differs", adopted.stderr)

    def test_adopt_refuses_card_set_change(self) -> None:
        extra = self.root / "knowledge/ops/ascendc/apis/extra_card.md"
        extra.write_text(CARD_FIXTURE, encoding="utf-8")
        adopted = self.run_adopt()
        self.assertEqual(1, adopted.returncode)
        self.assertIn("card set differs", adopted.stderr)

    def test_adopt_refuses_missing_index(self) -> None:
        (self.root / "artifacts/indexes/knowledge.sqlite3").unlink()
        adopted = self.run_adopt()
        self.assertEqual(1, adopted.returncode)
        self.assertIn("index missing", adopted.stderr)


if __name__ == "__main__":
    unittest.main()
