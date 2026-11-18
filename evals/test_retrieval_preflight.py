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
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from unittest.mock import patch

import yaml

from evals.run_retrieval import main, preflight_cases, query_arguments, run_cases, select_platform_overlay_cases
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

    def test_option_like_queries_round_trip_through_preflight_and_real_cli(self):
        import importlib.util
        from evals.run_retrieval import QUERY

        spec = importlib.util.spec_from_file_location("preflight_query_arguments", QUERY)
        query_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(query_module)
        for text in ("--prefiller-ports", "-k", "--query=other", "不存在的查询"):
            with self.subTest(query=text):
                case = self.case("unknown", query=text)
                case["filters"].update(match="literal", k=5)
                parsed = query_module.build_parser().parse_args(query_arguments(case))
                self.assertEqual(text, parsed.query)
                self.assertEqual(["a3"], parsed.platform)
                self.assertEqual(5, parsed.limit)
                self.assertEqual("ready", self.check(case)["status"])
                case.update(expected=[], expected_count=0)
                from contextlib import redirect_stdout
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, run_cases({"cases": [case]}, {"repository": self.root}))

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


class PlatformOverlayRetrievalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.card = self.root / "knowledge/model/inference/apis/fixture.md"
        self.card.parent.mkdir(parents=True)
        self.binding = {"resource": "https://gitcode.com/Ascend/op-plugin/blob/" + "a" * 40 + "/docs/api.md", "role": "constraint"}
        self.data = {"quality": {"min_recall_at_k": 1}, "cases": [
            {"id": "fixture", "query": "torch_npu.fixture", "filters": {"platform": "950", "k": 5},
             "expected": ["model/inference/apis/fixture"]}]}
        self.evidence = {"overlays": {"torch_npu.fixture": {"additional_platforms": {"950": {
            "source_doc": self.binding["resource"], "source_role": self.binding["role"], "retrieval_case": "fixture"}}}}}

    def write_card(self, sources, **metadata):
        self.card.write_text("---\n" + yaml.safe_dump({"sources": sources, **metadata}) + "---\n" + self.binding["resource"])

    def select(self, data=None, evidence=None):
        return select_platform_overlay_cases(self.data if data is None else data,
                                             self.evidence if evidence is None else evidence,
                                             {"repository": self.root})

    def test_missing_or_unbound_card_skips_without_queries(self):
        for sources in (None, [], [{**self.binding, "role": "primary"}], [{**self.binding, "resource": "https://example.com/other"}]):
            with self.subTest(sources=sources):
                if sources is not None:
                    self.write_card(sources)
                data, report = self.select()
                self.assertEqual([], data["cases"])
                self.assertEqual({"enabled": [], "skipped": ["fixture"], "total": 1}, report)
                with patch("evals.run_retrieval.subprocess.run") as query, redirect_stdout(io.StringIO()):
                    self.assertEqual(0, run_cases(data, {"repository": self.root}))
                    query.assert_not_called()

    def test_binding_enables_even_when_retrieval_metadata_regresses(self):
        self.write_card([self.binding], platforms=[], status="draft")
        original = deepcopy(self.data)
        before = self.card.read_bytes()
        data, report = self.select()
        self.assertEqual(["fixture"], report["enabled"])
        self.assertEqual(original, data)
        self.assertEqual(original, self.data)
        self.assertEqual(before, self.card.read_bytes())
        response = subprocess.CompletedProcess([], 0, json.dumps({"count": 0, "hits": []}), "")
        with patch("evals.run_retrieval.subprocess.run", return_value=response) as query, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(1, run_cases(data, {"repository": self.root}))
            query.assert_called_once()

    def test_partial_activation_preserves_case_order_and_quality(self):
        self.write_card([self.binding])
        other = {**self.data["cases"][0], "id": "other", "query": "torch_npu.other", "expected": ["model/inference/apis/missing"]}
        self.data["cases"] = [other, self.data["cases"][0]]
        self.evidence["overlays"]["torch_npu.other"] = {"additional_platforms": {"950": {
            "source_doc": self.binding["resource"], "source_role": self.binding["role"], "retrieval_case": "other"}}}
        data, report = self.select()
        self.assertEqual(["fixture"], [case["id"] for case in data["cases"]])
        self.assertEqual(["other"], report["skipped"])
        self.assertEqual(self.data["quality"], data["quality"])

    def test_mismatched_or_incomplete_mappings_fail_closed(self):
        for changes in ({"id": "unknown"}, {"query": "wrong"}, {"filters": {"platform": "a3"}}, {"expected": []}, {"corpus": "unknown"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.select({"cases": [{**self.data["cases"][0], **changes}]})
        with self.assertRaisesRegex(ValueError, "unique ids"):
            self.select({"cases": self.data["cases"] * 2})
        with self.assertRaisesRegex(ValueError, "missing retrieval cases"):
            self.select({"cases": []})
        for evidence in (None, {}, {"overlays": {"api": {}}}):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                select_platform_overlay_cases(self.data, evidence, {"repository": self.root})
        self.evidence["overlays"]["torch_npu.fixture"]["additional_platforms"]["950"]["source_role"] = "unknown"
        with self.assertRaisesRegex(ValueError, "source_role"):
            self.select()

    def test_paths_cannot_escape_bundle_including_symlinks(self):
        for path in ("../outside", str(self.root / "outside")):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "inside the knowledge root"):
                self.select({"cases": [{**self.data["cases"][0], "expected": [path]}]})
        self.card.symlink_to(self.root / "outside.md")
        with self.assertRaisesRegex(ValueError, "inside the knowledge root"):
            self.select()

    def test_malformed_card_is_an_error_instead_of_a_skip(self):
        for text in ("no frontmatter", "---\nsources: []\nsources: []\n---\n", "---\nsources: invalid\n---\n"):
            with self.subTest(text=text):
                self.card.write_text(text)
                with self.assertRaises((ValueError, yaml.YAMLError)):
                    self.select()

    def test_cli_executes_selected_cases_and_default_path_stays_unchanged(self):
        schema = Path("governance/schemas/frontmatter.schema.json")
        (self.root / schema).parent.mkdir(parents=True)
        (self.root / schema).write_bytes((Path(__file__).resolve().parents[1] / schema).read_bytes())
        cases, overlays = self.root / "cases.yaml", self.root / "overlays.yaml"
        cases.write_text(yaml.safe_dump(self.data))
        overlays.write_text(yaml.safe_dump(self.evidence))
        for bound in (False, True):
            if bound:
                self.write_card([self.binding])
            output = io.StringIO()
            with patch("sys.argv", ["run_retrieval.py", "--cases", str(cases), "--platform-overlays", str(overlays)]), patch("evals.run_retrieval.ROOT", self.root), patch("evals.run_retrieval.select_platform_overlay_cases", wraps=select_platform_overlay_cases) as selector, patch("evals.run_retrieval.run_cases", return_value=0) as run, redirect_stdout(output):
                self.assertEqual(0, main())
                self.assertEqual(int(bound), len(run.call_args.args[0]["cases"]))
                selector.assert_called_once()
                self.assertIn(f"enabled={int(bound)} skipped={int(not bound)} total=1", output.getvalue())
        with patch("sys.argv", ["run_retrieval.py", "--cases", str(cases)]), patch("evals.run_retrieval.select_platform_overlay_cases") as selector, patch("evals.run_retrieval.run_cases", return_value=0) as run:
            self.assertEqual(0, main())
            selector.assert_not_called()
            self.assertEqual(self.data, run.call_args.args[0])

if __name__ == "__main__":
    unittest.main()
