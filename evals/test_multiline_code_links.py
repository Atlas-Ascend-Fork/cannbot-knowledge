# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

import unittest

from governance.contracts.checks.links import markdown_targets, mask_code


class MultilineCodeSpanTest(unittest.TestCase):
    def test_multiline_code_link_is_not_a_real_target(self):
        text = "Inline code: `start\n[example](not_a_link.md)\nend`\n\n[real](real.md)\n"
        self.assertEqual(markdown_targets(text), [("real.md", False)])
        masked = mask_code(text)
        self.assertEqual(len(masked), len(text))
        self.assertEqual(masked.count("\n"), text.count("\n"))

    def test_double_backticks_can_contain_single_backticks(self):
        text = "Example: ``a`\n[fake](missing.md)\nb`` [real](real.md)"
        self.assertEqual(markdown_targets(text), [("real.md", False)])

    def test_mismatched_backtick_runs_do_not_hide_links(self):
        self.assertEqual(markdown_targets("Example: `a [real](real.md)``"), [("real.md", False)])

    def test_blank_paragraph_does_not_extend_a_code_span(self):
        text = "Open `text\n\n[real](real.md) and closing`"
        self.assertEqual(markdown_targets(text), [("real.md", False)])

    def test_single_line_and_fenced_code_are_unchanged(self):
        text = "`[inline](inline.md)`\n\n```md\n[fenced](fenced.md)\n```\n\n[real](real.md)"
        self.assertEqual(markdown_targets(text), [("real.md", False)])

    def test_separate_list_items_do_not_extend_a_code_span(self):
        text = "- Open `text\n- [real](real.md) and closing`"
        self.assertEqual(markdown_targets(text), [("real.md", False)])

    def test_heading_starts_a_separate_block(self):
        text = "Open `text\n## Heading [real](real.md) and closing`"
        self.assertEqual(markdown_targets(text), [("real.md", False)])
