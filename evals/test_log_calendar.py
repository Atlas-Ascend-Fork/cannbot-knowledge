# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from governance.contracts.checks.logs import check_repository


class LogCalendarTest(unittest.TestCase):
    def findings_for(self, date):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "logs").mkdir()
            (root / "logs" / f"{date}.md").write_text(
                f"# {date}\n\n## [08:00] test | Calendar fixture\n"
                "\n### Summary\nsummary\n\n### Details\ndetails\n",
                encoding="utf-8",
            )
            return check_repository(SimpleNamespace(root=root))

    def test_invalid_calendar_dates_are_rejected(self):
        for date in ["2026-02-30", "2025-02-29", "2026-13-01", "2026-00-10", "0000-01-01"]:
            with self.subTest(date=date):
                self.assertIn("log.filename", {issue.code for _, issue in self.findings_for(date)})

    def test_valid_regular_and_leap_dates_are_accepted(self):
        for date in ["2026-02-28", "2024-02-29"]:
            with self.subTest(date=date):
                self.assertEqual(self.findings_for(date), [])
