# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TRITON_ROOT = REPOSITORY_ROOT / "knowledge/ops/triton"
EXPERIENCE_REFERENCE = re.compile(r"\bexp_[A-Za-z0-9_]+\b")
ANCHOR_HEADING = re.compile(r"^### (exp_[A-Za-z0-9_]+)\s*$", re.MULTILINE)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\([^)\n]*\)")
MARKDOWN_EXPERIENCE_LINK = re.compile(
    r"\[(exp_[A-Za-z0-9_]+)\]\(([^)\n]+)\)"
)
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
NON_EXPERIENCE_TOKENS = {"exp_x", "exp_val", "exp_vals", "exp_result", "exp_buf"}
SKELETON_CARDS = {
    "flash_attention_causal": "flash_attention_causal.py",
    "gemm_basic": "gemm_basic.py",
    "moe_dispatch": "moe_dispatch.py",
    "rmsnorm_fused": "rmsnorm_fused.py",
}
KKB_SKELETON_ROOT = (
    "cannbot-skills_5171_kkb_pr/blob/"
    "e195a77116202190f6b706d8ea802b712e8cc3f4/"
    "ops/triton-knowledge-retrieval/knowledge/pages/skeletons"
)


def _body_without_frontmatter_and_code(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        frontmatter_end = text.find("\n---\n", 4)
        if frontmatter_end != -1:
            text = text[frontmatter_end + 5 :]
    return CODE_FENCE.sub("", text)


def _is_inside_markdown_link(line: str, position: int) -> bool:
    return any(
        match.start() <= position < match.end()
        for match in MARKDOWN_LINK.finditer(line)
    )


class TritonReferenceIntegrityTests(unittest.TestCase):
    def test_triton_experience_references_resolve(self) -> None:
        cards = sorted(TRITON_ROOT.rglob("*.md"))
        anchors: dict[str, Path] = {}
        for path in cards:
            for anchor in ANCHOR_HEADING.findall(path.read_text(encoding="utf-8")):
                self.assertNotIn(
                    anchor,
                    anchors,
                    f"duplicate experience anchor: {anchor} in {path}",
                )
                anchors[anchor] = path

        broken: list[str] = []
        for path in cards:
            if path.name == "index.md":
                continue
            relative = path.relative_to(REPOSITORY_ROOT)
            body = _body_without_frontmatter_and_code(path)
            for line_number, line in enumerate(body.splitlines(), 1):
                if line.lstrip().startswith("### exp_"):
                    continue
                for match in EXPERIENCE_REFERENCE.finditer(line):
                    token = match.group(0)
                    if token in NON_EXPERIENCE_TOKENS:
                        continue
                    location = f"{relative}:{line_number}"
                    if token not in anchors:
                        broken.append(f"{location}: unresolved {token}")
                        continue
                    if line[match.end() : match.end() + 5] == ".yaml":
                        continue
                    if not _is_inside_markdown_link(line, match.start()):
                        broken.append(f"{location}: {token} is not linked to its anchor")

            for match in MARKDOWN_EXPERIENCE_LINK.finditer(body):
                token, url = match.group(1), match.group(2)
                if token in NON_EXPERIENCE_TOKENS or token not in anchors:
                    continue
                target_path = url.split("#", 1)[0]
                target = (
                    path
                    if not target_path
                    else (path.parent / target_path).resolve()
                )
                if not target.exists():
                    broken.append(f"{relative}: link target missing: {url}")
                elif f"### {token}" not in target.read_text(encoding="utf-8"):
                    broken.append(f"{relative}: anchor missing in {url}")

        self.assertEqual([], broken, "\n".join(broken))

    def test_skeleton_examples_are_self_contained(self) -> None:
        broken: list[str] = []
        for card, skeleton in SKELETON_CARDS.items():
            path = TRITON_ROOT / "examples" / f"{card}.md"
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(REPOSITORY_ROOT)
            if "完整骨架见源文件" in text or re.search(
                rf"`skeletons/{re.escape(skeleton)}`", text
            ):
                broken.append(f"{relative}: broken skeleton source path remains")
            if "## 完整骨架" not in text or "```python" not in text:
                broken.append(f"{relative}: inline skeleton code is missing")
            if f"{KKB_SKELETON_ROOT}/{skeleton}" not in text:
                broken.append(f"{relative}: KKB skeleton source URL is missing")
        self.assertEqual([], broken, "\n".join(broken))


if __name__ == "__main__":
    unittest.main()
