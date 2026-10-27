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

import shutil
import tempfile
import unittest
from pathlib import Path

from governance.contracts.checks import Document, RunContext, links
from governance.contracts.knowledge import Contract

ROOT = Path(__file__).resolve().parents[1]


class ReferencePrecedenceTests(unittest.TestCase):
    def test_first_normalized_definition_wins(self) -> None:
        for first, second, reference in (
            ("ref", "ref", "ref"),
            ("REF", "ref", "ReF"),
            ("Guide  Name", "guide\tname", "guide name"),
        ):
            with self.subTest(first=first, second=second):
                text = f"[guide][{reference}]\n\n[{first}]: first.md\n[{second}]: last.md\n"
                self.assertEqual([("first.md", False)], links.markdown_targets(text))

    def test_forward_backward_and_collapsed_references_keep_first_target(self) -> None:
        definitions = '[guide]: <first.md> "Title"\n[GUIDE]: last.md\n'
        for text in (f"[guide][]\n\n{definitions}", f"{definitions}\n[guide][]"):
            with self.subTest(text=text):
                self.assertEqual([("first.md", False)], links.markdown_targets(text))

    def test_external_duplicate_does_not_change_local_link_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.md"
            for first, last in (
                ("https://example.com/guide", "missing.md"),
                ("local.md", "https://example.com/guide"),
            ):
                with self.subTest(first=first):
                    text = f"[guide][ref]\n\n[ref]: {first}\n[ref]: {last}\n"
                    result = links.links_in_text(text, source)
                    expected = [] if first.startswith("https:") else [
                        ("local.md", source.parent / "local.md", 1)
                    ]
                    self.assertEqual(expected, result)

    def test_image_reference_uses_first_definition_and_is_not_a_link(self) -> None:
        text = "![diagram][image]\n\n[image]: first.png\n[IMAGE]: last.png\n"
        self.assertEqual([("first.png", 1)], links.markdown_image_targets(text))
        self.assertEqual([], links.markdown_targets(text))

    def test_code_fence_definition_does_not_shadow_real_definition(self) -> None:
        text = (
            "~~~markdown\n[ref]: code.md\n~~~\n"
            "[ref]: first.md\n[guide][ref]\n"
        )
        self.assertEqual([("first.md", False)], links.markdown_targets(text))


class ReferenceLinkCheckTests(unittest.TestCase):
    def test_link_validation_uses_first_target_for_accept_and_reject(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            contract = Contract(root)
            relative = Path("knowledge/ops/ascendc/apis/source.md")
            path = root / relative
            path.parent.mkdir(parents=True)
            (path.parent / "valid.md").write_text("# Valid\n", encoding="utf-8")
            (root / "outside.md").write_text("# Outside\n", encoding="utf-8")
            for first, last, expected in (
                ("valid.md", "missing.md", []),
                ("missing.md", "valid.md", ["link.missing"]),
                ("../../../../outside.md", "valid.md", ["link.outside_bundle"]),
            ):
                with self.subTest(first=first):
                    text = f"[guide][ref]\n\n[ref]: {first}\n[REF]: {last}\n"
                    path.write_text(text, encoding="utf-8")
                    document = Document.create(
                        contract, path, relative, text, None, text
                    )
                    issues = links.check(contract, document, RunContext())
                    self.assertEqual(expected, [issue.code for issue in issues])
                    for issue in issues:
                        self.assertEqual(1, issue.line)
                        self.assertEqual(first, issue.details)


if __name__ == "__main__":
    unittest.main()
