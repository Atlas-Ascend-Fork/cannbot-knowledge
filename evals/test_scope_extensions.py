# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Optional partial Scope and trusted domain-handler extension boundaries."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from evals.test_retrieval_index import ROOT, make_root, run_index
from governance.contracts.knowledge import Contract
from governance.contracts.scope import ScopeRegistry
from governance.contracts.scope_matchers import DIMENSION_MATCHERS, DimensionMatch, object_fields


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
            "description": "仅供测试：验证领域容量条件的校验与匹配。", "domains": ["runtime"],
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
            "description": "仅供测试：验证匹配处理器的非法返回值会被拒绝。", "domains": ["runtime"],
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
            "description": "仅供测试：验证 Schema 只适用于明确登记的领域和路由。",
            "domains": ["runtime"], "routes": ["model/inference"],
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


class DirectDomainScopeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        make_root(self.root)
        self.path = self.root / "governance/schemas/registries.yaml"
        self.data = yaml.safe_load(self.path.read_text())
        self.data["scope_schemas"]["runtime.fixture.v1"] = {
            "description": "仅供测试：验证直接领域的 Scope 注册与检索。", "domains": ["runtime"],
            "dimensions": {"mode": {"kind": "enum", "values": ["sync", "async"]}},
        }
        self.save_registry()

    def save_registry(self):
        self.path.write_text(yaml.safe_dump(self.data, allow_unicode=True))

    def test_domain_registration_rejects_unknown_or_non_direct_domains(self):
        for domain in ["missing", "model", "ops"]:
            self.data["scope_schemas"]["runtime.fixture.v1"]["domains"] = [domain]
            self.save_registry()
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                Contract(self.root)

    def test_direct_scope_does_not_bypass_route_or_profile_boundaries(self):
        contract = Contract(self.root)
        metadata = {
            "type": "Concept", "title": "路径边界测试卡", "description": "验证 Scope 不会绕过路由或 Profile 限制。",
            "tags": ["task.lookup", "topic.graph_execution"], "status": "stable", "platforms": ["a3"],
            "sources": [{"resource": "https://example.com/direct-scope-fixture"}],
            "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
            "scope": fixture_scope(mode=["sync"]),
        }
        self.assertEqual([], contract.validate_card(Path("knowledge/runtime/concepts/fixture.md"), metadata, "# 路径边界测试卡\n"))
        issues = contract.validate_card(Path("knowledge/model/inference/concepts/fixture.md"), metadata, "# 路径边界测试卡\n")
        self.assertIn("scope.invalid", {i.code for i in issues})
        metadata["type"] = "API"
        issues = contract.validate_card(Path("knowledge/runtime/apis/fixture.md"), metadata, "# 路径边界测试卡\n")
        self.assertTrue(any("scope" in i.message for i in issues))

    def test_external_root_cannot_supply_executable_handler_code(self):
        handler = self.root / "governance/contracts/scope_matchers.py"
        handler.write_text(handler.read_text() + "\nraise RuntimeError('external-handler-was-executed')\n")
        result = run_index(self.root, "build")
        self.assertEqual(2, result.returncode)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("external-handler-was-executed", result.stderr)

    def test_direct_domain_scope_runs_through_index_and_query(self):
        directory = self.root / "knowledge/runtime/concepts"
        directory.mkdir(parents=True)
        for slug, mode in [("sync", "sync"), ("async", "async"), ("unknown", None)]:
            metadata = {
                "type": "Concept", "title": "DirectScopeFixture", "description": "验证直接领域查询排除冲突卡、保留未知卡。",
                "tags": ["task.lookup", "topic.graph_execution"], "status": "stable", "platforms": ["a3"],
                "sources": [{"resource": "https://example.com/direct-scope-fixture"}],
                "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
            }
            if mode is not None:
                metadata["scope"] = fixture_scope(mode=[mode])
            (directory / f"{slug}.md").write_text("---\n" + yaml.safe_dump(metadata) + "---\n\n# DirectScopeFixture\n")
        built = run_index(self.root, "build")
        self.assertEqual(0, built.returncode, built.stderr)
        command = [sys.executable, str(ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"),
                   "--knowledge-root", str(self.root), "search", "--query", "DirectScopeFixture",
                   "--domain", "runtime", "--platform", "a3", "--match", "literal"]
        plain = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(0, plain.returncode, plain.stderr)
        self.assertEqual(3, json.loads(plain.stdout)["count"])
        result = subprocess.run(command + ["--scope-json", json.dumps(fixture_scope(mode=["sync"]))],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual({"runtime/concepts/sync", "runtime/concepts/unknown"}, {h["path"] for h in payload["results"]})
        self.assertEqual(1, payload["scope_filter"]["excluded_count"])
        self.assertEqual(["match", "unknown"], [h["scope_match"]["state"] for h in payload["results"]])
        bad = subprocess.run(command + ["--scope-json", json.dumps(fixture_scope(phase=["prefill"]))],
                             capture_output=True, text=True)
        self.assertEqual(2, bad.returncode)


if __name__ == "__main__":
    unittest.main()
