#!/usr/bin/env python3

import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[4]
SCRIPT = Path(__file__).with_name("field_notes_lint.py")


def _card(title="可用标题", validation="- 构建退出 0（来源平台：a3；证据等级：tool_observed）。"):
    return f"""---
type: "Runbook"
title: "{title}"
description: "验证 linter 的最小现场卡。"
tags: [task.debugging, topic.compilation]
status: stable
sources: []
created_at: '2026-08-14T00:00:00Z'
updated_at: '2026-08-14T00:00:00Z'
platforms: [a3]
---

# {title}

## 现象

kernel 编译报错，定位为根因单元。

## 适用场景

- 工程形态：classic Ascend C 直调。
- API 路径：kernel 构建入口。
- 验证过的平台与版本：a3，CANN unknown。
- 适用粒度：exact_task。
- 路线优先级：recommended_fastpath。
- 不适用：其他平台与工具链版本。

## 判别方法

完整机制单元。

## 验证信号

{validation}
"""


class RunbookLintTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(REPO / "governance", self.root / "governance")
        for directory in (
            "knowledge/runtime",
            "knowledge/common",
            "knowledge/graph",
            "knowledge/model",
            "knowledge/ops",
            "knowledge/ops/ascendc",
            "knowledge/ops/shared",
            "knowledge/model/inference",
            "knowledge/model/shared",
            "knowledge/ops/triton",
            "knowledge/ops/tilelang",
            "knowledge/ops/pypto",
        ):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        (self.root / "knowledge/ops/ascendc/runbooks/compilation").mkdir(parents=True)
        (self.root / "knowledge/index.md").write_text(
            '---\nokf_version: "0.2"\n---\n# knowledge\n', encoding="utf-8"
        )

    def tearDown(self):
        self.temporary.cleanup()

    def _run(self, content):
        card = self.root / "knowledge/ops/ascendc/runbooks/compilation" / "card.md"
        card.write_text(content, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_card_passes(self):
        result = self._run(_card())
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_validation_bullet_requires_platform_and_level(self):
        result = self._run(_card(validation="- 构建退出 0。"))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("验证信号未逐条标来源平台", result.stdout)
        self.assertIn("验证信号未逐条标可用证据等级", result.stdout)

    def test_missing_apply_scenario_section_warns(self):
        result = self._run(_card().replace("## 适用场景\n", ""))
        self.assertEqual(0, result.returncode)
        self.assertIn("缺 `## 适用场景`", result.stdout)


if __name__ == "__main__":
    unittest.main()
