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

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from governance.contracts.knowledge import (  # noqa: E402
    Contract,
    markdown_targets,
    relative_markdown_links,
)
from governance.contracts.checks.platforms import (  # noqa: E402
    fixed_archive_platforms,
)
from governance.contracts.checks import Document, RunContext, body  # noqa: E402
from governance.contracts.indexes import summarize_subdir  # noqa: E402


INGEST = ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
INDEX = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
LINT = ROOT / ".agents/skills/knowledge-lint/scripts/knowledge_lint.py"
PINNED_SOURCE = (
    "https://gitcode.com/cann/asc-devkit/blob/"
    "c846650eec121f41bd0efa472fc5c84594b8208d/README.md"
)
SYNTHETIC_API_METADATA = {
    "type": "API",
    "title": "Synthetic API",
    "description": "Contract-only API fixture.",
    "tags": ["task.lookup", "topic.compilation"],
    "status": "stable",
    "sources": [{"resource": "https://example.com/cann/synthetic-api"}],
    "created_at": "2026-08-18T00:00:00Z",
    "updated_at": "2026-08-18T00:00:00Z",
    "platforms": ["a2"],
}


def load_lint_module():
    spec = importlib.util.spec_from_file_location("knowledge_lint_test", LINT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LINT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RouteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = Contract(ROOT)

    def test_planned_routes_are_accepted(self) -> None:
        cases = {
            "knowledge/common/platforms/concepts/architecture.md": ("common", "platforms"),
            "knowledge/common/toolchains/runbooks/compilation/environment.md": ("common", "toolchains"),
            "knowledge/contrib/ascendc/apis/example.md": ("contrib", "ascendc"),
            "knowledge/graph/torch_compile/concepts/capture.md": ("graph", "torch_compile"),
            "knowledge/graph/ge/apis/graph_api.md": ("graph", "ge"),
            "knowledge/ops/ascendc/apis/basic_api/data_copy/example.md": ("ops", "ascendc"),
            "knowledge/ops/ascendc/guides/programming_guide/example.md": ("ops", "ascendc"),
            "knowledge/ops/ascendc/operators/aclnn/nn/activation/gelu.md": ("ops", "ascendc"),
            "knowledge/ops/ascendc/operators/direct/transformer/gmm/grouped_matmul.md": ("ops", "ascendc"),
            "knowledge/model/inference/concepts/serving.md": ("model", "inference"),
            "knowledge/model/training/runbooks/runtime/oom.md": ("model", "training"),
            "knowledge/model/spatial/concepts/vggt.md": ("model", "spatial"),
            "knowledge/model/embodied/concepts/pi0.md": ("model", "embodied"),
            "knowledge/ops/triton/runbooks/compilation/missing_symbol.md": (
                "ops",
                "triton",
            ),
            "knowledge/runtime/apis/rt_api.md": ("runtime", None),
            "knowledge/runtime/runbooks/runtime/device_reset.md": ("runtime", None),
        }
        for value, expected in cases.items():
            with self.subTest(path=value):
                info = self.contract.derive_card_path(Path(value))
                self.assertEqual((info.domain, info.route), expected)
                self.assertFalse(info.doc_id.startswith("knowledge/"))

    def test_profiles_define_okf_types(self) -> None:
        expected = {
            "concepts": "Concept",
            "apis": "API",
            "examples": "Example",
            "guides": "Guide",
            "operators": "Operator",
            "optimizations": "Optimization",
            "runbooks": "Runbook",
            "interoperability": "Interoperability",
            "glossaries": "Glossary",
        }
        self.assertEqual(expected, {name: self.contract.okf_type(name) for name in expected})

    def test_platform_registry_uses_950_as_the_only_a5_generation_id(self) -> None:
        self.assertIn("950", self.contract.platforms)
        self.assertNotIn("a5", self.contract.platforms)

    def test_fixed_archive_mirror_declares_index_only_navigation_and_body_omission(self) -> None:
        mirror = self.contract.local_sources["cann_docs_raw"]["mirror"]
        self.assertEqual("index_only", mirror["navigation_policy"])
        self.assertEqual(
            ["产品支持情况"], mirror["omit_section_title_contains"]
        )

    def test_archive_source_roles_distinguish_mirrors_from_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            resource = "cann-docs-raw/asc-devkit/docs/zh/example.md"
            source_path = root / resource
            source_path.parent.mkdir(parents=True)
            source_path.write_text("# Source without platform scope\n", encoding="utf-8")
            contract = Contract(root)
            for kind, profile in (("API", "apis"), ("Guide", "guides")):
                for role in (None, "primary", "supporting", "example", "constraint",
                             "header", "implementation", "evidence"):
                    with self.subTest(kind=kind, role=role):
                        source = {"resource": resource}
                        if role is not None:
                            source["role"] = role
                        metadata = {
                            **SYNTHETIC_API_METADATA,
                            "type": kind,
                            "sources": [
                                {"resource": "https://example.com/core", "role": "primary"},
                                source,
                            ],
                        }
                        relative = Path(f"knowledge/ops/ascendc/{profile}/synthetic.md")
                        is_mirror = role in (None, "primary")
                        self.assertEqual(
                            is_mirror, contract.fixed_archive_mirror(metadata) is not None
                        )
                        issues = contract.validate_card(relative, metadata, "# Topic\n\nBody.\n")
                        self.assertEqual(
                            {"platform.source_unknown"} if is_mirror else set(),
                            {issue.code for issue in issues},
                        )
                        document = Document.create(
                            contract, root / relative, relative, "", metadata,
                            "# Topic\n\n# Second\n",
                        )
                        issues = body.check(contract, document, RunContext())
                        self.assertEqual(
                            set() if is_mirror else {"body.h1_count"},
                            {issue.code for issue in issues},
                        )

    def test_invalid_fixed_archive_navigation_policy_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            registry = root / "governance/schemas/registries.yaml"
            payload = yaml.safe_load(registry.read_text(encoding="utf-8"))
            payload["local_sources"]["cann_docs_raw"]["mirror"][
                "navigation_policy"
            ] = "mirror_every_markdown"
            registry.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "must be index_only"):
                Contract(root)

    def test_invalid_fixed_archive_omitted_sections_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            registry = root / "governance/schemas/registries.yaml"
            payload = yaml.safe_load(registry.read_text(encoding="utf-8"))
            payload["local_sources"]["cann_docs_raw"]["mirror"][
                "omit_section_title_contains"
            ] = ["产品支持情况", "产品支持情况"]
            registry.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "sorted list of unique"):
                Contract(root)

    def test_fixed_archive_platforms_only_include_supported_product_rows(self) -> None:
        body = """# API

## 产品支持情况

- Ascend 950PR/Ascend 950DT：支持
- Atlas A3 训练系列产品/Atlas A3 推理系列产品：支持
- Atlas A2 训练系列产品/Atlas A2 推理系列产品：不支持
- Atlas 200I/500 A2 推理产品：不支持
- Atlas 推理系列产品AI Core：支持，但实际功能不生效
- Atlas 训练系列产品：支持

## 功能说明
"""
        self.assertEqual(["950", "a3", "910"], fixed_archive_platforms(body))

    def test_fixed_archive_platforms_support_explicit_scope_without_guessing(self) -> None:
        self.assertEqual(
            ["a3"],
            fixed_archive_platforms(
                "# API\n\n## 约束说明\n\n目前仅支持Atlas A3训练系列产品。\n"
            ),
        )
        self.assertEqual(
            ["a2"],
            fixed_archive_platforms(
                "# Guide\n\n本性能优化手段仅针对Atlas A2训练系列产品生效。\n"
            ),
        )
        self.assertIsNone(
            fixed_archive_platforms(
                "# API\n\n以下示例在Atlas A3训练系列产品上运行。\n"
            )
        )
        self.assertIsNone(
            fixed_archive_platforms(
                "# Guide\n\nAscend 950之前仅支持SIMD；从Ascend 950开始支持SIMT。\n"
            )
        )
        self.assertIsNone(
            fixed_archive_platforms(
                "# Guide\n\n### SIMT\n- **限制**：当前仅支持Ascend 950芯片架构。\n"
            )
        )
        self.assertIsNone(
            fixed_archive_platforms(
                "# Guide\n\n针对Atlas A2推理产品，硬件支持两种模式。"
                "Ascend C场景下仅支持耦合模式。\n"
            )
        )
        self.assertIsNone(
            fixed_archive_platforms(
                "# API\n\n范围未知。\n\n"
                "- [Other](other.md)\n"
            )
        )
        self.assertIsNone(
            fixed_archive_platforms(
                "# API\n\n```markdown\n## 产品支持情况\n"
                "- Atlas A2 训练系列产品：支持\n```\n"
            )
        )

    def test_invalid_route_shapes_are_rejected(self) -> None:
        cases = (
            "knowledge/ops/apis/no_dsl.md",
            "knowledge/graph/ascendc/apis/wrong_domain.md",
            "knowledge/ops/ascendc/glossaries/unplanned/nested.md",
            "knowledge/ops/ascendc/operators/internal/nn/activation/unregistered_mode.md",
            "knowledge/ops/ascendc/operators/aclnn/nn/activations/unregistered_category.md",
            "knowledge/ops/ascendc/operators/aclnn/runtime/activation/unregistered_family.md",
            "knowledge/ops/ascendc/operators/aclnn/cv/mc2/family_category_mismatch.md",
            "knowledge/ops/ascendc/interoperability/not_shared.md",
            "knowledge/common/platforms/chip.md",
            "knowledge/contrib/apis/no_route.md",
            "knowledge/contrib/triton/apis/unregistered_route.md",
            "knowledge/model/shared/concepts/cross_scope.md",
            "knowledge/ops/ascendc/runbooks/timeout.md",
        )
        for value in cases:
            with self.subTest(path=value), self.assertRaises(ValueError):
                self.contract.derive_card_path(Path(value))

    def test_current_index_tree_is_complete(self) -> None:
        self.assertEqual(self.contract.validate_index_tree(), [])

    def test_registered_structure_is_materialized(self) -> None:
        expected = {
            "knowledge/common",
            "knowledge/contrib",
            "knowledge/graph",
            "knowledge/model",
            "knowledge/model/inference",
            "knowledge/model/training",
            "knowledge/model/spatial",
            "knowledge/model/embodied",
            "knowledge/ops",
            "knowledge/ops/tilelang",
            "knowledge/ops/pypto",
            "knowledge/ops/triton",
            "knowledge/ops/catlass",
            "knowledge/ops/catlass-dsl",
            "knowledge/runtime",
        }
        actual = {path.as_posix() for path in self.contract.structural_directories()}
        self.assertEqual(expected | {"knowledge/ops/ascendc", "knowledge/ops/shared"}, actual)
        self.assertTrue(all((ROOT / path / "index.md").is_file() for path in expected))
        not_precreated = {
            "knowledge/common/toolchains",
            "knowledge/common/observability",
            "knowledge/common/glossaries",
            "knowledge/graph/ge",
            "knowledge/graph/torch_compile",
            "knowledge/graph/shared",
            "knowledge/runtime/concepts",
            "knowledge/runtime/apis",
            "knowledge/runtime/runbooks",
        }
        self.assertTrue(not_precreated.isdisjoint(actual))
        for path in not_precreated:
            directory = ROOT / path
            if directory.exists():
                self.assertTrue(any(card.name != "index.md" for card in directory.rglob("*.md")), path)

    def test_repository_contains_ascendc_reference_corpus(self) -> None:
        cards = [
            path.relative_to(ROOT)
            for path in (ROOT / "knowledge").rglob("*.md")
            if path.name != "index.md"
        ]
        ascendc_cards = [
            path for path in cards if path.parts[1:3] == ("ops", "ascendc")
        ]
        apis = [path for path in ascendc_cards if "apis" in path.parts]
        guides = [path for path in ascendc_cards if "guides" in path.parts]
        self.assertGreaterEqual(len(apis), 2600)
        self.assertGreaterEqual(len(guides), 270)
        self.assertTrue(
            all(path.parts[1:3] == ("ops", "ascendc") for path in [*apis, *guides])
        )
        self.assertNotIn(
            Path("knowledge/common/platforms/concepts/ascend_910b3_atlas_a2.md"),
            cards,
        )
        # common/platforms 已由首批真实平台知识创建，只允许注册 Profile 子目录。
        platforms = ROOT / "knowledge/common/platforms"
        self.assertTrue((platforms / "concepts").is_dir())
        self.assertEqual(
            {path.name for path in platforms.iterdir() if path.is_dir()},
            {"concepts"},
        )

    def test_ascend910b3_runbooks_are_not_scoped_to_a3(self) -> None:
        conflicts: list[str] = []
        runbooks = ROOT / "knowledge/ops/ascendc/runbooks"
        for card in sorted(runbooks.glob("*/*.md")):
            if card.name == "index.md":
                continue
            text = card.read_text(encoding="utf-8")
            metadata = yaml.safe_load(text.split("---", 2)[1])
            if "Ascend910B3" in text and "a3" in metadata.get("platforms", []):
                conflicts.append(card.relative_to(ROOT).as_posix())
        self.assertEqual([], conflicts)

    def test_precreated_route_policy_is_declared_by_domain(self) -> None:
        enabled = {
            domain
            for domain, definition in self.contract.domains.items()
            if definition.get("precreate_routes", False)
        }
        self.assertEqual(enabled, {"ops", "model"})

    def test_bundle_root_declares_okf_version(self) -> None:
        self.assertEqual(
            [],
            self.contract.validate_index_frontmatter(
                Path("knowledge/index.md"),
                {"okf_version": "0.2"},
            ),
        )
        issues = self.contract.validate_index_frontmatter(Path("knowledge/index.md"), None)
        self.assertEqual(["index.frontmatter"], [issue.code for issue in issues])

    def test_card_type_must_match_path_profile(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["type"] = "Concept"
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("frontmatter.type", {issue.code for issue in issues})

    def test_profile_is_the_only_top_level_required_source(self) -> None:
        self.assertNotIn("required", self.contract.schema)
        self.assertEqual(
            {
                "type",
                "title",
                "description",
                "tags",
                "status",
                "sources",
                "created_at",
                "updated_at",
            },
            self.contract.common_fields,
        )
        self.assertEqual(
            ["resource"],
            self.contract.schema["properties"]["sources"]["items"]["required"],
        )

    def test_missing_required_fields_are_not_reported_twice(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for field in SYNTHETIC_API_METADATA:
            with self.subTest(field=field):
                metadata = dict(SYNTHETIC_API_METADATA)
                metadata.pop(field)
                issues = self.contract.validate_card(
                    relative,
                    metadata,
                    "# Synthetic API\n",
                )
                self.assertEqual(
                    ["frontmatter.required"],
                    [issue.code for issue in issues],
                )

    def test_blank_text_and_wrong_type_have_distinct_findings(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for field in ("title", "description"):
            for value in ("", "   "):
                with self.subTest(field=field, value=value):
                    metadata = dict(SYNTHETIC_API_METADATA)
                    metadata[field] = value
                    issues = self.contract.validate_card(
                        relative,
                        metadata,
                        "# Synthetic API\n",
                    )
                    self.assertEqual(
                        ["frontmatter.text"],
                        [issue.code for issue in issues],
                    )

        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["title"] = 7
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertEqual(["frontmatter.schema"], [issue.code for issue in issues])

    def test_missing_interoperability_endpoint_only_reports_required(self) -> None:
        relative = Path("knowledge/ops/shared/interoperability/synthetic.md")
        metadata = {
            **SYNTHETIC_API_METADATA,
            "type": "Interoperability",
            "source_technology": "ascendc",
            "target_technology": "triton",
        }
        for field in ("source_technology", "target_technology"):
            with self.subTest(field=field):
                candidate = dict(metadata)
                candidate.pop(field)
                issues = self.contract.validate_card(
                    relative,
                    candidate,
                    "# Synthetic interoperability\n",
                )
                self.assertEqual(
                    ["frontmatter.required"],
                    [issue.code for issue in issues],
                )

        invalid = dict(metadata)
        invalid["source_technology"] = []
        issues = self.contract.validate_card(
            relative,
            invalid,
            "# Synthetic interoperability\n",
        )
        self.assertEqual(["frontmatter.schema"], [issue.code for issue in issues])

    def test_missing_status_defers_dependent_checks(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = {
            **SYNTHETIC_API_METADATA,
            "sources": [],
            "platforms": [],
            "replaced_by": "ops/ascendc/apis/replacement",
        }
        metadata.pop("status")
        issues = self.contract.validate_card(
            relative,
            metadata,
            "# Synthetic API\n",
        )
        self.assertEqual(
            ["frontmatter.required"],
            [issue.code for issue in issues],
        )

    def test_missing_replacement_is_always_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = {
            **SYNTHETIC_API_METADATA,
            "status": "deprecated",
            "replaced_by": "ops/ascendc/apis/definitely_missing",
        }
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertTrue(
            any(
                issue.message.startswith("replacement card does not exist:")
                for issue in issues
            )
        )

    def test_replacement_requires_a_canonical_bundle_concept(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(ROOT / "governance", root / "governance")
            directory = root / "knowledge/ops/ascendc/apis"
            directory.mkdir(parents=True)
            for name in ("replacement.md", "index.md", "synthetic_api.md"):
                (directory / name).write_text("# Fixture\n", encoding="utf-8")
            outside = Path(temporary) / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (directory / "escape.md").symlink_to(outside)
            (directory / "index_alias.md").symlink_to(directory / "index.md")
            invalid = root / "knowledge/ops/unregistered/apis/replacement.md"
            invalid.parent.mkdir(parents=True)
            invalid.write_text("# Invalid route\n", encoding="utf-8")
            contract = Contract(root)
            cases = {
                "ops/ascendc/apis/replacement": True,
                "ops/ascendc/apis/index": False,
                "ops/ascendc/apis/index_alias": False,
                "ops/ascendc/apis/escape": False,
                "ops/ascendc/apis/synthetic_api": False,
                "ops/unregistered/apis/replacement": False,
                "ops/ascendc/apis/./replacement": False,
                "ops/ascendc/apis//replacement": False,
            }
            for replacement, accepted in cases.items():
                with self.subTest(replacement=replacement):
                    issues = contract.validate_card(
                        Path("knowledge/ops/ascendc/apis/synthetic_api.md"),
                        {**SYNTHETIC_API_METADATA, "status": "deprecated",
                         "replaced_by": replacement},
                        "# Synthetic API\n",
                    )
                    errors = [issue for issue in issues if issue.code == "status.replaced_by"]
                    self.assertEqual(accepted, not errors, errors)

    def test_hierarchical_tag_and_local_source_are_accepted(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/basic_api/data_copy/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["tags"] = ["task.lookup", "topic.implementation.api_layer.basic_api"]
        metadata["sources"] = [
            {
                "resource": "cann-docs-raw/any/fixed-archive/path.md",
                "role": "primary",
            }
        ]
        self.assertEqual([], self.contract.validate_card(relative, metadata, "# Synthetic API\n"))

    def test_api_source_headers_are_accepted(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["source_headers"] = [
            "include/c_api/asc_simd.h",
            "include/c_api/reg_compute/compute/reg_arith.h",
        ]
        self.assertEqual([], self.contract.validate_card(relative, metadata, "# Synthetic API\n"))

    def test_api_source_headers_reject_invalid_shape(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for value in ([123], "not-a-list", [""], ["include/a.h", "include/a.h"]):
            with self.subTest(value=value):
                metadata = dict(SYNTHETIC_API_METADATA)
                metadata["source_headers"] = value
                issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
                self.assertIn("frontmatter.schema", {issue.code for issue in issues})

    def test_source_headers_is_rejected_outside_api_profile(self) -> None:
        relative = Path("knowledge/ops/ascendc/guides/synthetic_guide.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["type"] = "Guide"
        metadata["source_headers"] = ["include/c_api/asc_simd.h"]
        issues = self.contract.validate_card(relative, metadata, "# Synthetic Guide\n")
        self.assertIn("frontmatter.extra", {issue.code for issue in issues})

    def test_stable_runbook_can_use_empty_sources(self) -> None:
        relative = Path("knowledge/ops/ascendc/runbooks/compilation/trajectory_finding.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata.update(
            {
                "type": "Runbook",
                "title": "Trajectory finding",
                "status": "stable",
                "sources": [],
            }
        )
        self.assertEqual([], self.contract.validate_card(relative, metadata, "# Trajectory finding\n"))

    def test_cann_versions_is_rejected_for_runbook_profile(self) -> None:
        relative = Path("knowledge/ops/ascendc/runbooks/compilation/trajectory_finding.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata.update(
            {
                "type": "Runbook",
                "title": "Trajectory finding",
                "status": "stable",
                "sources": [],
                "cann_versions": ["9.1.0"],
            }
        )
        issues = self.contract.validate_card(relative, metadata, "# Trajectory finding\n")
        self.assertIn("frontmatter.extra", {issue.code for issue in issues})

    def test_cann_versions_remains_allowed_for_non_runbook_profiles(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["cann_versions"] = ["9.1.0"]
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertNotIn("frontmatter.extra", {issue.code for issue in issues})

    def test_stable_non_runbook_still_requires_source(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["sources"] = []
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("source.required", {issue.code for issue in issues})

    def test_unregistered_local_source_is_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["sources"] = [
            {"resource": "unregistered-source/definitely/missing/source.md", "role": "primary"}
        ]
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("source.resource", {issue.code for issue in issues})

    def test_unsafe_local_sources_are_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for resource in (
            "../outside.md",
            "/tmp/outside.md",
            "cann-docs-raw\\outside.md",
            "cann-docs-raw",
            "cann-docs-raw//outside.md",
            "https:///missing-host.md",
            "https://user:secret@example.com/source.md",
        ):
            with self.subTest(resource=resource):
                metadata = dict(SYNTHETIC_API_METADATA)
                metadata["sources"] = [{"resource": resource}]
                issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
                self.assertIn("source.resource", {issue.code for issue in issues})

    def test_unknown_hierarchical_tag_is_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["tags"] = ["task.lookup", "topic.implementation.not_registered"]
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("tag.unknown", {issue.code for issue in issues})

    def test_bundle_absolute_markdown_link_resolves_from_bundle_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.md"
            path.write_text("[API](/ops/ascendc/apis/synthetic_api.md)\n", encoding="utf-8")
            links = relative_markdown_links(path, ROOT / "knowledge")
        self.assertEqual(
            [("/ops/ascendc/apis/synthetic_api.md", ROOT / "knowledge/ops/ascendc/apis/synthetic_api.md")],
            links,
        )

    def test_markdown_targets_ignore_inline_and_fenced_code(self) -> None:
        text = """[real](target.md), [operator\\[\\]](operator.md), and `[interval, end)`.

```cpp
auto fn = [](int value) { return value; };
[fake](inside_fence.md)
```

1. Nested list example:

    ```cpp
    auto path = [capture](inside_indented_fence.md);
    ```
"""
        self.assertEqual(
            [("target.md", False), ("operator.md", False)],
            markdown_targets(text),
        )

    def test_missing_index_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            (root / "knowledge/ops").mkdir(parents=True)
            (root / "knowledge/index.md").write_text("# Knowledge\n", encoding="utf-8")
            issues = Contract(root).validate_index_tree()
            self.assertIn("index.missing", {issue.code for _, issue in issues})


    def test_kirin_platforms_are_registered_without_allowing_unknown_values(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for platform in ("kirin_x90", "kirin_9030", "kirin_unknown"):
            metadata = dict(SYNTHETIC_API_METADATA, platforms=[platform])
            issues = self.contract.validate_card(relative, metadata, "# API\n")
            self.assertEqual(platform == "kirin_unknown", "platform.unknown" in {issue.code for issue in issues})


    def test_mirror_body_exception_requires_primary_archive_api_or_guide(self) -> None:
        from governance.contracts.checks import Document, RunContext, body

        resource = "cann-docs-raw/asc-devkit/docs/zh/example.md"
        for kind, profile in (("API", "apis"), ("Guide", "guides"), ("Concept", "concepts")):
            for role in (None, "primary", "supporting", "header", "implementation"):
                source = {"resource": resource}
                if role is not None:
                    source["role"] = role
                metadata = dict(SYNTHETIC_API_METADATA, type=kind, sources=[source])
                relative = Path(f"knowledge/ops/ascendc/{profile}/synthetic.md")
                allowed = kind in {"API", "Guide"} and role in (None, "primary")
                for text in ("# First\n\n# Second\n", "No heading.\n"):
                    with self.subTest(kind=kind, role=role, text=text):
                        document = Document.create(self.contract, ROOT / relative, relative, "", metadata, text)
                        issues = body.check(self.contract, document, RunContext())
                        self.assertEqual(not allowed or not text.startswith("#"), "body.h1_count" in {issue.code for issue in issues})


    def test_invalid_mirror_source_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            path = root / "governance/schemas/registries.yaml"
            registry = yaml.safe_load(path.read_text())
            for value in (None, "", "/absolute", "../escape", "docs/../escape", "docs\\escape"):
                registry["local_sources"]["cann_docs_raw"]["mirror"]["source_root"] = value
                path.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False))
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, "mirror.source_root"):
                    Contract(root)


    def test_malformed_mirror_sources_report_findings_without_crashing(self) -> None:
        from governance.contracts.checks import Document, RunContext, body

        relative = Path("knowledge/ops/ascendc/apis/synthetic.md")
        for sources in (None, 1, "invalid", {"resource": "invalid"}):
            metadata = dict(SYNTHETIC_API_METADATA, sources=sources)
            document = Document.create(self.contract, ROOT / relative, relative, "", metadata, "# First\n\n# Second\n")
            with self.subTest(sources=sources):
                issues = body.check(self.contract, document, RunContext())
                self.assertIn("body.h1_count", {issue.code for issue in issues})


class FixedArchiveHeaderTests(unittest.TestCase):
    def load_module(self):
        path = ROOT / ".agents/skills/knowledge-ingest/scripts/fixed_archive_docs.py"
        spec = importlib.util.spec_from_file_location("fixed_archive_docs_test", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_archive_selection_and_whitespace_exceptions_share_source_roles(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            contract = Contract(root)
            definition = contract.local_sources["cann_docs_raw"]
            prefix = f"{definition['root']}/{definition['mirror']['source_root']}/"
            expected = set()
            for kind, profile in (("API", "apis"), ("Guide", "guides")):
                for role in (None, "primary", "supporting", "example", "constraint",
                             "header", "implementation", "evidence"):
                    with self.subTest(kind=kind, role=role):
                        source = {"resource": f"{prefix}example.md"}
                        if role is not None:
                            source["role"] = role
                        metadata = {**SYNTHETIC_API_METADATA, "type": kind, "sources": [source]}
                        managed = "- [Related](other.md)"
                        text = module.render_card(metadata, "# Topic\n\nBody.  \n", managed)
                        path = root / f"knowledge/ops/ascendc/{profile}/{role or 'unroled'}.md"
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(text, encoding="utf-8", newline="\n")
                        is_mirror = role in (None, "primary")
                        if is_mirror:
                            expected.add(path)
                        offsets = module.mirror_authored_offsets(text, prefix, contract)
                        self.assertEqual(is_mirror, offsets is not None)
                        if offsets is not None:
                            self.assertEqual("# Topic\n\nBody.  \n", text[slice(*offsets)])
                        self.assertIsNone(module.mirror_authored_offsets(
                            text, "cann-docs-raw/other/", contract
                        ))
            self.assertEqual(expected, module.mirror_card_paths(root, definition))

    def test_source_frontmatter_is_stripped_before_mirroring(self) -> None:
        module = self.load_module()
        frontmatter = "---\nokftype: reference.api\ndependencies: []\n---\n"
        self.assertEqual(
            "# Title\n\nBody.\n",
            module.strip_source_frontmatter(frontmatter + "# Title\n\nBody.\n"),
        )
        self.assertEqual(
            "# Title\n",
            module.strip_source_frontmatter(
                "---\nokftype: reference.api\n---\n\n# Title\n"
            ),
        )
        self.assertEqual(
            "# Plain\n",
            module.strip_source_frontmatter("# Plain\n"),
        )
        self.assertEqual(
            "---\nnot a mapping\n---\n# Title\n",
            module.strip_source_frontmatter("---\nnot a mapping\n---\n# Title\n"),
        )
        self.assertEqual(
            "---\n- one\n- two\n---\n# Title\n",
            module.strip_source_frontmatter("---\n- one\n- two\n---\n# Title\n"),
        )

    def test_archive_sync_preserves_supporting_guide_and_verify_checks_expected_cards(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            base = root / "knowledge/ops/ascendc/guides"
            base.mkdir(parents=True)
            metadata = {
                **SYNTHETIC_API_METADATA, "type": "Guide",
                "sources": [{"resource": "cann-docs-raw/asc-devkit/docs/zh/example.md", "role": "primary"}],
            }
            mirror_text = module.render_card(metadata, "# Source\n\nSource body.\n", "")
            metadata["sources"][0]["role"] = "supporting"
            guide_text = module.render_card(metadata, "# Authored\n\nAuthored body.\n", "")
            mirror, stale, guide = (base / f"{name}.md" for name in ("mirror", "stale", "guide"))
            mirror.write_text(mirror_text, encoding="utf-8")
            stale.write_text(mirror_text, encoding="utf-8")
            guide.write_text(guide_text, encoding="utf-8")
            args = Namespace(knowledge_root=str(root), source_id="cann_docs_raw",
                             command="verify", updated_at="2026-09-11T00:00:00Z", report=None)
            with mock.patch.object(module, "expected_cards", return_value=({mirror: mirror_text}, {}, set())), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(1, module.command(args))
                args.command = "sync"
                self.assertEqual(0, module.command(args))
                self.assertFalse(stale.exists())
                for _ in range(2):
                    self.assertEqual(0, module.command(args))
                    self.assertEqual(guide_text, guide.read_text(encoding="utf-8"))
                    self.assertEqual(mirror_text, mirror.read_text(encoding="utf-8"))
                args.command = "verify"
                self.assertEqual(0, module.command(args))
                mirror.write_text(guide_text, encoding="utf-8")
                self.assertEqual(1, module.command(args))

    def test_navigation_after_accepts_legacy_and_canonical_separators(self) -> None:
        module = self.load_module()
        nav_after = module._navigation_after
        companion = f"\n\n{module.COMPANION_HEADING}\n\n"
        plain_links = "- [Related](other.md)\n- [Guide](guide.md)\n"
        noted_links = "- [Related](other.md)——两者在同一调用序列中成对出现\n"
        with self.subTest("legacy plain link list after two-newline separator"):
            source = "# Topic\n\nBody.\n"
            legacy = source + "\n\n" + plain_links
            self.assertEqual("- [Related](other.md)\n- [Guide](guide.md)",
                             nav_after(source, legacy))
        with self.subTest("legacy links then companion section after them"):
            source = "```cpp\nCopy();\n```\n\n"
            legacy = source + "\n" + plain_links.rstrip("\n") + companion + noted_links
            self.assertIn(module.COMPANION_HEADING, nav_after(source, legacy))
        with self.subTest("legacy two-newline separator with blank-line source tail"):
            source = "# Topic\n\nBody.\n\n"
            legacy = source + "\n\n" + plain_links
            self.assertEqual("- [Related](other.md)\n- [Guide](guide.md)",
                             nav_after(source, legacy))
        with self.subTest("canonical separators from render_card keep working"):
            companion_nav = f"{module.COMPANION_HEADING}\n\n{noted_links}"
            for body, navigation in (
                ("# Topic\n\nBody.\n\n", plain_links),
                ("# Topic\n\nBody.\n", plain_links),
                ("# Topic\n\nBody.", plain_links),
                ("# Topic\n\nBody.\n\n", companion_nav),
                ("# Topic\n\nBody.\n", companion_nav),
            ):
                with self.subTest(body_tail=body[-2:], noted="##" in navigation):
                    rendered = module.render_card({}, body, navigation)
                    framing = module.FRONTMATTER_RE.match(rendered)
                    card_body = rendered[framing.end():]
                    self.assertEqual(navigation.rstrip("\n"), nav_after(body, card_body))
        with self.subTest("re-rendered navigation round-trips through the parser"):
            source = "# Topic\n\nBody.\n"
            legacy = source + "\n\n" + plain_links
            navigation = nav_after(source, legacy)
            rebuilt = module.render_card({}, source, navigation)
            framing = module.FRONTMATTER_RE.match(rebuilt)
            self.assertEqual(navigation, nav_after(source, rebuilt[framing.end():]))
        with self.subTest("non-navigation additions are still rejected"):
            source = "# Topic\n\nBody.\n"
            for bad in (
                "\n\nPlain text paragraph.\n",
                "\n\n- [Related](other.md)\nExtra line.\n",
                "\n\n\n\n- [Related](other.md)\n",
                "\n",
                "X- [Related](other.md)\n",
                "\nX- [Related](other.md)\n",
                "\n\nX- [Related](other.md)\n",
            ):
                with self.subTest(bad=bad):
                    with self.assertRaises(ValueError):
                        nav_after(source, source + bad)

    def test_api_headers_extracts_declared_and_include_paths(self) -> None:
        module = self.load_module()
        body = (
            "头文件路径为：`\"c_api/reg_compute/compute/reg_arith.h\"`。\n\n"
            "#include \"c_api/asc_simd.h\"\n"
            "#include \"acl/acl.h\"\n"
        )
        self.assertEqual(
            ["include/c_api/reg_compute/compute/reg_arith.h", "include/c_api/asc_simd.h"],
            module.api_headers(body),
        )

    def test_api_headers_normalize_include_prefix_and_drop_non_public(self) -> None:
        module = self.load_module()
        body = (
            "头文件路径为：`\"include/tensor_api/experimental/arch/vector/data_reorder.h\"`。\n"
            "#include \"tools/cpudebug/include/stub_def.h\"\n"
            "#include \"kernel_operator.h\"\n"
        )
        self.assertEqual(
            ["include/tensor_api/experimental/arch/vector/data_reorder.h"],
            module.api_headers(body),
        )

    def test_api_headers_deduplicates(self) -> None:
        module = self.load_module()
        body = (
            "#include \"simt_api/device_warp_functions.h\"\n"
            "#include \"simt_api/device_warp_functions.h\"\n"
        )
        self.assertEqual(
            ["include/simt_api/device_warp_functions.h"], module.api_headers(body)
        )

    def metadata(self, module, *, old=None, body="# Probe\n", profile="apis"):
        return module.metadata_for(
            source=Path("/archive/source/api/Probe.md"),
            source_root=Path("/archive/source"),
            output=Path(f"/repo/knowledge/ops/ascendc/{profile}/probe.md"),
            body=body,
            definition={"root": "cann-docs-raw", "_archive_root": Path("/archive")},
            old=old,
            stamp="2026-09-08T00:00:00Z",
        )

    def test_metadata_retains_reviewed_headers_and_render_is_idempotent(self) -> None:
        module = self.load_module()
        body = '# Probe\n\n正文与空白保持。  \n\n```cpp\n#include "kernel_operator.h"\n```\n'
        old = self.metadata(module, body=body)
        old["source_headers"] = ["include/basic_api/probe.h"]
        managed = "- [关联](other.md)"
        expected = module.render_card(old, body, managed)
        for _ in range(2):
            new = self.metadata(module, old=old, body=body)
            self.assertEqual(old, new)
            self.assertIsNot(old["source_headers"], new["source_headers"])
            self.assertEqual(expected, module.render_card(new, body, managed))
            old = new

    def test_mirror_preserves_plain_link_suffix_and_rejects_untracked_prose(self) -> None:
        module = self.load_module()
        body = "# Probe\n\nFixed contract with source whitespace.  \n"
        metadata = self.metadata(module, body=body)
        navigation = "- [Related](other.md)"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "probe.md"
            rendered = module.render_card(metadata, body, navigation)
            path.write_text(rendered, encoding="utf-8", newline="\n")
            old, suffix = module.existing_card(path, body)
            self.assertEqual(metadata, old)
            self.assertEqual(navigation, suffix)
            self.assertEqual(rendered, module.render_card(old, body, suffix))
            path.write_text(
                module.render_card(metadata, body, None) + "\nInjected claim.\n",
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(ValueError, "ordinary trailing links"):
                module.existing_card(path, body)

    def test_companion_navigation_is_preserved_and_bounded(self) -> None:
        module = self.load_module()
        body = "# Probe\n\nFixed contract with source whitespace.  \n"
        changed = "# Probe\n\nOfficial wording changed.\n"
        note = "两个接口先后使用，后者消费前者的输出"
        navigation = (
            "- [Operator](operator.md)\n\n"
            "## 配套 API 与常见组合\n\n"
            f"- [Related](other.md)——{note}\n"
            "- [Bare](bare.md)"
        )
        metadata = self.metadata(module, body=body)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "probe.md"
            rendered = module.render_card(metadata, body, navigation)
            path.write_text(rendered, encoding="utf-8", newline="\n")
            old, suffix = module.existing_card(path, body)
            self.assertEqual(navigation, suffix)
            self.assertEqual(rendered, module.render_card(old, body, suffix))
            source, peeled = module.split_link_suffix(body + "\n" + navigation + "\n")
            self.assertEqual(body, source)
            self.assertEqual(navigation + "\n", peeled)
            old, suffix = module.existing_card(path, changed)
            self.assertEqual(navigation, suffix)

            accepted = f"## 配套 API 与常见组合\n\n- [Related](other.md)——{'A' * 110}"
            path.write_text(
                module.render_card(metadata, body, accepted),
                encoding="utf-8",
                newline="\n",
            )
            _, suffix = module.existing_card(path, body)
            self.assertEqual(accepted, suffix)

            rejected = (
                f"## 配套 API 与常见组合\n\n- [Related](other.md)——{'A' * 111}",
                "## 配套 API 与常见组合\n\n- [Related](other.md)——见 [另一张](x.md)",
                "## 配套 API 与常见组合\n\n- [Related](other.md)——",
                "## 其他标题\n\n- [Related](other.md)",
                "- [Related](other.md)——没有配套标题的机制说明",
                "## 配套 API 与常见组合\n\n不是链接列表",
            )
            for addition in rejected:
                path.write_text(
                    module.render_card(metadata, body, addition),
                    encoding="utf-8",
                    newline="\n",
                )
                with self.assertRaisesRegex(ValueError, "ordinary trailing links"):
                    module.existing_card(path, body)

    def test_source_trailing_newline_stays_outside_companion_navigation(self) -> None:
        module = self.load_module()
        source = "# Probe\n\n返回值说明\n\n无\n"
        navigation = (
            "## 配套 API 与常见组合\n\n"
            "- [SoftmaxGradFront](softmax_grad_front.md)——产出的 SoftMaxTiling 传入 kernel 侧 SoftmaxGradFront"
        )
        metadata = self.metadata(module, body=source)
        rendered = module.render_card(metadata, source, navigation)
        self.assertIn("无\n\n## 配套 API 与常见组合\n", rendered)
        self.assertNotIn("无\n\n\n## 配套 API 与常见组合\n", rendered)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "probe.md"
            path.write_text(rendered, encoding="utf-8", newline="\n")
            _, suffix = module.existing_card(path, source)
            self.assertEqual(navigation, suffix)
            self.assertEqual(rendered, module.render_card(metadata, source, suffix))
            refreshed_source = "返回值说明\n\n有\n"
            _, kept = module.existing_card(path, refreshed_source)
            self.assertEqual(navigation, kept)
            refreshed = module.render_card(metadata, refreshed_source, kept)
            path.write_text(refreshed, encoding="utf-8", newline="\n")
            _, again = module.existing_card(path, refreshed_source)
            self.assertEqual(navigation, again)
            self.assertEqual(refreshed, module.render_card(metadata, refreshed_source, again))
            self.assertIn("有\n\n## 配套 API 与常见组合\n", refreshed)
            blank_source = "# Probe\n\n段落。\n\n"
            blank_navigation = "## 配套 API 与常见组合\n\n- [Related](other.md)——来源正文末尾已经有空行"
            blank_rendered = module.render_card(metadata, blank_source, blank_navigation)
            self.assertIn("段落。\n\n## 配套 API 与常见组合\n", blank_rendered)
            self.assertNotIn("段落。\n\n\n## 配套 API 与常见组合\n", blank_rendered)
            path.write_text(blank_rendered, encoding="utf-8", newline="\n")
            _, blank_suffix = module.existing_card(path, blank_source)
            self.assertEqual(blank_navigation, blank_suffix)

        card = (
            ROOT
            / "knowledge/ops/ascendc/apis/simd_api/adv_api/activation_functions"
            / "soft_max_interface/softmax_grad_tiling_interface.md"
        )
        text = card.read_bytes().decode("utf-8").replace("\r\n", "\n")
        marker = "无\n\n## 配套 API 与常见组合\n"
        self.assertIn(marker, text)
        framing = module.FRONTMATTER_RE.match(text)
        self.assertIsNotNone(framing)
        source_end = text.index(marker) + len("无\n")
        independent_source = text[framing.end() : source_end]
        self.assertTrue(independent_source.endswith("无\n"))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "softmax_grad_tiling_interface.md"
            path.write_text(text, encoding="utf-8", newline="\n")
            _, real_navigation = module.existing_card(path, independent_source)
        self.assertIsNotNone(real_navigation)
        self.assertTrue(real_navigation.startswith("## 配套 API 与常见组合\n"))
        post = text[framing.end() :]
        self.assertEqual(post, independent_source + "\n" + real_navigation + "\n")
        frontmatter = yaml.safe_load(framing.group("metadata"))
        replayed = module.render_card(frontmatter, independent_source, real_navigation)
        replay_framing = module.FRONTMATTER_RE.match(replayed)
        self.assertIsNotNone(replay_framing)
        self.assertEqual(post, replayed[replay_framing.end() :])

    def test_repository_companion_sections_match_mirror_navigation(self) -> None:
        module = self.load_module()
        found = 0
        for path in (ROOT / "knowledge").rglob("*.md"):
            text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
            if "## 配套 API 与常见组合" not in text:
                continue
            framing = module.FRONTMATTER_RE.match(text)
            self.assertIsNotNone(framing, path)
            post = text[framing.end() :]
            body, navigation = module.split_link_suffix(post)
            self.assertIsNotNone(navigation, path)
            self.assertIn("## 配套 API 与常见组合", navigation)
            self.assertTrue(body.endswith("\n"), path)
            self.assertFalse(navigation.startswith("\n"), path)
            self.assertEqual(post, body + "\n" + navigation, path)
            suffix = post[len(body) :]
            self.assertTrue(suffix.startswith("\n"), path)
            self.assertTrue(module._is_trailing_navigation(suffix[1:]), path)
            self.assertEqual(navigation.rstrip("\n"), suffix[1:].rstrip("\n"), path)
            found += 1
        self.assertGreater(found, 0)

    def test_metadata_doc_headers_override_existing_enrichment(self) -> None:
        module = self.load_module()
        old = self.metadata(module)
        old["source_headers"] = ["include/basic_api/old.h"]
        body = '# Probe\n\n#include "basic_api/new.h"\n'
        new = self.metadata(module, old=old, body=body)
        self.assertEqual(["include/basic_api/new.h"], new["source_headers"])
        self.assertEqual(["include/basic_api/old.h"], old["source_headers"])

    def test_metadata_does_not_invent_headers_or_add_them_to_guides(self) -> None:
        module = self.load_module()
        self.assertNotIn("source_headers", self.metadata(module))
        old = self.metadata(module)
        old["source_headers"] = []
        self.assertNotIn("source_headers", self.metadata(module, old=old))
        self.assertNotIn(
            "source_headers",
            self.metadata(module, body='# Probe\n#include "basic_api/probe.h"\n', profile="guides"),
        )

    def test_metadata_rejects_invalid_retained_headers(self) -> None:
        module = self.load_module()
        header = "include/basic_api/probe.h"
        for value in (
            None, header, [None], [{}], [""], [header, header],
            ["/include/basic_api/probe.h"], ["basic_api/probe.h"],
            ["include/basic_api/../probe.h"], ["include/basic_api/./probe.h"],
            ["include/basic_api//probe.h"], ["include/basic_api/probe.h#anchor"],
            ["include/basic_api\\probe.h"], ["include/basic_api/probe.so"],
            ["include/private_api/probe.h"], ["include/kernel_operator.h"],
        ):
            with self.subTest(value=value):
                old = self.metadata(module)
                old["source_headers"] = value
                with self.assertRaisesRegex(ValueError, "invalid retained source_headers"):
                    self.metadata(module, old=old)

    def test_metadata_rejects_transferring_enrichment_to_another_source(self) -> None:
        module = self.load_module()
        for sources in (
            None, [], "not-a-list",
            [{"resource": "cann-docs-raw/source/api/Other.md", "role": "primary"}],
            [{"resource": "cann-docs-raw/source/api/Probe.md", "role": "supporting"}],
        ):
            with self.subTest(sources=sources):
                old = self.metadata(module)
                old["source_headers"] = ["include/basic_api/probe.h"]
                old["sources"] = sources
                with self.assertRaisesRegex(ValueError, "source_headers source changed"):
                    self.metadata(module, old=old)

    def test_api_headers_drop_unsafe_source_paths(self) -> None:
        module = self.load_module()
        self.assertEqual([], module.api_headers(
            '#include "basic_api/../../probe.h"\n'
            '#include "basic_api//probe.h"\n'
            '#include "basic_api/./probe.h"\n'
        ))


class IngestContractTests(unittest.TestCase):
    def run_ingest(
        self,
        extra: list[str],
        *,
        tags: tuple[str, ...] = ("task.lookup", "topic.compilation"),
        platforms: tuple[str, ...] = ("a2",),
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md") as body:
            body.write("# Candidate\n")
            body.flush()
            command = [
                sys.executable,
                str(INGEST),
                "--knowledge-root",
                str(ROOT),
                "create",
                "--path",
                "knowledge/ops/ascendc/concepts/contract_probe.md",
                "--title",
                "Contract probe",
                "--description",
                "Contract probe",
                "--source",
                PINNED_SOURCE,
                "--body-file",
                body.name,
                "--dry-run",
            ]
            for tag in tags:
                command.extend(["--tag", tag])
            for platform in platforms:
                command.extend(["--platform", platform])
            command.extend(extra)
            return subprocess.run(command, check=False, text=True, capture_output=True)

    def test_valid_candidate_is_rendered(self) -> None:
        result = self.run_ingest([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("type: Concept", result.stdout)
        self.assertIn("title: Contract probe", result.stdout)
        self.assertIn("resource: https://gitcode.com/", result.stdout)

    def test_target_contract_is_compared_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "knowledge").mkdir()
            (root / "governance/contracts").mkdir(parents=True)
            marker = root / "import-executed"
            (root / "governance/contracts/knowledge.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
                encoding="utf-8",
            )
            body = root / "body.md"
            body.write_text("# Candidate\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(INGEST),
                    "--knowledge-root",
                    str(root),
                    "create",
                    "--path",
                    "knowledge/common/glossaries/probe.md",
                    "--title",
                    "Probe",
                    "--description",
                    "Probe",
                    "--tag",
                    "task.lookup",
                    "--tag",
                    "topic.terminology",
                    "--body-file",
                    str(body),
                    "--dry-run",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            executed = marker.exists()
        self.assertEqual(2, result.returncode)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(executed)

    def test_profile_violations_are_rejected(self) -> None:
        cases = {
            "empty title": (["--title", ""], ("task.lookup", "topic.compilation"), ("a2",)),
            "missing topic": ([], ("task.lookup", "task.testing"), ("a2",)),
            "duplicate tag": ([], ("task.lookup", "topic.compilation", "topic.compilation"), ("a2",)),
            "mixed agnostic": ([], ("task.lookup", "topic.compilation"), ("a2", "agnostic")),
            "stable replacement": (
                [
                    "--status",
                    "stable",
                    "--replaced-by",
                    "ops/ascendc/concepts/replacement",
                ],
                ("task.lookup", "topic.compilation"),
                ("a2",),
            ),
        }
        for name, (extra, tags, platforms) in cases.items():
            with self.subTest(case=name):
                result = self.run_ingest(extra, tags=tags, platforms=platforms)
                self.assertEqual(result.returncode, 2, result.stdout)

    def test_verified_actor_contract(self) -> None:
        invalid = self.run_ingest(
            [
                "--verified-by",
                "reviewer",
                "--verified-at",
                "2026-08-15T08:00:00Z",
            ]
        )
        self.assertEqual(invalid.returncode, 2, invalid.stdout)
        self.assertIn("verified.actor", invalid.stderr)

        valid = self.run_ingest(
            [
                "--verified-by",
                "human:reviewer",
                "--verified-at",
                "2026-08-15T08:00:00Z",
            ]
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn("by: human:reviewer", valid.stdout)

        incomplete = self.run_ingest(["--verified-by", "human:reviewer"])
        self.assertEqual(incomplete.returncode, 2, incomplete.stdout)
        self.assertIn("must be provided together", incomplete.stderr)

    def test_unpinned_stable_git_source_is_rejected(self) -> None:
        for url in (
            "https://github.com/triton-lang/triton-ascend/tree/main",
            "https://gitcode.com/cann/cann-recipes-infer/pull/418/files",
        ):
            with self.subTest(url=url):
                result = self.run_ingest(["--status", "stable", "--source", url])
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("source.pin", result.stderr)

    def test_pinned_git_and_work_item_sources_are_accepted(self) -> None:
        commit = "c846650eec121f41bd0efa472fc5c84594b8208d"
        urls = (
            f"https://gitee.com/example/project/raw/{commit}/README.md",
            f"https://gitlab.com/example/project/-/raw/{commit}/README.md",
            f"https://raw.githubusercontent.com/example/project/{commit}/README.md",
            f"https://raw.gitcode.com/example/project/raw/{commit}/README.md",
            f"https://bitbucket.org/example/project/src/{commit}/README.md",
            f"https://codeberg.org/example/project/src/commit/{commit}/README.md",
            "https://gitcode.com/cann/cann-recipes-infer/merge_requests/418",
            "https://github.com/vllm-project/vllm-ascend/issues/972",
        )
        for url in urls:
            with self.subTest(url=url):
                result = self.run_ingest(["--status", "stable", "--source", url])
                self.assertEqual(result.returncode, 0, result.stderr)

class LintBehaviorTests(unittest.TestCase):
    def test_archive_registry_requires_https_url_without_pinned_hashes(self) -> None:
        for update in ({"archive_url": "https://example.invalid/daily.tar.gz"},
                       {"archive_url": "http://example.invalid/daily.tar.gz"},
                       {"archive_url": ""}, {"archive_sha256": "a" * 64},
                       {"tree_sha256": "b" * 64}):
            with self.subTest(update=update), tempfile.TemporaryDirectory() as temporary:
                root = self.make_root(temporary)
                registry = root / "governance/schemas/registries.yaml"
                import yaml
                data = yaml.safe_load(registry.read_text())
                data["local_sources"]["cann_docs_raw"].update(update)
                registry.write_text(yaml.safe_dump(data, allow_unicode=True))
                if update.get("archive_url", "").startswith("https://"):
                    self.assertEqual(update["archive_url"], Contract(root).local_sources["cann_docs_raw"]["archive_url"])
                else:
                    with self.assertRaisesRegex(ValueError, "HTTPS archive_url"):
                        Contract(root)

    def make_root(self, temporary: str) -> Path:
        root = Path(temporary)
        shutil.copytree(ROOT / "governance", root / "governance")
        (root / "knowledge").mkdir()
        return root

    def render_card(
        self,
        *,
        sources: str = "  - resource: https://example.com/source\n    role: primary",
        body: str = "Probe body.",
        created_at: str = "2026-08-22T00:00:00Z",
        title_lines: str = "title: Synthetic API",
    ) -> str:
        return f'''---
type: API
{title_lines}
description: Deterministic lint probe.
tags: [task.lookup, topic.compilation]
status: stable
sources:
{sources}
created_at: "{created_at}"
updated_at: "2026-08-22T00:00:00Z"
platforms: [a2]
---

# Synthetic API

{body}
'''

    def run_lint(
        self,
        root: Path,
        text: str,
        *flags: str,
    ) -> subprocess.CompletedProcess[str]:
        card = root / "knowledge/ops/ascendc/apis/synthetic.md"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(text, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(LINT),
                "--knowledge-root",
                str(root),
                "--card",
                "knowledge/ops/ascendc/apis/synthetic.md",
                *flags,
            ],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_invalid_calendar_time_is_a_card_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(created_at="2026-02-30T00:00:00Z"),
                "--json",
            )
        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(
            "frontmatter.time",
            {finding["code"] for finding in payload["findings"]},
        )

    def test_body_hygiene_rejects_duplicate_h1_and_collapsed_table(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(body="# Duplicate\n\n| A | B | | --- | --- |"),
                "--json",
            )
        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            {"body.h1_count", "body.collapsed_table"},
            {
                finding["code"]
                for finding in payload["findings"]
                if finding["check"] == "body"
            },
        )

    def test_body_hygiene_ignores_h1_and_table_examples_in_fences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(
                    body="````markdown\n```nested example\n# Example\n"
                    "| A | B | | --- | --- |\n```\n````"
                ),
                "--json",
            )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(
            {"body.h1_count", "body.collapsed_table"}
            & {finding["code"] for finding in payload["findings"]}
        )

    def test_fixed_archive_api_mirror_preserves_multiple_h1_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: cann-docs-raw/asc-devkit/docs/zh/example.md\n"
                        "    role: primary"
                    ),
                    body="# Second source topic\n\nSource text.",
                ),
                "--json",
            )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertNotIn(
            "body.h1_count",
            {finding["code"] for finding in payload["findings"]},
        )

    def test_fixed_archive_mirror_rejects_product_support_in_card_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: cann-docs-raw/asc-devkit/docs/zh/example.md\n"
                        "    role: primary"
                    ),
                    body=(
                        "## 产品支持情况\n\n"
                        "- Atlas A2 训练系列产品/Atlas A2 推理系列产品：支持"
                    ),
                ),
                "--json",
            )
        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(
            "platform.redundant_body_scope",
            {finding["code"] for finding in payload["findings"]},
        )

    def test_non_mirror_source_under_archive_root_does_not_get_h1_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: cann-docs-raw/other/example.md\n"
                        "    role: primary"
                    ),
                    body="# Second source topic\n\nSource text.",
                ),
                "--json",
            )
        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(
            "body.h1_count",
            {finding["code"] for finding in payload["findings"]},
        )

    def test_index_entry_without_summary_is_a_nonblocking_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "knowledge/common").mkdir()
            (root / "knowledge/common/index.md").write_text(
                "# Common\n", encoding="utf-8"
            )
            (root / "knowledge/example.md").write_text(
                "# Example\n", encoding="utf-8"
            )
            (root / "knowledge/index.md").write_text(
                '---\nokf_version: "0.2"\n---\n\n# Knowledge\n\n'
                "- [Common](common/index.md)\n\n"
                "- [External](https://example.com)\n\n"
                "```markdown\n- [Example](example.md)\n```\n\n"
                "    - [Indented](example.md)\n\n"
                "- [Inline summary](example.md)：`DataCopy`\n\n"
                "```markdown\n- [Unclosed](example.md)\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINT),
                    "--knowledge-root",
                    str(root),
                    "--card",
                    "knowledge/index.md",
                    "--json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [
                {
                    "check": "index_entry_description",
                    "tier": "P1",
                    "path": "knowledge/index.md",
                    "line": 7,
                    "code": "index.entry_description",
                    "message": "index entry requires a summary",
                    "details": "- [Common](common/index.md)",
                }
            ],
            payload["findings"],
        )

    def test_duplicate_frontmatter_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(title_lines="title: First\ntitle: Second"),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("frontmatter.parse", result.stdout)
        self.assertIn("duplicate key", result.stdout)

    def test_reference_links_and_image_pins_are_checked(self) -> None:
        body = """[Missing document][missing-doc]

![Missing diagram][missing-image]

<img data-src="missing-image.png">

[missing-doc]: missing.md
[missing-image]: missing.png"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(root, self.render_card(body=body))
        self.assertEqual(1, result.returncode)
        self.assertIn("image.pin", result.stdout)
        self.assertIn("image.syntax", result.stdout)
        self.assertIn("link.missing", result.stdout)

    def test_pinned_markdown_and_html_images_are_allowed(self) -> None:
        commit = "c846650eec121f41bd0efa472fc5c84594b8208d"
        markdown = (
            "https://raw.gitcode.com/cann/example/raw/"
            f"{commit}/docs/diagram.png"
        )
        html = (
            "https://raw.gitcode.com/cann/example/raw/"
            f"{commit}/docs/architecture.jpg"
        )
        body = f"""![Diagram]({markdown})

![Reference][diagram]
[diagram]: {markdown}

<img src="{html}" alt="Architecture" width="55%">"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(root, self.render_card(body=body))
        self.assertEqual(0, result.returncode, result.stdout)

    def test_links_ignore_code_and_images_and_report_locations(self) -> None:
        body = """[Inline](missing-inline.md)
`[Inline code](missing-code.md)`
![Image](missing-image.md)
```markdown
[Fenced](missing-fenced.md)
```
[Reference][missing-reference]
[missing-reference]: missing-reference.md
[Outside](../../../../README.md)
[Directory](directory_target)"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "README.md").write_text("# Outside\n", encoding="utf-8")
            (root / "knowledge/ops/ascendc/apis/directory_target").mkdir(
                parents=True
            )
            result = self.run_lint(root, self.render_card(body=body), "--json")
        self.assertEqual(1, result.returncode, result.stderr)
        findings = [
            finding
            for finding in json.loads(result.stdout)["findings"]
            if finding["check"] == "links"
        ]
        self.assertEqual(
            [
                ("link.missing", 17, "missing-inline.md"),
                ("link.missing", 23, "missing-reference.md"),
                ("link.outside_bundle", 25, "../../../../README.md"),
                ("link.not_file", 26, "directory_target"),
            ],
            [
                (finding["code"], finding["line"], finding["details"])
                for finding in findings
            ],
        )

    def test_index_empty_requires_a_valid_direct_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            common = root / "knowledge/common"
            glossaries = common / "glossaries"
            invalid_child = glossaries / "nested"
            invalid_child.mkdir(parents=True)
            (common / "index.md").write_text("# Common\n", encoding="utf-8")
            (glossaries / "index.md").write_text(
                "# Glossaries\n",
                encoding="utf-8",
            )
            (glossaries / "README.txt").write_text("junk\n", encoding="utf-8")
            (glossaries / "Bad-Name.md").write_text("# Invalid\n", encoding="utf-8")
            (invalid_child / "index.md").write_text(
                "# Invalid child\n",
                encoding="utf-8",
            )
            contract = Contract(root)

            empty_paths = {
                path.resolve().relative_to(root.resolve()).as_posix()
                for path, issue in contract.validate_index_tree()
                if issue.code == "index.empty"
            }
            self.assertIn("knowledge/common/glossaries", empty_paths)
            self.assertNotIn("knowledge/common", empty_paths)

            (glossaries / "valid_card.md").write_text(
                "# Valid path\n",
                encoding="utf-8",
            )
            populated_paths = {
                path.resolve().relative_to(root.resolve()).as_posix()
                for path, issue in contract.validate_index_tree()
                if issue.code == "index.empty"
            }
        self.assertNotIn("knowledge/common/glossaries", populated_paths)

    def test_local_link_cannot_leave_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "README.md").write_text("# Outside\n", encoding="utf-8")
            result = self.run_lint(
                root,
                self.render_card(body="[Outside](../../../../README.md)"),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("link.outside_bundle", result.stdout)

    def test_local_link_must_target_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            directory = root / "knowledge/ops/ascendc/apis/directory_target"
            directory.mkdir(parents=True)
            result = self.run_lint(
                root,
                self.render_card(body="[Directory](directory_target)"),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("link.not_file", result.stdout)

    def test_strict_navigation_requires_same_repository(self) -> None:
        commit = "54beb3b1f2f32067ac026202546011cd1b03977f"
        tree = f"https://gitcode.com/cann/repo-a/tree/{commit}/src/"
        unrelated = f"https://github.com/unrelated/repo-b/blob/{commit}/README.md"
        same_repo = f"https://gitcode.com/cann/repo-a/blob/{commit}/src/file.cpp"
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            rejected = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        f"  - resource: {tree}\n"
                        "    role: primary\n"
                        f"  - resource: {unrelated}\n"
                        "    role: supporting"
                    )
                ),
                "--strict-navigation",
            )
            accepted = self.run_lint(
                root,
                self.render_card(
                    sources=f"  - resource: {tree}\n    role: primary",
                    body=f"[Exact implementation]({same_repo})",
                ),
                "--strict-navigation",
            )
        self.assertEqual(1, rejected.returncode)
        self.assertIn("source.navigation", rejected.stdout)
        self.assertEqual(0, accepted.returncode, accepted.stdout)

    def test_existing_local_source_root_checks_marker_and_file(self) -> None:
        source_yaml = "  - resource: cann-docs-raw/source.md\n    role: primary"
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            absent = self.run_lint(root, self.render_card(sources=source_yaml))
        self.assertEqual(0, absent.returncode, absent.stdout)

        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            source_root = root / "cann-docs-raw"
            source_root.mkdir()
            source_definition = Contract(root).local_sources["cann_docs_raw"]
            archive_url = source_definition["archive_url"]
            (source_root / ".complete").write_text(
                f"archive_url={archive_url}\n",
                encoding="utf-8",
            )
            (source_root / "source.md").write_text("# Source\n", encoding="utf-8")
            valid = self.run_lint(root, self.render_card(sources=source_yaml))
        self.assertEqual(0, valid.returncode, valid.stdout)

        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            source_root = root / "cann-docs-raw"
            source_root.mkdir()
            (source_root / ".complete").write_text(
                "archive_url=https://wrong.example/archive.tar.gz\n",
                encoding="utf-8",
            )
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: cann-docs-raw/missing.md\n"
                        "    role: primary"
                    )
                ),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("source.archive_marker", result.stdout)
        self.assertIn("source.local_missing", result.stdout)

    def test_full_lint_requires_an_executable_local_source_fetch_script(self) -> None:
        module = load_lint_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            missing = module.Linter(root, False)
            missing.validate_full_tree()
            missing_codes = {finding["code"] for finding in missing.findings}

            fetch_script = root / "get_resources.sh"
            fetch_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            fetch_script.chmod(0o644)
            non_executable = module.Linter(root, False)
            non_executable.validate_full_tree()
            mode_codes = {
                finding["code"] for finding in non_executable.findings
            }
        self.assertIn("source.fetch_script_missing", missing_codes)
        self.assertIn("source.fetch_script_mode", mode_codes)

    def test_log_entries_require_summary_and_details(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "logs").mkdir()
            (root / "logs/2026-08-22.md").write_text(
                "# 2026-08-22\n\n## [08:00] governance | Missing sections\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(LINT), "--knowledge-root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("log.sections", result.stdout)

    def test_target_contract_is_compared_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "knowledge").mkdir()
            (root / "governance/schemas").mkdir(parents=True)
            (root / "governance/contracts").mkdir(parents=True)
            (root / "governance/schemas/registries.yaml").write_text("{}\n", encoding="utf-8")
            marker = root / "import-executed"
            (root / "governance/contracts/knowledge.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(LINT), "--knowledge-root", str(root), "--sample", "1"],
                check=False,
                text=True,
                capture_output=True,
            )
            executed = marker.exists()
        self.assertEqual(2, result.returncode)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(executed)

    def test_invalid_schema_returns_operational_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            schema_path = root / "governance/schemas/frontmatter.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["type"] = "invalid-json-schema-type"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LINT), "--knowledge-root", str(root), "--sample", "1"],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertNotIn("Traceback", result.stderr)

    def test_bitbucket_branch_source_is_not_considered_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: https://bitbucket.org/example/project/src/main/README.md\n"
                        "    role: primary"
                    )
                ),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("source.pin", result.stdout)


class MigratedSkillContractTests(unittest.TestCase):
    def test_lint_rejects_description_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            card = root / "knowledge/ops/ascendc/apis/synthetic.md"
            card.parent.mkdir(parents=True)
            metadata = dict(SYNTHETIC_API_METADATA)
            metadata["description"] = "表1 Summary"
            card.write_text(
                "---\n"
                + "\n".join(
                    [
                        f"type: {metadata['type']}",
                        f"title: {metadata['title']}",
                        f"description: {metadata['description']}",
                        "tags: [task.lookup, topic.compilation]",
                        "status: stable",
                        "sources:",
                        "  - resource: https://example.com/cann/synthetic-api",
                        'created_at: "2026-08-18T00:00:00Z"',
                        'updated_at: "2026-08-18T00:00:00Z"',
                        "platforms: [a2]",
                    ]
                )
                + "\n---\n\n# Synthetic\n\nComplete body.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINT),
                    "--knowledge-root",
                    str(root),
                    "--card",
                    "knowledge/ops/ascendc/apis/synthetic.md",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("frontmatter.description_placeholder", result.stdout)

    def test_query_receipt_is_versioned_and_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            shutil.copytree(ROOT / "governance", root / "governance")
            (root / "knowledge").mkdir(parents=True)
            built = subprocess.run(
                [sys.executable, str(INDEX), "--knowledge-root", str(root), "build"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, built.returncode, built.stderr)
            receipt = work / "search.json"
            command = [
                sys.executable,
                str(QUERY),
                "--knowledge-root",
                str(root),
                "search",
                "--query",
                "qzxk_vwbr_hjdm_plqn",
                "--technology",
                "ascendc",
                "--platform",
                "a2",
                "--decision",
                "empty corpus receipt",
                "--receipt",
                str(receipt),
                "--json",
            ]
            first = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "cannbot-knowledge-search.v3")
            self.assertEqual(payload["request"]["platforms"], ["a2"])
            self.assertTrue(payload["request_sha256"])
            self.assertTrue(payload["index"]["content_fingerprint"])
            self.assertTrue(payload["index"]["governance_fingerprint"])
            self.assertEqual(payload["result"]["count"], 0)
            self.assertTrue(all(hit["card_sha256"] for hit in payload["result"]["hits"]))
            self.assertTrue(all(hit["card_lines"] > 0 for hit in payload["result"]["hits"]))
            second = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite receipt", second.stderr)

    def test_strict_navigation_reports_broad_tree_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            card = root / "knowledge/ops/ascendc/operators/aclnn/nn/activation/synthetic.md"
            card.parent.mkdir(parents=True)
            card.write_text(
                """---
type: Operator
title: Synthetic operator
description: Contract-only broad source fixture.
tags: [task.implementation, topic.activation]
status: draft
sources:
  - resource: https://gitcode.com/cann/ops-nn/tree/54beb3b1f2f32067ac026202546011cd1b03977f/activation/synthetic/
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: [a2]
---

# Synthetic operator

This isolated fixture verifies strict source navigation.
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINT),
                    "--knowledge-root",
                    str(root),
                    "--card",
                    "knowledge/ops/ascendc/operators/aclnn/nn/activation/synthetic.md",
                    "--strict-navigation",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("source.navigation", result.stdout)


class IndexSummaryTests(unittest.TestCase):
    def write_card(self, root: Path, name: str, title: str, description: str) -> None:
        (root / name).write_text(
            f"---\ntitle: {title}\ndescription: {description}\n---\n\n# {title}\n",
            encoding="utf-8",
        )

    def test_overview_card_description_leads_the_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "hybrid"
            directory.mkdir()
            self.write_card(
                directory,
                "overview.md",
                "混合编程概述",
                "以SIMD为主、SIMT为辅的混合编程模型。",
            )
            self.write_card(directory, "a.md", "抽象硬件架构", "架构描述。")
            self.write_card(directory, "b.md", "核函数与VF函数", "核函数描述。")
            self.write_card(directory, "c.md", "内存层级", "内存描述。")
            self.write_card(directory, "d.md", "编程示例", "示例描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "以SIMD为主、SIMT为辅的混合编程模型。"
                "（共 5 张知识卡：抽象硬件架构、核函数与VF函数、内存层级 等）",
            )

    def test_directory_named_card_takes_precedence_over_overview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "matrix_compute"
            directory.mkdir()
            self.write_card(
                directory,
                "matrix_compute.md",
                "矩阵计算",
                "矩阵计算由数据搬入、mmad计算和结果搬出组成。",
            )
            self.write_card(directory, "overview.md", "概述", "详细描述请参考LINK。")
            self.write_card(directory, "aux.md", "辅助配置", "辅助描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "矩阵计算由数据搬入、mmad计算和结果搬出组成。"
                "（共 3 张知识卡：辅助配置、概述）",
            )

    def test_collection_summary_without_overview_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "family"
            directory.mkdir()
            self.write_card(directory, "a.md", "算子甲", "甲描述。")
            self.write_card(directory, "b.md", "算子乙", "乙描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "共 2 张知识卡（如 算子甲、算子乙）。",
            )

    def test_single_card_directory_uses_its_description(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "solo"
            directory.mkdir()
            self.write_card(directory, "a.md", "唯一卡", "唯一描述。")
            self.assertEqual(summarize_subdir(directory), "唯一描述。")

    def test_recursive_count_includes_subdirectory_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "mixed"
            directory.mkdir()
            self.write_card(directory, "a.md", "直接卡", "直接描述。")
            nested = directory / "sub"
            nested.mkdir()
            self.write_card(nested, "x.md", "嵌套卡一", "嵌套描述一。")
            self.write_card(nested, "y.md", "嵌套卡二", "嵌套描述二。")
            self.assertEqual(
                summarize_subdir(directory),
                "共 3 张知识卡（如 直接卡 等）。",
            )

    def test_overview_with_only_nested_cards_reports_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "guide"
            directory.mkdir()
            self.write_card(
                directory, "overview.md", "指南概述", "本指南覆盖编译全流程。"
            )
            nested = directory / "chapter"
            nested.mkdir()
            self.write_card(nested, "x.md", "章节卡", "章节描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "本指南覆盖编译全流程。（共 2 张知识卡，分布在 1 个子目录）",
            )

    def test_nested_only_directory_reports_subdirectory_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "hub"
            directory.mkdir()
            for name in ("sub1", "sub2"):
                nested = directory / name
                nested.mkdir()
                self.write_card(nested, "x.md", f"{name}卡", f"{name}描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "共 2 张知识卡，分布在 2 个子目录（sub1、sub2）。",
            )

    def test_deep_nesting_counts_first_level_subdirectories_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "hub"
            directory.mkdir()
            first = directory / "a"
            (first / "b").mkdir(parents=True)
            second = directory / "c"
            second.mkdir()
            self.write_card(first, "y.md", "一级卡", "一级描述。")
            self.write_card(first / "b", "x.md", "二级卡", "二级描述。")
            self.write_card(second, "z.md", "另一卡", "另一描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "共 3 张知识卡，分布在 2 个子目录（a、c）。",
            )

    def test_deep_nesting_with_overview_counts_first_level_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "guide"
            directory.mkdir()
            self.write_card(
                directory, "overview.md", "指南概述", "本指南覆盖编译全流程。"
            )
            nested = directory / "chapter"
            (nested / "section").mkdir(parents=True)
            self.write_card(nested, "x.md", "章节卡", "章节描述。")
            self.write_card(nested / "section", "y.md", "小节卡", "小节描述。")
            self.assertEqual(
                summarize_subdir(directory),
                "本指南覆盖编译全流程。（共 3 张知识卡，分布在 1 个子目录）",
            )


if __name__ == "__main__":
    unittest.main()
