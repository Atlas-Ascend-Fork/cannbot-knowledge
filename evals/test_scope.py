# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Scope decision-table, producer, retrieval and audit compatibility tests."""

from __future__ import annotations

import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import yaml

from evals.test_retrieval_index import ROOT, make_root, run_index
from evals.scope_metrics import summarize, summarize_workflows
from evals.scope_review import equivalence_fingerprint, evaluate_review
from evals.run_retrieval import run_cases
from governance.contracts.knowledge import Contract
from governance.contracts.scope import ScopeRegistry
from governance.contracts.checks.navigation import structural_directories


def scope(**conditions):
    return {"schema": "model.inference.v1", "any_of": [{"all_of": conditions}]}


def load_query():
    path = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
    spec = importlib.util.spec_from_file_location("scope_test_query", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScopeWorkflowMetricsTests(unittest.TestCase):
    def test_human_workflow_metrics_keep_incomplete_tasks_and_real_denominators(self):
        report = summarize_workflows(
            [{"id": "a", "completed": True, "human_applicable": True},
             {"id": "b", "completed": True, "human_applicable": False},
             {"id": "c", "completed": False}],
            [{"id": "new", "human_duplicate": False}],
            [{"id": "stable", "human_source_complete": True, "human_scope_complete": True,
              "human_validation_complete": False, "human_boundary_complete": True}],
        )
        self.assertEqual(0.5, report["decision_accuracy"])
        self.assertEqual(1, report["incomplete_decisions"])
        self.assertEqual(0, report["duplicate_rate"])
        self.assertEqual(0, report["evidence_completeness"])
        empty = summarize_workflows([], [], [])
        self.assertIsNone(empty["decision_accuracy"])
        self.assertIsNone(empty["duplicate_rate"])
        self.assertIsNone(empty["evidence_completeness"])

    def test_missing_review_labels_cannot_be_replaced_by_machine_states(self):
        with self.assertRaises(ValueError):
            summarize_workflows([{"id": "a", "completed": True, "scope_match": "match"}], [], [])
        with self.assertRaises(ValueError):
            summarize_workflows([], [{"id": "new", "human_duplicate": None}], [])
        with self.assertRaises(ValueError):
            summarize_workflows([], [], [{"id": "stable", "lint_passed": True}])


class ScopeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = Contract(ROOT)
        cls.registry = cls.contract.scope_registry

    def state(self, query, card):
        return self.registry.compare(self.registry.normalize(query, query=True), card)["state"]

    def test_model_migration_rejects_retired_sections_only_in_registered_routes(self):
        for section in ["guides/experience/interventions", "optimizations/experience/rules"]:
            with self.subTest(section=section):
                with self.assertRaises(ValueError):
                    self.contract.derive_card_path(Path(f"knowledge/model/inference/{section}/sample.md"))
                self.assertTrue(self.contract.validate_index_path(Path(f"knowledge/model/inference/{section}/index.md")))
        for section in ["guides/integration", "optimizations/rules", "optimizations/cases"]:
            self.contract.derive_card_path(Path(f"knowledge/model/inference/{section}/sample.md"))
            self.assertEqual([], self.contract.validate_index_path(Path(f"knowledge/model/inference/{section}/index.md")))
        self.contract.derive_card_path(Path("knowledge/model/training/guides/experience/sample.md"))
        self.contract.derive_card_path(Path("knowledge/ops/tilelang/guides/experience/sample.md"))

    def test_decision_table(self):
        cases = [
            (scope(phase=["prefill"], execution_mode=["ge_graph"]), scope(phase=["prefill"], execution_mode=["ge_graph"]), "match"),
            (scope(phase=["prefill"], execution_mode=["ge_graph"]), scope(phase=["prefill"]), "unknown"),
            (scope(phase=["prefill"]), scope(phase=["prefill"], execution_mode=["ge_graph"]), "unknown"),
            (scope(phase=["prefill"], execution_mode=["ge_graph"]), scope(phase=["prefill"], execution_mode=["any"]), "match"),
            (scope(phase=["any"]), scope(phase=["prefill"]), "unknown"),
            (scope(phase=["prefill"], execution_mode=["ge_graph"]), scope(phase=["prefill"], execution_mode=["eager"]), "conflict"),
            (scope(phase=["prefill"]), scope(phase=["decode"]), "conflict"),
            (scope(model_features={"all_of": ["moe", "mla"]}), scope(model_features={"all_of": ["moe"]}), "match"),
            (scope(model_features={"all_of": ["moe"]}), scope(model_features={"all_of": ["moe", "mla"]}), "unknown"),
            (scope(model_features={"all_of": ["moe"], "none_of": ["mla"]}), scope(model_features={"all_of": ["moe", "mla"]}), "conflict"),
            (scope(phase=["prefill"]), None, "unknown"),
            (scope(phase=["prefill", "decode"]), scope(phase=["decode"]), "match"),
            (scope(objective=["throughput"]), scope(objective=["latency"]), "conflict"),
            (scope(objective=["tpot"]), scope(objective=["latency"]), "conflict"),
            (scope(objective=["tpot"]), scope(objective=["latency", "tpot"]), "match"),
            (scope(objective=["ttft"]), scope(objective=["latency", "tpot"]), "conflict"),
            (scope(objective=["throughput"]), scope(phase=["decode"]), "unknown"),
            (scope(model_features={"all_of": ["moe", "mla", "dsa"]}), scope(model_features={"all_of": ["moe", "mla"]}), "match"),
            (scope(model_features={"none_of": ["mla"]}), scope(model_features={"all_of": ["moe"]}), "unknown"),
            (scope(phase=["decode"]), scope(phase=["any"]), "match"),
            (scope(phase=["any"]), scope(phase=["any"]), "match"),
            (scope(phase=["prefill"]), scope(phase=["prefill"], objective=["ttft"]), "unknown"),
            (scope(phase=["prefill"], objective=["ttft"]), scope(phase=["decode"]), "conflict"),
            (scope(parallelism={"all_of": ["dp", "ep"]}), scope(parallelism={"all_of": ["ep"]}), "match"),
            (scope(parallelism={"all_of": ["ep"]}), scope(parallelism={"all_of": ["dp", "ep"]}), "unknown"),
            (scope(context_length=["long_context"], batch_size=["small_batch"]), scope(context_length=["long_context"], batch_size=["small_batch"]), "match"),
            (scope(context_length=["long_context"], batch_size=["large_batch"]), scope(context_length=["long_context"], batch_size=["small_batch"]), "conflict"),
            (scope(serving_mode=["online"], deployment_topology={"all_of": ["afd", "pd_disaggregated"]}), scope(serving_mode=["online"], deployment_topology={"all_of": ["afd", "pd_disaggregated"]}), "match"),
            (scope(framework=["vllm"]), scope(framework=["sglang"]), "conflict"),
            (scope(quantization=["w8a8"]), scope(quantization=["w8a8", "bf16"]), "match"),
            (scope(concurrency=["single_request"]), scope(concurrency=["high_concurrency"]), "conflict"),
            (scope(execution_mode=["ge_graph"]), scope(execution_mode=["any"], model_features={"all_of": ["moe"]}), "unknown"),
            (scope(phase=["prefill"]), scope(execution_mode=["any"]), "unknown"),
        ]
        self.assertGreaterEqual(len(cases), 30)
        for query, card, expected in cases:
            with self.subTest(query=query, card=card):
                self.assertEqual(expected, self.state(query, card))

    def test_branches_never_form_cartesian_product(self):
        card = scope(phase=["prefill"], execution_mode=["ge_graph"])
        card["any_of"] += scope(phase=["decode"], execution_mode=["eager"])["any_of"]
        for phase, mode, expected in [
            ("prefill", "ge_graph", "match"), ("decode", "eager", "match"),
            ("prefill", "eager", "conflict"), ("decode", "ge_graph", "conflict"),
        ]:
            self.assertEqual(expected, self.state(scope(phase=[phase], execution_mode=[mode]), card))
        result = self.registry.compare(self.registry.normalize(scope(phase=["decode"], execution_mode=["eager"]), query=True), card)
        self.assertEqual([1], [p["card_profile"] for p in result["profiles"] if p["state"] == "match"])

    def test_branch_unknown_is_preserved_when_other_branch_conflicts(self):
        card = scope(phase=["prefill"], execution_mode=["ge_graph"])
        card["any_of"] += scope(phase=["decode"])["any_of"]
        self.assertEqual("unknown", self.state(scope(phase=["prefill"]), card))

    def test_query_alternatives_and_matched_intersection_are_reported(self):
        query = scope(phase=["prefill", "decode"])
        query["any_of"] += scope(execution_mode=["eager"])["any_of"]
        result = self.registry.compare(self.registry.normalize(query, query=True), scope(phase=["prefill"]))
        self.assertEqual("match", result["state"])
        self.assertEqual(["prefill"], result["profiles"][0]["matched_values"]["phase"])

    def test_invalid_scope_is_rejected(self):
        invalid = [None, [], {}, {"schema": "missing.v1", "any_of": []},
                   {"schema": "model.inference.v1", "any_of": []},
                   scope(), scope(phase=[]), scope(phase=["prefill", "prefill"]),
                   scope(phase=["prefill", "any"]), scope(phase=["unknown"]),
                   scope(load=["long_context"]), scope(deployment=["online"]),
                   scope(model_features={"all_of": ["any"]}),
                   scope(model_features={"all_of": ["moe"], "none_of": ["moe"]}),
                   scope(deployment_topology={"none_of": ["afd"]}),
                   {**scope(phase=["prefill"]), "confirmed": True}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.registry.normalize(value, query=True)

    def test_aliases_are_only_normalized_for_explicit_queries(self):
        value = scope(phase=["预填充"], execution_mode=["GE"])
        self.assertEqual(scope(execution_mode=["ge_graph"], phase=["prefill"]), self.registry.normalize(value, query=True))
        with self.assertRaises(ValueError):
            self.registry.normalize(value)
        with self.assertRaises(ValueError):
            self.registry.normalize(scope(phase=["Prefill", "prefill"]), query=True)

    def test_duplicate_keys_and_equivalent_branches_fail(self):
        with self.assertRaises(yaml.YAMLError):
            self.contract.parse_scope("schema: model.inference.v1\nschema: model.inference.v1\nany_of: []")
        value = scope(model_features={"all_of": ["moe", "mla"]})
        value["any_of"] += scope(model_features={"all_of": ["mla", "moe"]})["any_of"]
        with self.assertRaises(ValueError):
            self.registry.normalize(value)

    def test_only_query_supports_feature_none_of(self):
        value = scope(model_features={"none_of": ["mla"]})
        self.assertEqual(value, self.registry.normalize(value, query=True))
        with self.assertRaises(ValueError):
            self.registry.normalize(value)

    def test_parallelism_absence_requires_explicit_evidence(self):
        cases = [
            ({"none_of": ["cp"]}, {"none_of": ["cp"]}, "match"),
            ({"none_of": ["cp", "ep"]}, {"none_of": ["cp"]}, "match"),
            ({"none_of": ["cp", "ep"]}, {"none_of": ["cp", "ep"]}, "match"),
            ({"none_of": ["cp"]}, {"none_of": ["cp", "ep"]}, "unknown"),
            ({"all_of": ["cp"]}, {"none_of": ["cp", "ep"]}, "conflict"),
            ({"all_of": ["cp"]}, {"none_of": ["cp"]}, "conflict"),
            ({"none_of": ["cp"]}, {"all_of": ["cp"]}, "conflict"),
            ({"all_of": ["tp"]}, {"none_of": ["cp"]}, "unknown"),
            ({"none_of": ["ep"]}, {"none_of": ["cp"]}, "unknown"),
            ({"all_of": ["tp"], "none_of": ["cp"]}, {"none_of": ["cp"]}, "match"),
            ({"all_of": ["tp"], "none_of": ["cp"]}, {"all_of": ["tp"], "none_of": ["cp"]}, "match"),
            ({"all_of": ["tp"]}, {"all_of": ["tp"], "none_of": ["cp"]}, "unknown"),
            ({"none_of": ["cp"]}, {"all_of": ["tp"], "none_of": ["cp"]}, "unknown"),
            ({"all_of": ["cp"]}, {"all_of": ["tp"], "none_of": ["cp"]}, "conflict"),
            ({"none_of": ["tp"]}, {"all_of": ["tp"], "none_of": ["cp"]}, "conflict"),
            ({"all_of": ["tp"], "none_of": ["cp"]}, {"all_of": ["tp"]}, "match"),
        ]
        for query, card, expected in cases:
            with self.subTest(query=query, card=card):
                self.assertEqual(expected, self.state(scope(parallelism=query), scope(parallelism=card)))
        card = scope(phase=["prefill"], parallelism={"none_of": ["cp"]})
        self.assertEqual("unknown", self.state(scope(phase=["prefill"]), card))
        result = self.registry.compare(
            self.registry.normalize(scope(phase=["prefill"], parallelism={"all_of": ["tp"]}), query=True), card)
        self.assertEqual("missing_query_absences", result["profiles"][0]["reasons"][0]["reason"])
        self.assertEqual(["cp"], result["profiles"][0]["reasons"][0]["features"])

    def test_parallelism_negative_branches_are_not_merged(self):
        card = scope(phase=["prefill"], parallelism={"none_of": ["cp"]})
        card["any_of"] += scope(phase=["decode"], parallelism={"all_of": ["cp"]})["any_of"]
        for phase, condition, expected in [
            ("prefill", {"none_of": ["cp"]}, "match"),
            ("decode", {"all_of": ["cp"]}, "match"),
            ("prefill", {"all_of": ["cp"]}, "conflict"),
            ("decode", {"none_of": ["cp"]}, "conflict"),
            ("prefill", {"all_of": ["tp"]}, "unknown"),
        ]:
            with self.subTest(phase=phase, condition=condition):
                self.assertEqual(expected, self.state(scope(phase=[phase], parallelism=condition), card))

    def test_parallelism_negation_is_registered_and_validated_for_cards_and_queries(self):
        value = scope(parallelism={"none_of": ["ep", "cp"], "all_of": ["tp", "dp"]})
        canonical = scope(parallelism={"all_of": ["dp", "tp"], "none_of": ["cp", "ep"]})
        for query in (False, True):
            self.assertEqual(canonical, self.registry.normalize(value, query=query))
            for condition in [{}, {"none_of": []}, {"none_of": "cp"},
                              {"none_of": ["any"]}, {"none_of": ["unknown"]},
                              {"none_of": ["cp", "cp"]},
                              {"all_of": [], "none_of": ["cp"]},
                              {"all_of": ["cp"], "none_of": ["cp"]}]:
                with self.subTest(query=query, condition=condition), self.assertRaises(ValueError):
                    self.registry.normalize(scope(parallelism=condition), query=query)
            with self.assertRaises(ValueError):
                self.registry.normalize(scope(deployment_topology={"none_of": ["afd"]}), query=query)
        self.assertEqual(scope(parallelism={"none_of": ["cp"]}),
                         self.registry.normalize(scope(parallelism={"none_of": ["CP"]}), query=True))
        with self.assertRaises(ValueError):
            self.registry.normalize(scope(parallelism={"none_of": ["CP"]}))
        with self.assertRaises(ValueError):
            self.registry.normalize(scope(parallelism={"none_of": ["cp", "CP"]}), query=True)
        for permission in ("query_none_of", "card_none_of"):
            for name, invalid in [("phase", True), ("parallelism", "true")]:
                definitions = copy.deepcopy(self.registry.definitions)
                definitions["model.inference.v1"]["dimensions"][name][permission] = invalid
                with self.subTest(permission=permission, name=name), self.assertRaises(ValueError):
                    ScopeRegistry(definitions)

    def test_other_registered_schema_is_unknown(self):
        definitions = copy.deepcopy(self.registry.definitions)
        definitions["ops.compat.v1"] = {"description": "夹具", "routes": ["ops/ascendc"], "dimensions": {"mode": {"kind": "enum", "values": ["direct"]}}}
        registry = ScopeRegistry(definitions)
        result = registry.compare(scope(phase=["prefill"]), {"schema": "ops.compat.v1", "any_of": [{"all_of": {"mode": ["direct"]}}]})
        self.assertEqual("schema_mismatch", result["reason"])
        self.assertEqual("unknown", result["state"])

    def test_registry_rejects_ambiguous_alias_and_unregistered_route(self):
        definitions = copy.deepcopy(self.registry.definitions)
        definitions["model.inference.v1"]["dimensions"]["phase"]["aliases"]["PREFILL"] = "decode"
        with self.assertRaises(ValueError):
            ScopeRegistry(definitions)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            path = root / "governance/schemas/registries.yaml"
            data = yaml.safe_load(path.read_text())
            data["scope_schemas"]["model.inference.v1"]["routes"] = ["ops/inference"]
            path.write_text(yaml.safe_dump(data, allow_unicode=True))
            with self.assertRaises(ValueError):
                Contract(root)


class ScopeRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        make_root(cls.root)
        cls.query = load_query()
        cls.cards_dir = cls.root / "knowledge/model/inference/optimizations"
        cls.cards_dir.mkdir(parents=True)
        definitions = {
            "a_unknown": None,
            "b_prefill": scope(phase=["prefill"], execution_mode=["ge_graph"]),
            "c_decode": scope(phase=["decode"], execution_mode=["eager"]),
            "d_any_mode": scope(phase=["prefill"], execution_mode=["any"]),
            "e_moe": scope(phase=["prefill"], execution_mode=["ge_graph"], model_features={"all_of": ["moe"]}),
            "f_moe_mla": scope(phase=["prefill"], execution_mode=["ge_graph"], model_features={"all_of": ["moe", "mla"]}),
            "z_unknown_title": None,
        }
        for slug, declaration in definitions.items():
            cls.write_card(slug, declaration)
        built = run_index(cls.root, "build")
        if built.returncode:
            raise AssertionError(built.stderr)
        cls.connection, cls.metadata = cls.query.open_index(cls.root)
        cls.cards = cls.query.load_cards(cls.connection)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.temporary.cleanup()

    @classmethod
    def write_card(cls, slug, declaration):
        metadata = {
            "type": "Optimization", "title": "ScopeFixture" if slug == "z_unknown_title" else "范围匹配夹具",
            "description": "用于验证场景匹配和错误边界。", "tags": ["task.optimization", "topic.graph_execution"],
            "status": "stable", "sources": [{"resource": "https://example.com/scope"}],
            "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z", "platforms": ["a3"],
        }
        if declaration is not None:
            metadata["scope"] = declaration
        (cls.cards_dir / f"{slug}.md").write_text("---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n\n# 范围匹配夹具\n\nScopeFixture\n")

    def search(self, declaration=None, *, limit=10):
        args = self.query.build_parser().parse_args(["search", "--query", "ScopeFixture", "--platform", "a3", "--match", "literal", "-k", str(limit)])
        args.scope = declaration
        return self.query.search_payload(self.root, self.cards, self.metadata, self.connection, args, include_current_repository=False)

    def test_scope_is_opt_in_and_no_scope_request_shape_is_unchanged(self):
        payload = self.search()
        self.assertEqual(7, payload["count"])
        self.assertNotIn("scope_filter", payload)
        self.assertNotIn("scope", payload["request"])
        self.assertTrue(all("scope_match" not in hit for hit in payload["results"]))

    def test_filtering_precedes_top_k_and_retains_unknown(self):
        payload = self.search(scope(phase=["prefill"], execution_mode=["ge_graph"]), limit=6)
        self.assertEqual(6, payload["count"])
        self.assertEqual(1, payload["scope_filter"]["excluded_count"])
        self.assertFalse(any(hit["path"].endswith("/c_decode") for hit in payload["results"]))
        hits = {hit["path"].split("/")[-1]: hit for hit in payload["results"]}
        self.assertEqual("unknown", hits["a_unknown"]["scope_match"]["state"])
        self.assertEqual("match", hits["b_prefill"]["scope_match"]["state"])

    def test_relevance_beats_scope_completeness_but_ties_prefer_match(self):
        hits = self.search(scope(phase=["prefill"], execution_mode=["ge_graph"]))["results"]
        self.assertTrue(hits[0]["path"].endswith("/z_unknown_title"))
        self.assertEqual("unknown", hits[0]["scope_match"]["state"])
        paths = [hit["path"].split("/")[-1] for hit in hits]
        self.assertLess(paths.index("b_prefill"), paths.index("a_unknown"))

    def test_negative_query_is_auditable_and_excludes_required_feature(self):
        payload = self.search(scope(phase=["prefill"], execution_mode=["ge_graph"], model_features={"all_of": ["moe"], "none_of": ["mla"]}))
        self.assertTrue(any(item["path"].endswith("/f_moe_mla") for item in payload["scope_filter"]["excluded"]))
        self.assertTrue(any(hit["path"].endswith("/e_moe") for hit in payload["results"]))
        args = self.query.search_args_from_request(payload["request"])
        replay = self.query.search_payload(self.root, self.cards, self.metadata, self.connection, args, include_current_repository=False)
        self.assertEqual(payload, replay)
        request = json.loads(json.dumps(payload["request"]))
        request["filters"]["scope"] = scope(phase=["decode"])
        with self.assertRaises(ValueError):
            self.query.search_args_from_request(request)

    def test_existing_platform_domain_profile_filters_are_not_relaxed(self):
        for flags in (["--platform", "a2"], ["--domain", "ops"], ["--type", "apis"], ["--status", "draft"]):
            args = self.query.build_parser().parse_args(["search", "--query", "ScopeFixture", "--platform", "a3", *flags])
            args.scope = scope(phase=["prefill"])
            payload = self.query.search_payload(self.root, self.cards, self.metadata, self.connection, args, include_current_repository=False)
            self.assertEqual(0, payload["count"])

    def test_cli_rejects_invalid_and_duplicate_scope(self):
        for raw in ('{"schema":"not.registered.v1","any_of":[]}', 'schema: model.inference.v1\nschema: model.inference.v1\nany_of: []'):
            result = subprocess.run([sys.executable, str(ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"), "--knowledge-root", str(self.root), "search", "--query", "ScopeFixture", "--platform", "a3", "--scope-json", raw], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertEqual(json.loads(result.stdout), json.loads(result.stderr))

    def test_card_scope_rejects_wrong_route_and_query_only_negation(self):
        contract = Contract(ROOT)
        metadata = yaml.safe_load((self.cards_dir / "e_moe.md").read_text().split("---", 2)[1])
        issues = contract.validate_card(Path("knowledge/ops/ascendc/optimizations/example.md"), metadata, "# Example\n\nBody.")
        self.assertIn("scope.invalid", {issue.code for issue in issues})
        metadata["scope"] = scope(model_features={"all_of": ["moe"], "none_of": ["mla"]})
        issues = contract.validate_card(Path("knowledge/model/inference/optimizations/example.md"), metadata, "# Example\n\nBody.")
        self.assertIn("scope.invalid", {issue.code for issue in issues})
        metadata["scope"] = scope(parallelism={"none_of": ["cp"]})
        self.assertEqual([], contract.validate_card(
            Path("knowledge/model/inference/optimizations/example.md"), metadata, "# Example\n\nBody."))

    def test_ingest_dry_run_accepts_card_scope_but_rejects_query_negation(self):
        script = ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            body = root / "body.md"
            body.write_text("# 示例\n\nScopeFixture\n")
            declaration = root / "scope.yaml"
            command = [sys.executable, str(script), "--knowledge-root", str(root), "create", "--path", "knowledge/model/inference/optimizations/new.md", "--title", "示例", "--description", "示例范围", "--tag", "task.optimization", "--tag", "topic.graph_execution", "--platform", "a3", "--body-file", str(body), "--scope-file", str(declaration), "--dry-run"]
            declaration.write_text(yaml.safe_dump(scope(phase=["decode"])))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("scope:", result.stdout)
            self.assertFalse((root / "knowledge/model/inference/optimizations/new.md").exists())
            declaration.write_text(yaml.safe_dump(scope(phase=["prefill"], parallelism={"none_of": ["cp"]})))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("none_of:", result.stdout)
            self.assertFalse((root / "knowledge/model/inference/optimizations/new.md").exists())
            declaration.write_text(yaml.safe_dump(scope(model_features={"none_of": ["mla"]})))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertFalse((root / "knowledge/model/inference/optimizations/new.md").exists())


class ScopeParallelismRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        make_root(cls.root)
        directory = cls.root / "knowledge/model/inference/optimizations"
        directory.mkdir(parents=True)
        cls.declarations = {
            "a_no_cp": scope(phase=["prefill"], parallelism={"none_of": ["cp"]}),
            "b_cp": scope(phase=["prefill"], parallelism={"all_of": ["cp"]}),
            "c_phase_only": scope(phase=["prefill"]),
            "d_legacy": None,
            "e_tp_no_cp": scope(phase=["prefill"], parallelism={"all_of": ["tp"], "none_of": ["cp"]}),
        }
        for slug, declaration in cls.declarations.items():
            metadata = {
                "type": "Optimization", "title": "ParallelScopeFixture", "description": "并行条件的隔离检索夹具。",
                "tags": ["task.optimization", "topic.parallelism"], "status": "stable",
                "platforms": ["a3"], "sources": [{"resource": "https://example.com/parallel-scope"}],
                "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
            }
            if declaration is not None:
                metadata["scope"] = declaration
            (directory / (slug + ".md")).write_text(
                "---\n" + yaml.safe_dump(metadata, allow_unicode=True) + "---\n\n# 并行条件夹具\n\nParallelScopeFixture\n")
        built = run_index(cls.root, "build")
        if built.returncode:
            raise AssertionError(built.stderr)
        cls.query = load_query()
        cls.connection, cls.metadata = cls.query.open_index(cls.root)
        cls.cards = cls.query.load_cards(cls.connection)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.temporary.cleanup()

    def search(self, declaration=None, *, limit=10):
        args = self.query.build_parser().parse_args([
            "search", "--query", "ParallelScopeFixture", "--platform", "a3", "--match", "literal", "-k", str(limit)])
        args.scope = declaration
        return self.query.search_payload(self.root, self.cards, self.metadata, self.connection, args,
                                         include_current_repository=False)

    def test_explicit_cp_excludes_negative_cards_before_limit_with_audit(self):
        payload = self.search(scope(phase=["prefill"], parallelism={"all_of": ["cp"]}), limit=3)
        self.assertEqual(["b_cp", "c_phase_only", "d_legacy"],
                         [h["path"].split("/")[-1] for h in payload["results"]])
        self.assertEqual(["match", "unknown", "unknown"],
                         [h["scope_match"]["state"] for h in payload["results"]])
        exclusions = payload["scope_filter"]["excluded"]
        self.assertEqual({"a_no_cp", "e_tp_no_cp"}, {h["path"].split("/")[-1] for h in exclusions})
        for hit in exclusions:
            reasons = hit["scope_match"]["profiles"][0]["reasons"]
            self.assertTrue(any(r["reason"] == "present_forbidden_features" and r["features"] == ["cp"]
                                for r in reasons))

    def test_negative_query_matches_absence_but_keeps_missing_conditions_unknown(self):
        payload = self.search(scope(phase=["prefill"], parallelism={"none_of": ["cp"]}))
        states = {h["path"].split("/")[-1]: h["scope_match"]["state"] for h in payload["results"]}
        self.assertEqual({"a_no_cp": "match", "c_phase_only": "unknown", "d_legacy": "unknown",
                          "e_tp_no_cp": "unknown"}, states)
        self.assertEqual(1, payload["scope_filter"]["excluded_count"])
        replay_args = self.query.search_args_from_request(payload["request"])
        self.assertEqual(payload, self.query.search_payload(
            self.root, self.cards, self.metadata, self.connection, replay_args, include_current_repository=False))
        self.assertEqual(scope(parallelism={"none_of": ["cp"]}, phase=["prefill"]), payload["request"]["scope"])

    def test_positive_tp_does_not_imply_cp_is_disabled_or_change_legacy_scores(self):
        legacy = self.search()
        explicit = self.search(scope(phase=["prefill"], parallelism={"all_of": ["tp"]}))
        self.assertEqual(5, explicit["count"])
        self.assertTrue(all(h["scope_match"]["state"] == "unknown" for h in explicit["results"]))
        self.assertEqual([(h["path"], h["score"]) for h in legacy["results"]],
                         [(h["path"], h["score"]) for h in explicit["results"]])
        self.assertNotIn("scope", legacy["request"])
        self.assertNotIn("scope_filter", legacy)
        self.assertTrue(all("scope_match" not in h for h in legacy["results"]))

    def test_cli_rejects_contradictory_parallelism_without_silently_broadening(self):
        invalid = scope(parallelism={"all_of": ["cp"], "none_of": ["cp"]})
        result = subprocess.run([
            sys.executable, str(ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"),
            "--knowledge-root", str(self.root), "search", "--query", "ParallelScopeFixture", "--platform", "a3",
            "--scope-json", json.dumps(invalid)], capture_output=True, text=True)
        self.assertEqual(2, result.returncode)
        self.assertEqual(json.loads(result.stdout), json.loads(result.stderr))


class ScopeHarnessTests(unittest.TestCase):
    def run_case(self, payload, **extra):
        case = {"id": "scope_harness", "query": "example", "scope": scope(phase=["decode"]), **extra}
        completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
        with patch("evals.run_retrieval.subprocess.run", return_value=completed) as run, \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status = run_cases({"cases": [case]}, {"repository": ROOT})
        return status, run.call_args.args[0]

    def test_structured_scope_is_forwarded_and_states_are_asserted(self):
        payload = {"count": 1, "hits": [{"path": "a", "rank": 1, "scope_match": {"state": "unknown"}}],
                   "scope_filter": {"enabled": True, "excluded": []}}
        status, command = self.run_case(payload, expected=["a"], expected_scope_states={"a": "unknown"})
        self.assertEqual(0, status)
        self.assertEqual(scope(phase=["decode"]), json.loads(command[command.index("--scope-json") + 1]))
        status, _ = self.run_case(payload, expected_scope_states={"a": "match"})
        self.assertEqual(1, status)

    def test_conflicts_must_be_excluded_and_audited(self):
        payload = {"count": 0, "hits": [], "scope_filter": {
            "enabled": True, "excluded": [{"path": "a", "scope_match": {"state": "conflict"}}]}}
        self.assertEqual(0, self.run_case(payload, expected_scope_excluded=["a"])[0])
        payload["scope_filter"]["excluded"] = []
        self.assertEqual(1, self.run_case(payload, expected_scope_excluded=["a"])[0])
        payload["hits"] = [{"path": "a", "rank": 1, "scope_match": {"state": "conflict"}}]
        payload["count"] = 1
        self.assertEqual(1, self.run_case(payload)[0])

    def test_missing_filter_or_malformed_state_cannot_pass(self):
        payload = {"count": 0, "hits": []}
        self.assertEqual(1, self.run_case(payload)[0])
        payload = {"count": 1, "hits": [{"path": "a", "rank": 1, "scope_match": []}],
                   "scope_filter": {"enabled": True, "excluded": []}}
        self.assertEqual(1, self.run_case(payload)[0])
        payload["hits"][0]["scope_match"] = {"state": []}
        self.assertEqual(1, self.run_case(payload)[0])

    def test_scope_contract_failure_is_not_an_aggregate_recall_miss(self):
        completed = subprocess.CompletedProcess([], 0, json.dumps({
            "count": 1, "hits": [{"path": "a", "rank": 1, "scope_match": {"state": "unknown"}}],
            "scope_filter": {"enabled": True, "excluded": []}}), "")
        data = {"quality": {"min_recall_at_k": 0.1, "min_mrr": 0.1}, "cases": [{
            "id": "scope_harness", "query": "example", "scope": scope(phase=["decode"]),
            "expected": ["a"], "expected_scope_states": {"a": "match"}}]}
        with patch("evals.run_retrieval.subprocess.run", return_value=completed), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(1, run_cases(data, {"repository": ROOT}, quality_gate=True))

    def test_scope_assertions_require_scope_and_reject_duplicate_inputs(self):
        for extra in [{"expected_scope_states": {"a": "conflict"}},
                      {"scope": None}, {"filters": {"scope_json": "{}"}}]:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.run_case({"count": 0, "hits": []}, **extra)
        with self.assertRaises(ValueError):
            run_cases({"cases": [{"id": "invalid", "query": "example", "expected_scope_states": {"a": "match"}}]}, {"repository": ROOT})


class ScopeDslCompatibilityTests(unittest.TestCase):
    """Positive DSL coverage lives in isolated fixtures, not production facts."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        make_root(cls.root)
        base = {
            "type": "Concept", "title": "DSL 兼容夹具", "description": "隔离检索与跨技术端点夹具。",
            "tags": ["task.implementation", "topic.compilation"], "status": "stable",
            "sources": [{"resource": "https://example.com/dsl-compatibility-fixture"}],
            "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
            "platforms": ["a3"],
        }
        paths = {f"ops/{dsl}/concepts/local": {} for dsl in ["ascendc", "tilelang", "pypto"]}
        paths.update({
            "ops/shared/concepts/generic": {},
            "graph/shared/concepts/other_domain": {},
            "ops/shared/interoperability/pair": {
                "type": "Interoperability", "source_technology": "tilelang", "target_technology": "pypto"},
            "ops/shared/interoperability/unrelated": {
                "type": "Interoperability", "source_technology": "ascendc", "target_technology": "triton"},
        })
        for concept_id, extra in paths.items():
            path = cls.root / "knowledge" / f"{concept_id}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\n" + yaml.safe_dump({**base, **extra}, allow_unicode=True)
                            + "---\n\n# DSL 兼容夹具\n\nDSLCompatibility\n")
        built = run_index(cls.root, "build")
        if built.returncode:
            raise AssertionError(built.stderr)
        cls.query = load_query()
        cls.connection, cls.metadata = cls.query.open_index(cls.root)
        cls.cards = cls.query.load_cards(cls.connection)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.temporary.cleanup()

    def search(self, dsl, *, shared=False, declaration=None):
        flags = ["--include-shared"] if shared else []
        args = self.query.build_parser().parse_args([
            "search", "--query", "DSLCompatibility", "--match", "literal", "--domain", "ops",
            "--technology", dsl, "--platform", "a3", "-k", "10", *flags])
        args.scope = declaration
        return self.query.search_payload(self.root, self.cards, self.metadata, self.connection, args,
                                         include_current_repository=False)

    def test_positive_dsl_results_preserve_default_route_and_score_with_model_scope(self):
        for dsl in ["ascendc", "tilelang", "pypto"]:
            with self.subTest(dsl=dsl):
                original = self.search(dsl)
                explicit = self.search(dsl, declaration=scope(phase=["prefill"]))
                self.assertEqual([f"ops/{dsl}/concepts/local"], [hit["path"] for hit in original["results"]])
                self.assertNotIn("scope_filter", original)
                self.assertEqual([(hit["path"], hit["score"]) for hit in original["results"]],
                                 [(hit["path"], hit["score"]) for hit in explicit["results"]])
                self.assertEqual("unknown", explicit["results"][0]["scope_match"]["state"])
                self.assertEqual(0, explicit["scope_filter"]["excluded_count"])

    def test_shared_expansion_preserves_domain_and_interoperability_endpoints(self):
        for dsl in ["tilelang", "pypto"]:
            with self.subTest(dsl=dsl):
                hits = self.search(dsl, shared=True, declaration=scope(phase=["decode"]))["results"]
                self.assertEqual({f"ops/{dsl}/concepts/local", "ops/shared/concepts/generic",
                                  "ops/shared/interoperability/pair"}, {hit["path"] for hit in hits})
                self.assertTrue(all(hit["scope_match"]["state"] == "unknown" for hit in hits))

    def test_model_scope_cannot_be_attached_to_dsl_cards(self):
        contract = Contract(self.root)
        for dsl in ["ascendc", "tilelang", "pypto"]:
            relative = Path(f"knowledge/ops/{dsl}/concepts/local.md")
            metadata = yaml.safe_load((self.root / relative).read_text().split("---", 2)[1])
            self.assertEqual([], contract.validate_card(relative, metadata, "# 夹具\n\n隔离测试。\n"))
            metadata["scope"] = scope(phase=["decode"])
            issues = contract.validate_card(relative, metadata, "# 夹具\n\n隔离测试。\n")
            self.assertIn("scope.invalid", {issue.code for issue in issues})


class ScopeOperatorIngestCompatibilityTests(unittest.TestCase):
    def test_existing_operator_can_be_written_linted_indexed_and_retrieved(self):
        """Re-ingest real governed material in a fresh root; production is read-only."""
        relative = Path("knowledge/ops/ascendc/operators/aclnn/cv/image/im2col_backward_950.md")
        original = (ROOT / relative).read_bytes()
        metadata, body = original.decode().split("---", 2)[1:]
        metadata = yaml.safe_load(metadata)
        ingest = ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
        lint = ROOT / ".agents/skills/knowledge-lint/scripts/knowledge_lint.py"
        with tempfile.TemporaryDirectory(prefix="rfc47_operator_ingest_") as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            shutil.copy2(ROOT / "get_resources.sh", root / "get_resources.sh")
            contract = Contract(root)
            directories = structural_directories(contract) | {Path("knowledge")}
            parent = relative.parent
            while parent != Path("."):
                directories.add(parent)
                parent = parent.parent
            for directory in directories:
                if directory == Path("."):
                    continue
                target = root / directory
                target.mkdir(parents=True, exist_ok=True)
                prefix = '---\nokf_version: "0.2"\n---\n\n' if directory == Path("knowledge") else ""
                (target / "index.md").write_text(prefix + "# 兼容验证目录\n")
            body_file = root / "candidate_body.md"
            body_file.write_text(body)
            command = [sys.executable, str(ingest), "--knowledge-root", str(root), "create",
                       "--path", relative.as_posix(), "--title", metadata["title"],
                       "--description", metadata["description"], "--status", metadata["status"],
                       "--body-file", str(body_file)]
            for flag, values in [("tag", metadata["tags"]), ("platform", metadata["platforms"]),
                                 ("cann-version", metadata.get("cann_versions", [])),
                                 ("source", [item["resource"] for item in metadata["sources"]])]:
                for value in values:
                    command.extend(["--" + flag, value])
            dry = subprocess.run(command + ["--dry-run"], capture_output=True, text=True)
            self.assertEqual(0, dry.returncode, dry.stderr)
            self.assertFalse((root / relative).exists())
            created = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, created.returncode, created.stderr)
            written = (root / relative).read_bytes()
            produced, produced_body = written.decode().split("---", 2)[1:]
            produced = yaml.safe_load(produced)
            self.assertEqual("Operator", produced["type"])
            self.assertNotIn("scope", produced)
            self.assertEqual(body.strip(), produced_body.strip())
            self.assertEqual(metadata["platforms"], produced["platforms"])
            self.assertEqual([item["resource"] for item in metadata["sources"]],
                             [item["resource"] for item in produced["sources"]])
            duplicate = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, duplicate.returncode)
            self.assertEqual(written, (root / relative).read_bytes())
            nav = subprocess.run([sys.executable, str(ingest), "--knowledge-root", str(root),
                                  "sync-indexes"], capture_output=True, text=True)
            self.assertEqual(0, nav.returncode, nav.stderr)
            day, clock = subprocess.check_output(["date", "+%Y-%m-%d %H:%M"], text=True).strip().split()
            (root / "logs").mkdir()
            (root / "logs" / f"{day}.md").write_text(
                f"# {day}\n\n## [{clock}] ingest | 隔离 Operator 摄入兼容验证\n\n"
                "### Summary\n\n摄入既有 Operator 材料，验证 Profile 与无 Scope 路径。\n\n"
                "### Details\n\n- 正文和来源资源保持一致；没有执行上游源码或硬件测试。\n")
            checked = subprocess.run([sys.executable, str(lint), "--knowledge-root", str(root),
                                      "--strict-navigation", "--json"], capture_output=True, text=True)
            self.assertEqual(0, checked.returncode, checked.stderr + checked.stdout)
            self.assertEqual([], json.loads(checked.stdout)["findings"])
            built = run_index(root, "build")
            self.assertEqual(0, built.returncode, built.stderr)
            verified = run_index(root, "verify", "--level", "full")
            self.assertEqual(0, verified.returncode, verified.stderr)
            query = load_query()
            connection, index = query.open_index(root)
            try:
                cards = query.load_cards(connection)
                for platform, expected in [("950", 1), ("a3", 0)]:
                    args = query.build_parser().parse_args([
                        "search", "--query", metadata["title"], "--match", "literal", "--domain", "ops",
                        "--technology", "ascendc", "--type", "operators", "--platform", platform])
                    result = query.search_payload(root, cards, index, connection, args,
                                                  include_current_repository=False)
                    self.assertEqual(expected, result["count"])
                    self.assertNotIn("scope_filter", result)
                    if expected:
                        self.assertEqual("Operator", result["results"][0]["type"])
                        self.assertEqual("ops/ascendc/operators/aclnn/cv/image/im2col_backward_950",
                                         result["results"][0]["path"])
            finally:
                connection.close()
        self.assertEqual(original, (ROOT / relative).read_bytes())


class ScopeMetricTests(unittest.TestCase):
    def test_precision_conflict_unknown_use_actual_micro_denominator(self):
        cases = [
            {"confirmed_scope": True, "expected": ["a", "b"], "results": [
                {"path": "a", "human_judgment": "match"},
                {"path": "b", "human_judgment": "match"},
                {"path": "c", "human_judgment": "conflict"},
                {"path": "d", "human_judgment": "unknown"},
                {"path": "e", "human_judgment": "unknown"}]},
            {"confirmed_scope": True, "expected": ["f"], "results": [
                {"path": "f", "human_judgment": "match"}]},
            {"confirmed_scope": False, "expected": ["g"], "results": [{"path": "g"}]},
        ]
        result = summarize(cases)
        self.assertEqual(0.5, result["scope_precision_at_5"])
        self.assertEqual(1 / 6, result["conflict_rate_at_5"])
        self.assertEqual(2 / 6, result["unknown_rate_at_5"])
        self.assertEqual(1.0, result["recall_at_5"])
        self.assertEqual([5, 1, 1], result["returned_counts"])

    def test_empty_results_are_not_perfect_precision(self):
        result = summarize([{"confirmed_scope": True, "expected": ["a"], "results": []}])
        self.assertIsNone(result["scope_precision_at_5"])
        self.assertEqual(0.0, result["recall_at_5"])
        self.assertEqual(0.0, result["nonempty_recall_rate"])
        self.assertEqual([0], result["returned_counts"])

    def test_query_self_report_does_not_replace_review(self):
        with self.assertRaises(ValueError):
            summarize([{"confirmed_scope": True, "expected": ["a"], "results": [
                {"path": "a", "scope_match": {"state": "match"}}]}])

    def test_macro_recall_does_not_mean_at_least_one_hit(self):
        result = summarize([
            {"confirmed_scope": False, "expected": ["a", "b"], "results": [{"path": "a"}]},
            {"confirmed_scope": False, "expected": ["c"], "results": []},
        ])
        self.assertEqual(0.25, result["recall_at_5"])
        self.assertEqual(0.5, result["nonempty_recall_rate"])

    def test_duplicate_results_cannot_inflate_precision(self):
        with self.assertRaises(ValueError):
            summarize([{"confirmed_scope": True, "expected": ["a"], "results": [
                {"path": "a", "human_judgment": "match"}, {"path": "a", "human_judgment": "match"}]}])


class ScopeReviewTests(unittest.TestCase):
    def setUp(self):
        self.hashes = {"A": "a" * 64, "B": "b" * 64}
        self.captures = {}
        self.review = {"schema_version": "rfc47.human-evaluation.v1", "human_review_complete": True,
                       "reviewer": "Fixture reviewer", "capture_sha256": self.hashes.copy(), "variants": {},
                       "cases_input_sha256": "f" * 64,
                       "equivalence_sha256": equivalence_fingerprint({"old": "new"})}
        for variant, path, label in [("A", "old", "unknown"), ("B", "new", "match")]:
            request = {"query": "fixture", "filters": {"platforms": ["a3"]}}
            if variant == "B":
                request["scope"] = scope(phase=["prefill"])
                request["filters"]["scope"] = request["scope"]
            self.captures[variant] = {"variant": variant, "cases_input_sha256": "f" * 64, "cases": [
                {"id": "case", "request": request, "results": [{"path": path, "rank": 1}]}]}
            self.review["variants"][variant] = [{"id": "case", "confirmed_scope": True, "expected": [path],
                                                  "excluded": [], "answer_points": ["fixture"],
                                                  "results": [{"path": path, "human_judgment": label}]}]

    def evaluate(self):
        return evaluate_review(self.review, self.captures, self.hashes, {"old": "new"})

    def test_complete_bound_review_scores_with_frozen_migration_equivalence(self):
        report = self.evaluate()
        self.assertEqual("reviewed", report["status"])
        self.assertTrue(report["retrieval_criteria_passed"])
        self.assertFalse(report["acceptance_complete"])
        self.assertEqual(1, report["metrics"]["A"]["recall_at_5"])
        self.assertEqual(1, report["metrics"]["B"]["scope_precision_at_5"])
        self.assertEqual(1, report["metrics"]["A"]["unknown_rate_at_5"])

    def test_pending_review_produces_no_metrics(self):
        self.review["human_review_complete"] = False
        self.review["variants"]["B"][0]["results"][0]["human_judgment"] = None
        result = self.evaluate()
        self.assertEqual("awaiting_human_review", result["status"])
        self.assertEqual(1, result["pending_fields"])
        self.assertIsNone(result["metrics"])
        self.review["human_review_complete"] = True
        with self.assertRaisesRegex(ValueError, "pending"):
            self.evaluate()

    def test_changed_capture_bytes_or_result_order_are_rejected(self):
        self.review["capture_sha256"]["B"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "capture bytes"):
            self.evaluate()
        self.review["capture_sha256"] = self.hashes.copy()
        self.review["variants"]["B"][0]["results"][0]["path"] = "substituted"
        with self.assertRaisesRegex(ValueError, "paths or order"):
            self.evaluate()

    def test_missing_or_duplicate_cases_cannot_shrink_denominators(self):
        self.review["variants"]["B"] = []
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.evaluate()
        self.setUp()
        self.captures["A"]["cases"] *= 2
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            self.evaluate()

    def test_different_queries_gold_or_scope_confirmation_are_rejected(self):
        for change in ["query", "expected", "confirmed_scope", "input_hash"]:
            with self.subTest(change=change):
                self.setUp()
                if change == "query":
                    self.captures["B"]["cases"][0]["request"]["query"] = "easier"
                elif change == "input_hash":
                    self.captures["B"]["cases_input_sha256"] = "c" * 64
                else:
                    self.review["variants"]["B"][0][change] = ["different"] if change == "expected" else False
                with self.assertRaises(ValueError):
                    self.evaluate()

    def test_zero_return_and_nonimprovement_do_not_pass(self):
        self.review["variants"]["A"][0]["results"][0]["human_judgment"] = "match"
        self.assertFalse(self.evaluate()["retrieval_criteria_passed"])
        for variant in ["A", "B"]:
            self.captures[variant]["cases"][0]["results"] = []
            self.review["variants"][variant][0]["results"] = []
        report = self.evaluate()
        self.assertFalse(report["retrieval_criteria_passed"])
        self.assertIsNone(report["metrics"]["B"]["scope_precision_at_5"])

    def test_machine_scope_state_cannot_replace_human_judgment(self):
        item = self.review["variants"]["B"][0]["results"][0]
        item.pop("human_judgment")
        item["scope_match"] = {"state": "match"}
        with self.assertRaisesRegex(ValueError, "pending"):
            self.evaluate()

    def test_changed_equivalence_cannot_improve_recall(self):
        with self.assertRaisesRegex(ValueError, "equivalence has changed"):
            evaluate_review(self.review, self.captures, self.hashes, {"old": "unrelated"})


if __name__ == "__main__":
    unittest.main()
