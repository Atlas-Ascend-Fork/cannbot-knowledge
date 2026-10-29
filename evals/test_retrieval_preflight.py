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
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

import yaml

from evals.run_retrieval import main, preflight_cases, query_arguments, run_cases
from evals.test_retrieval_index import make_root, run_index


def scope(**conditions):
    return {"schema": "model.inference.v1", "any_of": [{"all_of": conditions}]}


class RetrievalPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        make_root(cls.root)
        directory = cls.root / "knowledge/model/inference/optimizations"
        directory.mkdir(parents=True)
        for slug, declaration, draft in [
            ("bringup", scope(objective=["bringup"]), False),
            ("unknown", None, False),
            ("mla", scope(phase=["decode"], model_features={"all_of": ["mla"]}), False),
            ("draft", None, True),
        ]:
            metadata = {"type": "Optimization", "title": "范围夹具", "description": "检索协议的确定性夹具。",
                        "tags": ["task.optimization", "topic.attention"], "status": "draft" if draft else "stable",
                        "platforms": [] if draft else ["a3"], "sources": [{"resource": "https://example.com/preflight"}],
                        "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z"}
            if declaration is not None:
                metadata["scope"] = declaration
            (directory / (slug + ".md")).write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n\n# 范围夹具\n\n未命中查询词的正文。\n")
        built = run_index(cls.root, "build")
        if built.returncode:
            raise AssertionError(built.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def case(self, slug="bringup", **overrides):
        return {"id": "fixture", "query": "absent-lexical-term", "expected": ["model/inference/optimizations/" + slug],
                "filters": {"domain": "model", "technology": "inference", "platform": ["a3"], "status": "stable"}, **overrides}

    def check(self, case):
        return preflight_cases({"cases": [case]}, {"repository": self.root})

    def test_accepts_declared_match_without_claiming_lexical_or_human_match(self):
        report = self.check(self.case(scope=scope(objective=["bringup"])))
        self.assertEqual("ready", report["status"])
        self.assertEqual("match", report["cases"][0]["groups"][0]["alternatives"][0]["scope_match"]["state"])
        self.assertIn("not relevance", report["note"])

    def test_scope_conflict_rejects_invalid_positive_instead_of_dropping_it(self):
        report = self.check(self.case(scope=scope(objective=["latency"])))
        self.assertEqual(["fixture"], report["failed_cases"])
        self.assertEqual("scope_conflict", report["cases"][0]["groups"][0]["alternatives"][0]["reason"])
        self.assertEqual(1, len(report["cases"]))

    def test_unknown_stays_eligible_but_explicit_absence_conflicts(self):
        declaration = scope(phase=["decode"], model_features={"none_of": ["mla"]})
        unknown = self.check(self.case("unknown", scope=declaration))
        self.assertEqual("ready", unknown["status"])
        self.assertEqual("unknown", unknown["cases"][0]["groups"][0]["alternatives"][0]["scope_match"]["state"])
        self.assertEqual("invalid_expectations", self.check(self.case("mla", scope=declaration))["status"])

    def test_unlocated_draft_cannot_be_a_stable_platform_positive(self):
        report = self.check(self.case("draft"))
        self.assertEqual("invalid_expectations", report["status"])
        self.assertEqual(["a3"], report["cases"][0]["request"]["filters"]["platforms"])
        metadata = report["cases"][0]["groups"][0]["alternatives"][0]["metadata"]
        self.assertEqual("draft", metadata["status"])
        self.assertEqual([], metadata["platforms"])
        draft = self.case("draft", filters={"domain": "model", "technology": "inference", "status": "draft", "include_unlocated": True})
        self.assertEqual("ready", self.check(draft)["status"])
        self.assertEqual("invalid_expectations", self.check(self.case(filters={"platform": ["a2"]}))["status"])

    def test_alternative_group_requires_one_eligible_member_and_all_mandatory_groups(self):
        prefix = "model/inference/optimizations/"
        alternatives = [[prefix + "draft", prefix + "unknown"]]
        self.assertEqual("ready", self.check(self.case(expected=[], expected_any=alternatives))["status"])
        self.assertEqual("invalid_expectations", self.check(self.case("draft", expected_any=alternatives))["status"])
        missing = self.check(self.case("missing"))
        self.assertEqual("missing_concept", missing["cases"][0]["groups"][0]["alternatives"][0]["reason"])

    def test_malformed_or_duplicate_cases_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "must be lists"):
            self.check(self.case(expected="model/inference/optimizations/unknown"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            preflight_cases({"cases": [self.case(), self.case()]}, {"repository": self.root})
        with self.assertRaises(ValueError):
            self.check(self.case(scope={"schema": "unknown.schema", "any_of": [{"all_of": {}}]}))

    def test_scope_cannot_hide_in_generic_filters_in_either_execution_path(self):
        for key in ("scope", "scope_json", "scope_file", "scope-json", "scope-file",
                    "scope-j", "scope_f"):
            for explicit in (False, True):
                with self.subTest(key=key, explicit_scope=explicit):
                    case = self.case()
                    case["filters"][key] = "hidden-scope"
                    if explicit:
                        case["scope"] = scope(phase=["decode"])
                    with self.assertRaisesRegex(ValueError, "only Scope input"):
                        query_arguments(case)
                    with self.assertRaisesRegex(ValueError, "only Scope input"):
                        self.check(case)
                    with patch("evals.run_retrieval.subprocess.run") as query:
                        with self.assertRaisesRegex(ValueError, "only Scope input"):
                            run_cases({"cases": [case]}, {"repository": self.root})
                        query.assert_not_called()

    def test_canonical_scope_and_legacy_arguments_remain_supported(self):
        legacy = self.case()
        arguments = query_arguments(legacy)
        self.assertNotIn("--scope-json", arguments)
        self.assertIn("--platform", arguments)
        scoped = {**legacy, "scope": scope(phase=["decode"])}
        arguments = query_arguments(scoped)
        self.assertEqual(1, arguments.count("--scope-json"))
        import json
        self.assertEqual(scoped["scope"], json.loads(arguments[arguments.index("--scope-json") + 1]))

    def test_preflight_is_read_only_and_does_not_build_missing_index(self):
        files = [p for p in self.root.rglob("*") if p.is_file()]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        self.assertEqual("ready", self.check(self.case())["status"])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            with self.assertRaises(ValueError):
                preflight_cases({"cases": [self.case()]}, {"repository": root})
            self.assertFalse((root / "artifacts/indexes/knowledge.sqlite3").exists())

    def test_preflight_only_does_not_silently_claim_quality_gate_passed(self):
        with tempfile.TemporaryDirectory() as temporary:
            cases = Path(temporary) / "cases.yaml"
            cases.write_text("cases: []\n")
            with patch("sys.argv", ["run_retrieval.py", "--cases", str(cases), "--preflight-only", "--quality-gate"]), redirect_stderr(io.StringIO()):
                self.assertEqual(2, main())


if __name__ == "__main__":
    unittest.main()
