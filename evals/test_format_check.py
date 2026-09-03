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

import hashlib
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / ".gitcode/scripts/format_check.py"
LICENSE_SHA256 = "cb282ac2b66d7d6734c3fb354db792b28cf23ab29fbc16d5cfd8bd542bedeb1e"
LICENSE_NOTICE = """# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License."""


def has_cann_license_header(text: str) -> bool:
    return LICENSE_NOTICE in text[:2000]


def license_header_paths() -> list[Path]:
    paths = list(ROOT.glob("*.sh"))
    for directory in (ROOT / "governance", ROOT / "evals"):
        for suffix in ("*.py", "*.yaml", "*.yml"):
            paths.extend(directory.rglob(suffix))
    return sorted(path for path in paths if path.read_text(encoding="utf-8").strip())


def load_entrypoint():
    spec = importlib.util.spec_from_file_location("format_check_test", ENTRYPOINT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ENTRYPOINT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FormatCheckSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entrypoint = load_entrypoint()

    def test_summary_omits_ci_meta_context(self) -> None:
        findings = [
            {
                "check": "format",
                "tier": "P1",
                "path": f"knowledge/example_{index}.md",
                "line": index + 1,
                "code": "format.example",
                "message": "Example finding.",
                "details": None,
            }
            for index in range(21)
        ]
        summary = self.entrypoint.render_summary(
            {"checked": 21, "findings": findings}, 0, "", ""
        )
        for text in ("format-check.json", "结果文件", "OBS", "Summary", "下载"):
            self.assertNotIn(text, summary)
        self.assertNotIn("检查范围", summary)
        self.assertEqual(21, summary.count("| P1 |"))
        self.assertIn("knowledge/example_20.md:21", summary)
        self.assertEqual(
            "FormatCheck 未生成有效结果。",
            self.entrypoint.runtime_result(ROOT)["findings"][0]["message"],
        )

    def test_public_artifact_hides_the_runner_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "format.json"
            self.entrypoint.write_result(
                output,
                {"root": "/runner/private/repository", "checked": 1, "findings": []},
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(".", result["root"])
        self.assertNotIn("/runner", json.dumps(result))


class LicenseComplianceTests(unittest.TestCase):
    def test_matcher_accepts_shebang_and_rejects_missing_header(self) -> None:
        self.assertTrue(has_cann_license_header(f"#!/usr/bin/env python3\n{LICENSE_NOTICE}\n"))
        self.assertFalse(has_cann_license_header("#!/usr/bin/env python3\nprint('missing')\n"))

    def test_repository_sources_have_cann_license_header(self) -> None:
        for path in license_header_paths():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(
                    has_cann_license_header(path.read_text(encoding="utf-8")),
                    f"missing CANN 2.0 license header: {path.relative_to(ROOT)}",
                )

    def test_license_file_contains_complete_cann_v2_text(self) -> None:
        license_bytes = (ROOT / "LICENSE").read_bytes()
        license_text = license_bytes.decode("utf-8")
        self.assertEqual(LICENSE_SHA256, hashlib.sha256(license_bytes).hexdigest())
        self.assertTrue(license_text.startswith("CANN Open Software License Agreement Version 2.0\n"))
        self.assertIn("the validity of other provisions of this Agreement", license_text)
        self.assertTrue(license_text.rstrip().endswith("END OF THE TERMS AND CONDITIONS"))

    def test_oat_policy_declares_cann_v2_matcher_and_exempts_license(self) -> None:
        root = ET.parse(ROOT / "OAT.xml").getroot()
        policy = root.find(".//policyitem[@type='license'][@name='CANN-2.0']")
        copyright_policy = root.find(
            ".//policyitem[@type='copyright'][@name='Huawei Technologies Co., Ltd.']"
        )
        matcher = root.find(".//licensematcher[@name='CANN-2.0']/licensetext")
        self.assertIsNotNone(policy)
        self.assertIsNotNone(copyright_policy)
        self.assertIsNotNone(matcher)
        filter_name = policy.attrib.get("filefilter") if policy is not None else None
        self.assertEqual("defaultPolicyFilter", filter_name)
        license_filter = root.find(f".//filefilter[@name='{filter_name}']")
        self.assertIsNotNone(license_filter)
        self.assertIsNotNone(
            license_filter.find("./filteritem[@type='filepath'][@name='LICENSE']")
            if license_filter is not None
            else None
        )
        filename_filter = root.find(".//filefilter[@name='licenseFileNamePolicyFilter']")
        self.assertIsNotNone(filename_filter)
        self.assertIsNone(
            filename_filter.find("./filteritem[@name='LICENSE']")
            if filename_filter is not None
            else None
        )
        self.assertEqual(
            "copyrightPolicyFilter",
            copyright_policy.attrib.get("filefilter") if copyright_policy is not None else None,
        )
        self.assertIn(
            "CANN Open Software License Agreement Version 2.0",
            matcher.attrib["name"] if matcher is not None else "",
        )


if __name__ == "__main__":
    unittest.main()
