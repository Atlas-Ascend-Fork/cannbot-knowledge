# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Optional Scope governance, strict acceptance and legacy-consumer compatibility."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from evals.test_retrieval_index import ROOT, QUERY, make_root, run_index
from governance.contracts.knowledge import Contract
from governance.contracts.scope import ScopeRegistry
from governance.contracts.scope_matchers import DIMENSION_MATCHERS, DimensionMatch, object_fields


def scope(**conditions):
    return {"schema": "model.inference.v1", "any_of": [{"all_of": conditions}]}


class ScopeGovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = Contract(ROOT)
        cls.registry = cls.contract.scope_registry

    def state(self, query, card):
        return self.registry.compare(self.registry.normalize(query, query=True), card)["state"]


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


class CapacityFixture:
    """Test-only non-enumerated handler; no production domain is preregistered."""

    def __init__(self, definition, location):
        object_fields(definition, {"kind", "unit"}, location)
        if definition.get("unit") != "fixture_units":
            raise ValueError("fixture unit required")

    def normalize(self, value, *, query, location):
        del query
        value = object_fields(value, {"capacity"}, location)
        capacity = value.get("capacity")
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("positive fixture capacity required")
        return {"capacity": capacity}

    def compare(self, query, card):
        if query is None:
            return DimensionMatch([{"state": "unknown", "reason": "fixture_missing_capacity"}])
        if query["capacity"] < card["capacity"]:
            return DimensionMatch([{"state": "conflict", "reason": "fixture_insufficient_capacity"}])
        return DimensionMatch()


def fixture_scope(**conditions):
    return {"schema": "runtime.fixture.v1", "any_of": [{"all_of": conditions}]}


class ScopeExtensionTests(unittest.TestCase):
    def test_domain_kind_controls_configuration_values_and_matching(self):
        definitions = {"runtime.fixture.v1": {
            "description": "隔离扩展夹具", "domains": ["runtime"],
            "dimensions": {"budget": {"kind": "fixture_capacity", "unit": "fixture_units"}},
        }}
        with patch.dict(DIMENSION_MATCHERS, {"fixture_capacity": CapacityFixture}):
            registry = ScopeRegistry(definitions)
        card = fixture_scope(budget={"capacity": 4})
        for capacity, expected in [(8, "match"), (4, "match"), (2, "conflict")]:
            query = registry.normalize(fixture_scope(budget={"capacity": capacity}), query=True)
            self.assertEqual(expected, registry.compare(query, card)["state"])
        for capacity in [0, -1, True, "4", [4]]:
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                registry.normalize(fixture_scope(budget={"capacity": capacity}), query=True)
        missing = copy.deepcopy(definitions)
        missing["runtime.fixture.v1"]["dimensions"]["mode"] = {"kind": "enum", "values": ["safe"]}
        with patch.dict(DIMENSION_MATCHERS, {"fixture_capacity": CapacityFixture}):
            registry = ScopeRegistry(missing)
            self.assertEqual("unknown", registry.compare(registry.normalize(fixture_scope(mode=["safe"])), card)["state"])
            missing["runtime.fixture.v1"]["dimensions"]["budget"]["unit"] = "unregistered"
            with self.assertRaises(ValueError):
                ScopeRegistry(missing)
        with self.assertRaises(ValueError):
            ScopeRegistry(definitions)

    def test_registry_cannot_load_handlers_from_data(self):
        for kind in ["unregistered", "path.to.callable", "../handler", "__import__", []]:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                ScopeRegistry({"runtime.fixture.v1": {
                    "description": "拒绝未登记处理器", "domains": ["runtime"],
                    "dimensions": {"mode": {"kind": kind}},
                }})

    def test_matcher_must_return_valid_decision_reasons(self):
        for reasons in [None, [{}], [{"state": "match", "reason": "wrong"}],
                        [{"state": "unknown", "reason": ""}]]:
            with self.subTest(reasons=reasons), self.assertRaises(ValueError):
                DimensionMatch(reasons)
        definitions = {"runtime.fixture.v1": {
            "description": "错误返回值夹具", "domains": ["runtime"],
            "dimensions": {"budget": {"kind": "fixture_capacity", "unit": "fixture_units"}},
        }}
        with patch.dict(DIMENSION_MATCHERS, {"fixture_capacity": CapacityFixture}):
            registry = ScopeRegistry(definitions)
        value = registry.normalize(fixture_scope(budget={"capacity": 1}))
        with patch.object(CapacityFixture, "compare", return_value=None), self.assertRaises(ValueError):
            registry.compare(value, value)

    def test_partial_scope_can_exclude_despite_another_unknown_dimension(self):
        registry = Contract(ROOT).scope_registry
        card = {"schema": "model.inference.v1", "any_of": [{"all_of": {"phase": ["prefill"]}}]}
        for phase, expected in [("prefill", "unknown"), ("decode", "conflict")]:
            query = {"schema": "model.inference.v1", "any_of": [{"all_of": {
                "phase": [phase], "execution_mode": ["ge_graph"],
            }}]}
            self.assertEqual(expected, registry.compare(registry.normalize(query, query=True), card)["state"])
        self.assertEqual("unknown", registry.compare(registry.normalize(card, query=True), None)["state"])

    def test_bindings_are_explicit_and_do_not_spread_across_routes(self):
        registry = ScopeRegistry({"runtime.fixture.v1": {
            "description": "显式绑定夹具", "domains": ["runtime"], "routes": ["model/inference"],
            "dimensions": {"mode": {"kind": "enum", "values": ["sync"]}},
        }})
        self.assertTrue(registry.applies_to("runtime.fixture.v1", "runtime", None))
        self.assertTrue(registry.applies_to("runtime.fixture.v1", "model", "inference"))
        self.assertFalse(registry.applies_to("runtime.fixture.v1", "model", "training"))
        self.assertFalse(registry.applies_to("runtime.fixture.v1", "runtime", "inference"))
        for bindings in [{}, {"domains": []}, {"domains": "runtime"}, {"routes": []}]:
            with self.subTest(bindings=bindings), self.assertRaises(ValueError):
                ScopeRegistry({"runtime.fixture.v1": {"description": "非法绑定", "dimensions": {
                    "mode": {"kind": "enum", "values": ["sync"]}}, **bindings}})


class ScopeGovernanceWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        make_root(self.root)
        self.contract = Contract(self.root)
        self.metadata = {
            "type": "Concept", "title": "ScopeGovernanceProbe 场景夹具",
            "description": "独立验证可选适用条件及旧消费流程。",
            "tags": ["task.lookup", "topic.architecture"], "status": "draft",
            "sources": [], "platforms": ["a2"],
            "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
        }
        self.relative = Path("knowledge/model/inference/concepts/probe.md")
        self.body = "# ScopeGovernanceProbe 场景夹具\n\n用于治理回归，不包含设备技术结论。\n"

    def write_card(self, value):
        card = self.root / self.relative
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text("---\n" + yaml.safe_dump(value, allow_unicode=True) + "---\n\n" + self.body)
        return card

    def run_ingest(self, *arguments):
        return subprocess.run([
            sys.executable, str(ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"),
            "--knowledge-root", str(self.root), *arguments,
        ], capture_output=True, text=True)

    def test_optional_partial_scope_and_supported_profiles(self):
        profiles = [
            ("concepts/probe.md", "Concept"), ("guides/probe.md", "Guide"),
            ("optimizations/rules/probe.md", "Optimization"),
            ("runbooks/performance/probe.md", "Runbook"),
        ]
        for tail, kind in profiles:
            relative = Path("knowledge/model/inference") / tail
            for declared in (None, scope(phase=["prefill"])):
                value = {**self.metadata, "type": kind}
                if declared is not None:
                    value["scope"] = declared
                with self.subTest(profile=tail, scope=declared):
                    self.assertEqual([], self.contract.validate_card(relative, value, self.body))

    def test_unsupported_profile_wrong_route_and_unknown_fields_are_rejected(self):
        value = {**self.metadata, "scope": scope(phase=["prefill"])}
        for relative, kind, expected in [
            ("knowledge/model/inference/apis/probe.md", "API", "frontmatter.extra"),
            ("knowledge/model/inference/examples/probe.md", "Example", "frontmatter.extra"),
            ("knowledge/model/training/concepts/probe.md", "Concept", "scope.invalid"),
            ("knowledge/ops/ascendc/concepts/probe.md", "Concept", "scope.invalid"),
        ]:
            issues = self.contract.validate_card(Path(relative), {**value, "type": kind}, self.body)
            self.assertIn(expected, {item.code for item in issues})
        value["unexpected_field"] = True
        self.assertIn("frontmatter.schema", {item.code for item in self.contract.validate_card(self.relative, value, self.body)})

    def test_legacy_experience_paths_remain_valid_until_knowledge_migration(self):
        for section, kind in [("guides/experience/interventions", "Guide"),
                              ("optimizations/experience/rules", "Optimization")]:
            relative = Path("knowledge/model/inference") / section
            self.contract.derive_card_path(relative / "probe.md")
            self.assertEqual([], self.contract.validate_index_path(relative / "index.md"))
            value = {**self.metadata, "type": kind, "scope": scope(phase=["prefill"])}
            self.assertEqual([], self.contract.validate_card(relative / "probe.md", value, self.body))

    def test_direct_domain_schema_is_explicit_and_still_obeys_profile_boundaries(self):
        path = self.root / "governance/schemas/registries.yaml"
        registry = yaml.safe_load(path.read_text())
        registry["scope_schemas"]["runtime.fixture.v1"] = {
            "description": "直接领域夹具", "domains": ["runtime"],
            "dimensions": {"mode": {"kind": "enum", "values": ["sync", "async"]}},
        }
        path.write_text(yaml.safe_dump(registry, allow_unicode=True))
        contract = Contract(self.root)
        value = {**self.metadata, "scope": fixture_scope(mode=["sync"])}
        self.assertEqual([], contract.validate_card(Path("knowledge/runtime/concepts/probe.md"), value, self.body))
        issues = contract.validate_card(self.relative, value, self.body)
        self.assertIn("scope.invalid", {issue.code for issue in issues})
        registry["scope_schemas"]["runtime.fixture.v1"]["domains"] = ["model"]
        path.write_text(yaml.safe_dump(registry, allow_unicode=True))
        with self.assertRaises(ValueError):
            Contract(self.root)

    def test_index_preserves_scope_without_changing_unscoped_query_scores(self):
        value = {**self.metadata, "status": "stable", "sources": [{"resource": "https://example.com/scope-governance"}]}
        self.write_card(value)
        synced = self.run_ingest("sync-indexes")
        self.assertEqual(0, synced.returncode, synced.stdout + synced.stderr)
        def search():
            built = run_index(self.root, "build")
            self.assertEqual(0, built.returncode, built.stdout + built.stderr)
            result = subprocess.run([
                sys.executable, str(QUERY), "search", "--knowledge-root", str(self.root),
                "--query", "ScopeGovernanceProbe", "--platform", "a2", "--domain", "model",
                "--technology", "inference", "--match", "literal", "--json", "--k", "5",
            ], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            hits = json.loads(result.stdout)["hits"]
            self.assertEqual(1, len(hits))
            return [(item["path"], item["rank"], item["score"]) for item in hits]
        before = search()
        value["scope"] = scope(phase=["prefill"])
        card = self.write_card(value)
        declared = card.read_bytes()
        self.assertEqual(before, search())
        with sqlite3.connect(self.root / "artifacts/indexes/knowledge.sqlite3") as connection:
            stored, = connection.execute("SELECT metadata_json FROM documents WHERE relative_path = ?", (str(self.relative),)).fetchone()
        self.assertEqual(value["scope"], json.loads(stored)["scope"])
        built = self.run_ingest("build-graph")
        self.assertEqual(0, built.returncode, built.stdout + built.stderr)
        graph = json.loads((self.root / "artifacts/graphs/graph.json").read_text())
        self.assertIn("model/inference/concepts/probe", {node["id"] for node in graph["nodes"]})
        self.assertEqual(declared, card.read_bytes())

    def test_invalid_scope_is_rejected_by_lint_index_and_graph_without_card_writes(self):
        value = {**self.metadata, "scope": scope(phase=["not_registered"])}
        card = self.write_card(value)
        before = card.read_bytes()
        lint = subprocess.run([
            sys.executable, str(ROOT / ".agents/skills/knowledge-lint/scripts/knowledge_lint.py"),
            "--knowledge-root", str(self.root), "--card", str(self.relative), "--json",
        ], capture_output=True, text=True)
        self.assertEqual(1, lint.returncode, lint.stdout + lint.stderr)
        self.assertIn("scope.invalid", {item["code"] for item in json.loads(lint.stdout)["findings"]})
        for result in (run_index(self.root, "build"), self.run_ingest("build-graph")):
            self.assertNotEqual(0, result.returncode)
            self.assertIn("scope.invalid", result.stdout + result.stderr)
        self.assertEqual(before, card.read_bytes())
        self.assertFalse((self.root / "artifacts/graphs/graph.json").exists())

    def test_external_root_cannot_execute_a_replacement_scope_handler(self):
        marker = self.root / "executed"
        target = self.root / "governance/contracts/scope_matchers.py"
        target.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        result = run_index(self.root, "build")
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("target governance contract does not match", result.stderr)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
