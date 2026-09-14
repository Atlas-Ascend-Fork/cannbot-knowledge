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

import ast
import json
import os
import tarfile
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from unittest import mock

import yaml


TAG_RE = re.compile(r"\b(?:task|topic|paradigm)(?:\.[a-z][a-z0-9_]*)+\b")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from governance.contracts.knowledge import (  # noqa: E402
    Contract,
    markdown_targets,
    relative_markdown_links,
)


class DocumentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.contract = Contract(cls.root)
        cls.registries = yaml.safe_load(
            (cls.root / "governance/schemas/registries.yaml").read_text(encoding="utf-8")
        )

    def documentation_files(self) -> list[Path]:
        roots = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            self.root / "AGENTS.md",
            self.root / "CLAUDE.md",
            self.root / "governance/specs",
            self.root / ".agents/skills",
            self.root / "docs",
            self.root / "recipes",
            self.root / "knowledge",
            self.root / "logs",
        ]
        result: list[Path] = []
        for path in roots:
            if path.is_file():
                result.append(path)
            else:
                result.extend(path.rglob("*.md"))
        return sorted(result)

    def external_documentation_files(self) -> list[Path]:
        roots = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            self.root / "AGENTS.md",
            self.root / "CLAUDE.md",
            self.root / "governance/specs",
        ]
        roots.extend((self.root / "docs", self.root / "recipes"))
        result: list[Path] = []
        for path in roots:
            if path.is_file():
                result.append(path)
            else:
                result.extend(path.rglob("*.md"))
        return sorted(result)

    def is_fixed_archive_mirror(self, text: str) -> bool:
        framing = re.match(r"\A---\n(?P<metadata>.*?)\n---\n", text, re.DOTALL)
        if framing is None:
            return False
        metadata = yaml.safe_load(framing.group("metadata"))
        if not isinstance(metadata, dict):
            return False
        return self.contract.fixed_archive_mirror(metadata) is not None

    def test_local_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for document in self.documentation_files():
            bundle = self.root / "knowledge" if document.is_relative_to(self.root / "knowledge") else None
            for target, resolved in relative_markdown_links(document, bundle):
                if not resolved.exists():
                    failures.append(f"{document.relative_to(self.root)}: {target}")
        self.assertEqual([], failures)

    def test_readme_links_every_governance_spec(self) -> None:
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        missing = [
            spec.name
            for spec in sorted((self.root / "governance/specs").glob("*.md"))
            if f"governance/specs/{spec.name}" not in readme
        ]
        self.assertEqual([], missing)

    def test_local_link_check_uses_bundle_paths_only_within_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "knowledge/ops/ascendc/apis"
            directory.mkdir(parents=True)
            (directory / "target.md").write_text("# Target\n", encoding="utf-8")
            card = directory / "card.md"
            card.write_text(
                "[relative](target.md)\n[root](/ops/ascendc/apis/target.md)\n"
                "[encoded](/ops/ascendc/apis/%74arget.md)\n",
                encoding="utf-8",
            )
            readme = root / "README.md"
            readme.write_text("[card](knowledge/ops/ascendc/apis/card.md)\n", encoding="utf-8")
            with mock.patch.object(self, "root", root), mock.patch.object(
                self, "documentation_files", return_value=[card, readme]
            ):
                self.test_local_markdown_links_resolve()
                for document, target in (
                    (card, "/ops/ascendc/apis/missing.md"),
                    (readme, "/ops/ascendc/apis/target.md"),
                ):
                    with self.subTest(document=document.name):
                        before = document.read_text(encoding="utf-8")
                        document.write_text(before + f"[invalid]({target})\n", encoding="utf-8")
                        with self.assertRaises(AssertionError):
                            self.test_local_markdown_links_resolve()
                        document.write_text(before, encoding="utf-8")

    def test_readme_links_all_public_documentation(self) -> None:
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        for directory in ("docs", "recipes"):
            for document in sorted((self.root / directory).rglob("*.md")):
                with self.subTest(document=document.relative_to(self.root)):
                    self.assertIn(document.relative_to(self.root).as_posix(), readme)

    def test_reviewed_model_python_examples_have_valid_syntax(self) -> None:
        for relative in (
            "knowledge/model/inference/concepts/models/sana_video.md",
            "knowledge/model/inference/concepts/parallelism/ulysses.md",
        ):
            text = (self.root / relative).read_text(encoding="utf-8")
            blocks = list(re.finditer(r"(?ms)^```python\n(.*?)^```", text))
            self.assertTrue(blocks, relative)
            for block in blocks:
                line = text[:block.start(1)].count("\n") + 1
                with self.subTest(card=relative, line=line):
                    ast.parse(block.group(1), filename=f"{relative}:{line}")

    def test_readme_concrete_knowledge_path_examples_exist(self) -> None:
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        examples = re.findall(r"(?m)^knowledge/[^\n<>]*\.md$", readme)
        self.assertTrue(examples)
        for relative in examples:
            with self.subTest(path=relative):
                path = self.root / relative
                self.assertTrue(path.is_file(), relative)
                self.contract.derive_card_path(Path(relative))

    def test_operator_templates_render_the_requested_cann_version(self) -> None:
        for producer in ("ops-knowledge-vv-ingest", "ops-knowledge-cv-ingest"):
            template = (
                self.root / ".agents/skills" / producer / "templates/operator-template.md"
            ).read_text(encoding="utf-8")
            for version in ("8.5.0", "9.1.0"):
                with self.subTest(producer=producer, version=version):
                    rendered = template.replace("<CANN_VERSION>", version)
                    frontmatter = rendered.split("```markdown\n---\n", 1)[1].split("\n---\n", 1)[0]
                    metadata = yaml.safe_load(frontmatter)
                    self.assertEqual([version], metadata["cann_versions"])

    def test_api_query_mode_requires_a_separate_unlocated_draft_fallback(self) -> None:
        skill = (
            self.root / ".agents/skills/knowledge-query/SKILL.md"
        ).read_text(encoding="utf-8")
        mode = (
            self.root / ".agents/skills/knowledge-query/modes/api-selection/MODE.md"
        ).read_text(encoding="utf-8")
        for text in (skill, mode):
            self.assertIn("--include-unlocated", text)
            self.assertIn("--status draft", text)
            self.assertIn("不能", text)

    def test_governance_specs_keep_five_focused_entries(self) -> None:
        expected = {"okf.md", "paths.md", "frontmatter.md", "schemas.md", "skills.md"}
        actual = {path.name for path in (self.root / "governance/specs").glob("*.md")}
        self.assertEqual(expected, actual)

    def test_okf_reference_is_pinned_and_scoped(self) -> None:
        commit = "fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f"
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        spec = (self.root / "governance/specs/okf.md").read_text(encoding="utf-8")
        reference = (
            "https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/"
            f"{commit}/okf/SPEC.md"
        )
        self.assertIn(reference, readme)
        self.assertIn(reference, spec)
        self.assertIn("符合 OKF v0.2", readme)
        self.assertIn("Open Knowledge Format", spec)
        self.assertIn("`knowledge/` 是本仓唯一的 OKF Knowledge Bundle", spec)

    def test_okf_terms_distinguish_concept_type_and_profiles(self) -> None:
        spec = (self.root / "governance/specs/okf.md").read_text(encoding="utf-8")
        for term in ("OKF Concept", "OKF `type`", "路径 Profile", "CANNBot Profile", "安装模式"):
            with self.subTest(term=term):
                self.assertIn(term, spec)
        self.assertIn("`type: API` 的卡片仍然是一个 OKF Concept", spec)

    def test_verified_is_not_a_stable_requirement(self) -> None:
        profiles = yaml.safe_load(
            (self.root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
        )
        self.assertTrue(
            all("verified" not in profile.get("required", []) for profile in profiles["profiles"].values())
        )
        frontmatter = (self.root / "governance/specs/frontmatter.md").read_text(encoding="utf-8")
        self.assertIn("`status` 和 trust tier 相互独立", frontmatter)

    def test_installation_mode_is_not_called_a_knowledge_profile(self) -> None:
        documents = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            *sorted((self.root / "governance/specs").glob("*.md")),
        ]
        failures = [path.relative_to(self.root).as_posix() for path in documents if "安装 Profile" in path.read_text(encoding="utf-8")]
        self.assertEqual([], failures)

    def test_knowledge_cards_use_okf_core_fields(self) -> None:
        root_index = (self.root / "knowledge/index.md").read_text(encoding="utf-8")
        root_metadata = yaml.safe_load(root_index.split("---", 2)[1])
        self.assertEqual({"okf_version": "0.2"}, root_metadata)

        failures: list[str] = []
        for card in sorted((self.root / "knowledge").rglob("*.md")):
            if card.name == "index.md":
                continue
            metadata = yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1])
            if not str(metadata.get("type", "")).strip():
                failures.append(f"{card.relative_to(self.root)}: missing type")
            if metadata.get("status") not in {"draft", "stable", "deprecated"}:
                failures.append(f"{card.relative_to(self.root)}: invalid status")
            for source in metadata.get("sources", []):
                if "resource" not in source or "url" in source:
                    failures.append(f"{card.relative_to(self.root)}: invalid source shape")
        self.assertEqual([], failures)

    def test_ascendc_runbooks_do_not_use_intermediate_repository_sources(self) -> None:
        forbidden_origin = "npu_code_agent/NPU-Kernel-Wiki"
        failures: list[str] = []
        runbooks = self.root / "knowledge/ops/ascendc/runbooks"
        for card in sorted(runbooks.glob("*/*.md")):
            if card.name == "index.md":
                continue
            text = card.read_text(encoding="utf-8")
            metadata = yaml.safe_load(text.split("---", 2)[1])
            for source in metadata.get("sources", []):
                if forbidden_origin in str(source.get("resource", "")):
                    failures.append(card.relative_to(self.root).as_posix())
            if forbidden_origin in text:
                failures.append(card.relative_to(self.root).as_posix())
        self.assertEqual([], failures)

    def test_knowledge_cards_have_no_managed_graph_blocks(self) -> None:
        failures = [str(path.relative_to(self.root))
                    for path in (self.root / "knowledge").rglob("*.md")
                    if "cannbot:related" in path.read_text(encoding="utf-8")
                    or "cannbot:api-operator" in path.read_text(encoding="utf-8")]
        self.assertEqual([], failures)

    def test_fixed_archive_uses_indexes_as_its_only_navigation_documents(self) -> None:
        mirror_roots = (
            self.root / "knowledge/ops/ascendc/apis",
            self.root / "knowledge/ops/ascendc/guides",
        )
        failures: list[str] = []
        support_heading = re.compile(r"(?m)^#{1,6}\s+[^\n]*产品支持情况")
        for base in mirror_roots:
            for card in sorted(base.rglob("*.md")):
                if card.name == "index.md":
                    continue
                text = card.read_text(encoding="utf-8")
                if not self.is_fixed_archive_mirror(text):
                    continue
                if card.name.casefold() == "readme.md":
                    failures.append(f"{card.relative_to(self.root)}: README card")
                if "本文件为文档发布时所需的索引文件" in text:
                    failures.append(f"{card.relative_to(self.root)}: publisher placeholder")
                if support_heading.search(text):
                    failures.append(f"{card.relative_to(self.root)}: product support section")
        self.assertEqual([], failures)

        api_root = self.root / "knowledge/ops/ascendc/apis"
        absent_navigation = (
            api_root / "readme.md",
            api_root / "api_list.md",
            api_root / "ai_cpu_api/ai_cpu_api_list.md",
            api_root / "simd_api/adv_api/adv_api.md",
            api_root / "simd_api/adv_api/adv_api_list.md",
        )
        retained_knowledge = (
            api_root / "simd_api/basic_api/kernel_tiling/tiling_key_list.md",
            api_root
            / "utils_api/prototype_register_management/op_param_def/data_type_list.md",
            api_root
            / "simd_api/basic_api/data_move_guide/overview/overview.md",
            api_root / "simd_api/c_api/c_api_reference.md",
        )
        self.assertTrue(all(not path.exists() for path in absent_navigation))
        self.assertTrue(all(path.is_file() for path in retained_knowledge))

    def body_invocation_pairs(self):
        cached = getattr(type(self), "_body_invocation_pairs", None)
        if cached is None:
            module = self.load_module(
                self.root / ".agents/skills/knowledge-ingest/scripts/api_operator_links.py",
                "documentation_body_invocations",
            )
            with mock.patch.object(module, "source_inputs", return_value=[]):
                items = module.invocations(self.root)[2]
            cached = {(item.api.path, item.operator.path) for item in items}
            type(self)._body_invocation_pairs = cached
        return cached

    def test_api_operator_invocation_navigation_examples_are_present(self) -> None:
        cases = (
            (
                self.root
                / "knowledge/ops/ascendc/apis/utils_api/tiling_template_programming/get_tpl_tiling_key.md",
                "../../../operators/aclnn/cv/objdetect/roi_pooling_with_arg_max_950.md",
            ),
            (
                self.root
                / "knowledge/ops/ascendc/apis/simd_api/basic_api/kernel_tiling/tiling_key_is.md",
                "../../../../operators/aclnn/transformer/moe/moe_token_permute_grad.md",
            ),
        )
        for card, target in cases:
            with self.subTest(card=card.relative_to(self.root)):
                text = card.read_text(encoding="utf-8")
                # A valid body example may now be outside the source-first display cap.
                self.assertIn((card, (card.parent / target).resolve()), self.body_invocation_pairs())
                targets = [target for target, _ in markdown_targets(text)]
                self.assertTrue(any("operators/" in target for target in targets))

    def test_api_operator_navigation_regressions(self) -> None:
        api_root = self.root / "knowledge/ops/ascendc/apis"
        positive_cases = (
            (
                api_root
                / "simd_api/basic_api/data_structures/global_tensor/"
                "set_global_buffer.md",
                "../../../../../operators/aclnn/nn/matmul/"
                "quant_batch_matmul_inplace_add_950.md",
            ),
            (
                api_root
                / "simd_api/adv_api/cube_compute/matmul_kernel/init.md",
                "../../../../../operators/aclnn/nn/matmul/"
                "sparse4to2_quant_matmul_weight_nz.md",
            ),
        )
        for card, target in positive_cases:
            with self.subTest(card=card.relative_to(self.root), target=target):
                self.assertIn((card, (card.parent / target).resolve()), self.body_invocation_pairs())

        negative_cases = (
            (
                api_root
                / "simt_api/math_functions/float_math_functions/expf.md",
                "foreach_expm1_950.md",
            ),
            (
                api_root
                / "simt_api/math_functions/float_math_functions/isfinite.md",
                "hardsigmoid_backward_950.md",
            ),
            (
                api_root
                / "simt_api/math_functions/float_math_functions/isfinite.md",
                "swiglu_group_quant_950.md",
            ),
            (
                api_root
                / "simt_api/math_functions/float_math_functions/isfinite.md",
                "exp_950.md",
            ),
            (
                api_root
                / "simd_api/basic_api/reg_vector_compute/type_conversion/cast.md",
                "logical_not_950.md",
            ),
            (
                api_root
                / "simd_api/basic_api/data_structures/global_tensor/"
                "set_l2_cache_hint.md",
                "mhc_post_950.md",
            ),
        )
        for card, target in negative_cases:
            with self.subTest(card=card.relative_to(self.root), target=target):
                self.assertNotIn(target, card.read_text(encoding="utf-8"))
                self.assertFalse(any(api == card and operator.name == target for api, operator in self.body_invocation_pairs()))

    def test_generic_guides_do_not_inherit_subsection_platform_limits(self) -> None:
        paths = (
            "knowledge/ops/ascendc/guides/getting_started/quick_start/"
            "heterogeneous_system_and_programming_model.md",
            "knowledge/ops/ascendc/guides/programming_guide/programming_model/"
            "programming_model_overview.md",
            "knowledge/ops/ascendc/guides/programming_guide/advanced_programming/"
            "hardware_implementation/basic_architecture.md",
        )
        for relative in paths:
            with self.subTest(card=relative):
                text = (self.root / relative).read_text(encoding="utf-8")
                metadata = yaml.safe_load(text.split("---", 2)[1])
                self.assertEqual("draft", metadata["status"])
                self.assertEqual([], metadata["platforms"])

    def test_ascendc_runbooks_do_not_use_legacy_sections(self) -> None:
        failures = [str(card.relative_to(self.root))
                    for card in (self.root / "knowledge/ops/ascendc/runbooks").glob("*/*.md")
                    if re.search(r"(?m)^## 遗留问题\s*$", card.read_text(encoding="utf-8"))]
        self.assertEqual([], failures)

    def test_knowledge_index_entries_have_descriptions(self) -> None:
        failures: list[str] = []
        for index in sorted((self.root / "knowledge").rglob("index.md")):
            for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), start=1):
                if line.startswith("- [") and ")：" not in line:
                    failures.append(f"{index.relative_to(self.root)}:{number}")
        self.assertEqual([], failures)

    def test_each_skill_links_its_references(self) -> None:
        failures: list[str] = []
        for skill in sorted((self.root / ".agents/skills").iterdir()):
            if not skill.is_dir():
                continue
            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
            references = skill / "references"
            if not references.exists():
                continue
            for reference in sorted(references.glob("*.md")):
                target = f"references/{reference.name}"
                if target not in skill_text:
                    failures.append(f"{skill.name}: {target}")
        self.assertEqual([], failures)

    def test_skill_frontmatter_contract(self) -> None:
        failures: list[str] = []
        for skill in sorted((self.root / ".agents/skills").iterdir()):
            if not skill.is_dir():
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            parts = text.split("---", 2)
            if len(parts) != 3 or parts[0].strip():
                failures.append(f"{skill.name}: invalid frontmatter delimiters")
                continue
            node = yaml.compose(parts[1])
            if not isinstance(node, yaml.MappingNode):
                failures.append(f"{skill.name}: frontmatter is not a mapping")
                continue
            keys = [key.value for key, _ in node.value]
            if len(keys) != len(set(keys)):
                failures.append(f"{skill.name}: duplicate frontmatter key")
                continue
            metadata = yaml.safe_load(parts[1])
            if not isinstance(metadata, dict) or set(metadata) != {"name", "description"}:
                failures.append(f"{skill.name}: frontmatter requires only name and description")
                continue
            if metadata["name"] != skill.name or not str(metadata["description"]).strip():
                failures.append(f"{skill.name}: invalid name or description")
        self.assertEqual([], failures)

    def test_unified_gate_enables_strict_source_navigation(self) -> None:
        check = (self.root / "check.sh").read_text(encoding="utf-8")
        self.assertIn("--strict-navigation", check)

    def test_unified_gate_runs_trace_runbook_contract(self) -> None:
        check = (self.root / "check.sh").read_text(encoding="utf-8")
        self.assertIn("ops-knowledge-trace-ingest/scripts/field_notes_lint.py", check)

    def test_skill_inventory_and_install_scope_are_explicit(self) -> None:
        expected = {
            "knowledge-ingest",
            "knowledge-query",
            "knowledge-lint",
            "ascendc-api-knowledge-query",
            "ops-knowledge-trace-ingest",
            "ops-knowledge-vv-ingest",
            "ops-knowledge-cv-ingest",
        }
        actual = {path.name for path in (self.root / ".agents/skills").iterdir() if path.is_dir()}
        self.assertEqual(expected, actual)
        for relative in (
            "README.md",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "docs/design_principles.md",
            "docs/user_guide.md",
            "governance/specs/skills.md",
        ):
            text = (self.root / relative).read_text(encoding="utf-8")
            self.assertIn("ops-knowledge-trace-ingest", text, relative)
            self.assertIn("ascendc-api-knowledge-query", text, relative)
        skills_spec = (self.root / "governance/specs/skills.md").read_text(encoding="utf-8")
        self.assertIn("仓内 trace producer", skills_spec)

    def test_trace_ingest_uses_current_repository_contracts(self) -> None:
        root = self.root / ".agents/skills/ops-knowledge-trace-ingest"
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.suffix in {".md", ".py"}
        )
        for forbidden in (
            "build_graph.py",
            "okf:related",
            "graph/edge_judgments.json",
            "--aggregate-only",
            "origin okf",
            "log/README.md",
            "| `verified` | bool |",
            "reference/",
            "图谱增量",
            "补反链",
            "双侧显式标注",
            "trace.curated-review.v1",
            "deprecated: true",
            "* slug.md — description",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)
        self.assertIn("local-graphs.md", text)
        self.assertNotIn("cannbot:related", text)
        self.assertIn("object/object[]", text)
        self.assertIn("trace.curated-review.v2", text)
        self.assertIn("--pre-review", text)
        self.assertIn("--staged-card", text)
        self.assertIn("staged-cards", text)
        self.assertIn("target_path", text)
        self.assertIn("publish_reviewed_cards.py", text)
        self.assertIn("agent-runtime-message", text)
        self.assertIn("sync-indexes", text)
        self.assertNotIn("per-dir materialize already done", text)
        materialize = (
            root / "scripts/materialize_trace_contract.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "--verified requires --ledger, --receipt, and --cards-root",
            materialize,
        )

    def test_knowledge_does_not_refer_to_retired_a5_card_suffix(self) -> None:
        stale = re.compile(
            r"(?:见[^\n]*_a5|_a5[^\n]*(?:卡|文件|目标)|"
            r"(?:生成|创建|没有)[^\n]*_a5|_a5[^\n]*正式卡)"
        )
        failures: list[str] = []
        for card in sorted((self.root / "knowledge").rglob("*.md")):
            for number, line in enumerate(card.read_text(encoding="utf-8").splitlines(), start=1):
                if stale.search(line):
                    failures.append(f"{card.relative_to(self.root)}:{number}")
        self.assertEqual([], failures)

    def test_skill_sources_do_not_contain_agent_vendor_metadata(self) -> None:
        vendor_metadata = sorted(
            path.relative_to(self.root).as_posix()
            for path in (self.root / ".agents/skills").glob("*/agents/*")
            if path.is_file()
        )
        self.assertEqual([], vendor_metadata)

    def test_markdown_structure(self) -> None:
        failures: list[str] = []
        for document in self.documentation_files():
            text = document.read_text(encoding="utf-8")
            lines = text.splitlines()
            fixed_archive_mirror = self.is_fixed_archive_mirror(text)
            content_start = 0
            if lines and lines[0] == "---":
                try:
                    content_start = lines.index("---", 1) + 1
                except ValueError:
                    failures.append(f"{document.relative_to(self.root)}: unterminated frontmatter")
                    continue
            first = next((line for line in lines[content_start:] if line.strip()), "")
            if not first.startswith("# "):
                failures.append(f"{document.relative_to(self.root)}: first content heading is not H1")
            if (
                sum(line.startswith("```") for line in lines) % 2
                and not fixed_archive_mirror
            ):
                failures.append(f"{document.relative_to(self.root)}: unbalanced fenced code blocks")
            whitespace_lines = lines
            if fixed_archive_mirror:
                mirror = self.load_module(
                    self.root / ".agents/skills/knowledge-ingest/scripts/fixed_archive_docs.py",
                    "documentation_mirror_whitespace",
                )
                _, navigation = mirror.split_link_suffix(text)
                whitespace_lines = lines[:content_start] + (navigation.splitlines() if navigation else [])
            if any(line != line.rstrip() for line in whitespace_lines):
                failures.append(f"{document.relative_to(self.root)}: trailing whitespace")
        self.assertEqual([], failures)

    def test_external_docs_do_not_expose_skill_script_cli(self) -> None:
        forbidden = (
            "knowledge_query.py",
            "knowledge_ingest.py",
            "knowledge_lint.py",
            "build_graph.py",
            "quick_validate.py",
        )
        failures: list[str] = []
        for document in self.external_documentation_files():
            text = document.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    failures.append(f"{document.relative_to(self.root)}: {token}")
        self.assertEqual([], failures)

    def test_repository_docs_do_not_describe_an_import_origin(self) -> None:
        forbidden = ("NPU-Kernel-Wiki", "NPU Kernel Wiki", "迁移 pilot", "首批迁移", "旧仓")
        failures: list[str] = []
        for document in self.external_documentation_files():
            # Logs preserve actual source/audit history, not repository positioning.
            if document.is_relative_to(self.root / "logs"):
                continue
            text = document.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    failures.append(f"{document.relative_to(self.root)}: {token}")
        self.assertEqual([], failures)

    def test_document_archive_download_refresh_and_failure_preserve_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy2(self.root / "get_resources.sh", root / "get_resources.sh")
            registry = root / "governance/schemas/registries.yaml"
            registry.parent.mkdir(parents=True)
            registry.write_text("local_sources:\n  cann_docs_raw:\n    archive_url: https://example.invalid/current.tar.gz\n")
            repair = root / ".agents/skills/knowledge-ingest/scripts/repair_fixed_archive.py"
            repair.parent.mkdir(parents=True)
            repair.write_text("raise SystemExit(0)\n")
            source = root / "input/asc-devkit/docs/zh/example.md"
            source.parent.mkdir(parents=True)
            archive = root / "input.tar.gz"
            def package(text):
                source.write_text(text)
                with tarfile.open(archive, "w:gz") as stream:
                    stream.add(root / "input/asc-devkit", arcname="asc-devkit")
            binary = root / "bin"
            binary.mkdir()
            curl = binary / "curl"
            curl.write_text('#!/usr/bin/env bash\nset -eu\nwhile [[ "$1" != "-o" ]]; do shift; done\ncp "$TEST_DOCUMENT_ARCHIVE" "$2"\n')
            curl.chmod(0o755)
            env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                   "TEST_DOCUMENT_ARCHIVE": str(archive)}
            def fetch(*args):
                return subprocess.run(["bash", str(root / "get_resources.sh"), "--docs", *args],
                                      env=env, capture_output=True, text=True)
            package("first publication\n")
            result = fetch()
            self.assertEqual(0, result.returncode, result.stderr)
            restored = root / "cann-docs-raw/asc-devkit/docs/zh/example.md"
            marker = root / "cann-docs-raw/.complete"
            self.assertEqual("first publication\n", restored.read_text())
            self.assertIn("archive_url=https://example.invalid/current.tar.gz", marker.read_text())
            package("changed daily publication\n")
            result = fetch()
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("first publication\n", restored.read_text())
            result = fetch("--refresh")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("changed daily publication\n", restored.read_text())
            archive.write_bytes(b"broken archive")
            result = fetch("--refresh")
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("changed daily publication\n", restored.read_text())
            marker.unlink()
            result = fetch()
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Refusing to overwrite incomplete", result.stderr)

    def test_document_archive_reuses_legacy_marker_without_content_hash_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy2(self.root / "get_resources.sh", root / "get_resources.sh")
            registry = root / "governance/schemas/registries.yaml"
            registry.parent.mkdir(parents=True)
            registry.write_text("local_sources:\n  cann_docs_raw:\n    archive_url: https://example.invalid/current.tar.gz\n")
            source = root / "cann-docs-raw/docs/example.md"
            source.parent.mkdir(parents=True)
            source.write_text("changed content\n")
            marker = root / "cann-docs-raw/.complete"
            marker.write_text("archive_sha256=old\ntree_sha256=old\n")
            result = subprocess.run(["bash", str(root / "get_resources.sh"), "--docs"],
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("changed content\n", source.read_text())
            self.assertIn("archive_url=https://example.invalid/current.tar.gz", marker.read_text())
            self.assertNotIn("sha256", marker.read_text())

    def test_document_publisher_repairs_allow_changed_counts_but_reject_unknown_tokens(self) -> None:
        module = self.load_module(self.root / ".agents/skills/knowledge-ingest/scripts/repair_fixed_archive.py", "review_repair")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = "api/SIMD-API/tensor_api/tensor/tensor.md"
            source = root / relative
            source.parent.mkdir(parents=True)
            prefix = module.UPSTREAM_BASE + str(Path(relative).parent) + "/"
            source.write_text("# Example\n\n```cpp\n" + (prefix + "constexpr int x = 1;\n") * 43 + "```\n")
            self.assertEqual(43, module.repair_tree(root, write=True))
            self.assertEqual(0, module.repair_tree(root, write=False))
            self.assertEqual(0, module.repair_tree(root, write=True))
            source.write_text("# Example\n\n```cpp\n" + prefix + "UnknownToken x;\n```\n")
            before = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "current-directory URLs"):
                module.repair_tree(root, write=True)
            self.assertEqual(before, source.read_bytes())

    def test_ingest_distinguishes_git_and_fixed_archive_reference(self) -> None:
        skill = (
            self.root / ".agents/skills/knowledge-ingest/SKILL.md"
        ).read_text(encoding="utf-8")
        onboarding = (
            self.root / ".agents/skills/knowledge-ingest/references/source-onboarding.md"
        ).read_text(encoding="utf-8")
        reference = (
            self.root / ".agents/skills/knowledge-ingest/references/official-reference-ingest.md"
        ).read_text(encoding="utf-8")
        incremental = (
            self.root / ".agents/skills/knowledge-ingest/references/incremental-sync.md"
        ).read_text(encoding="utf-8")
        version = (
            self.root / ".agents/skills/knowledge-ingest/references/version-upgrade.md"
        ).read_text(encoding="utf-8")
        spec = (self.root / "governance/specs/skills.md").read_text(encoding="utf-8")

        self.assertIn("Git Reference 批次", skill)
        self.assertIn("文档归档批次不生成 inventory、ledger 或 verification receipt", onboarding)
        self.assertIn("文档归档批次不生成 inventory、ledger 或 verification receipt", reference)
        self.assertIn("文档归档不走本流程", incremental)
        self.assertIn("文档归档刷新后的结构与内容变更", version)
        self.assertIn("文档归档刷新前先保留旧来源", version)
        self.assertIn("文档归档批次按 Registry 的官方 URL 获取", spec)

    def test_documented_tags_are_registered(self) -> None:
        registered = set(self.registries["tags"])
        locations = [
            self.root / "CONTRIBUTING.md",
            self.root / "governance/specs/frontmatter.md",
            self.root / ".agents/skills/knowledge-ingest/SKILL.md",
            self.root / ".agents/skills/knowledge-query/SKILL.md",
            self.root / ".agents/skills/knowledge-lint/SKILL.md",
        ]
        documented = set()
        for path in locations:
            documented.update(TAG_RE.findall(path.read_text(encoding="utf-8")))
        self.assertEqual(set(), documented - registered)

    def test_frontmatter_spec_lists_every_source_role(self) -> None:
        schema = json.loads(
            (self.root / "governance/schemas/frontmatter.schema.json").read_text(encoding="utf-8")
        )
        roles = schema["properties"]["sources"]["items"]["properties"]["role"]["enum"]
        spec = (self.root / "governance/specs/frontmatter.md").read_text(encoding="utf-8")
        self.assertEqual([], [role for role in roles if f"`{role}`" not in spec])

    def test_authoritative_frontmatter_docs_cover_profiles(self) -> None:
        profiles = yaml.safe_load(
            (self.root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
        )
        documents = [
            self.root / "governance/specs/frontmatter.md",
            self.root / ".agents/skills/knowledge-ingest/references/frontmatter-profiles.md",
        ]
        for document in documents:
            text = document.read_text(encoding="utf-8")
            with self.subTest(document=document.name):
                for field in profiles["common_required"]:
                    self.assertIn(f"`{field}`", text)
                for profile in profiles["profiles"]:
                    self.assertTrue(
                        f"`{profile}`" in text or f"`{profile}/`" in text,
                        f"{document} does not document profile {profile}",
                    )

    def test_frontmatter_spec_covers_schema_fields_and_enums(self) -> None:
        schema = json.loads(
            (self.root / "governance/schemas/frontmatter.schema.json").read_text(encoding="utf-8")
        )
        spec = (self.root / "governance/specs/frontmatter.md").read_text(encoding="utf-8")
        missing_fields = [field for field in schema["properties"] if f"`{field}`" not in spec]
        self.assertEqual([], missing_fields)
        for field in ("status",):
            with self.subTest(field=field):
                self.assertEqual(
                    [],
                    [value for value in schema["properties"][field]["enum"] if f"`{value}`" not in spec],
                )

    def test_schema_spec_covers_path_contract_identifiers(self) -> None:
        path_spec = (self.root / "governance/specs/paths.md").read_text(encoding="utf-8")
        schema_spec = (self.root / "governance/specs/schemas.md").read_text(encoding="utf-8")
        profiles = yaml.safe_load(
            (self.root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
        )
        for section in ("domains", "technologies", "scopes"):
            with self.subTest(section=section):
                self.assertIn(f"`{section}`", schema_spec)
                self.assertEqual(
                    [],
                    [item for item in self.registries[section] if f"`{item}`" not in path_spec],
                )
        self.assertEqual(
            [],
            [profile for profile in profiles["profiles"] if f"`{profile}" not in path_spec],
        )
        path_values: list[str] = []
        for values in self.registries["paths"].values():
            if isinstance(values, dict):
                path_values.extend(values)
                path_values.extend(
                    value for nested in values.values() for value in nested
                )
            else:
                path_values.extend(values)
        self.assertEqual(
            [], [value for value in path_values if f"`{value}`" not in path_spec]
        )

    @staticmethod
    def load_module(path: Path, name: str):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def parser_options(parser: ArgumentParser) -> set[str]:
        result: set[str] = set()
        for action in parser._actions:
            result.update(option for option in action.option_strings if option.startswith("--"))
            if isinstance(action, _SubParsersAction):
                for child in action.choices.values():
                    result.update(DocumentationContractTests.parser_options(child))
        return result

    def test_skill_docs_only_use_supported_cli_flags(self) -> None:
        cases = (
            (
                "ingest",
                (
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/knowledge_graph.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/reference_inventory.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/fixed_archive_docs.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/api_operator_links.py",
                        "parser",
                    ),
                ),
                self.root / ".agents/skills/knowledge-ingest",
            ),
            (
                "query",
                (
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
                        "build_parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/knowledge_index.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/retrieval_state.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/retrieval_outcome.py",
                        "parser",
                    ),
                ),
                self.root / ".agents/skills/knowledge-query",
            ),
            (
                "ascendc_api",
                (
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
                        "build_parser",
                    ),
                    (
                        self.root / ".agents/skills/ascendc-api-knowledge-query/scripts/resolve_resources.py",
                        "build_parser",
                    ),
                ),
                self.root / ".agents/skills/ascendc-api-knowledge-query",
            ),
            (
                "lint",
                (
                    (
                        self.root / ".agents/skills/knowledge-lint/scripts/knowledge_lint.py",
                        "build_parser",
                    ),
                ),
                self.root / ".agents/skills/knowledge-lint",
            ),
        )
        for name, parsers, docs_root in cases:
            supported: set[str] = set()
            if name == "ingest":
                resource_help = subprocess.run(
                    ["bash", str(self.root / "get_resources.sh"), "--help"],
                    check=True, capture_output=True, text=True,
                )
                supported.update(re.findall(r"--[a-z][a-z0-9-]*", resource_help.stdout))
            for index, (script, parser_factory) in enumerate(parsers):
                module = self.load_module(script, f"documentation_{name}_{index}")
                supported.update(self.parser_options(getattr(module, parser_factory)()))
            documented: set[str] = set()
            for document in docs_root.rglob("*.md"):
                documented.update(re.findall(r"--[a-z][a-z0-9-]*", document.read_text(encoding="utf-8")))
            with self.subTest(skill=name):
                self.assertEqual(set(), documented - supported)

    def test_query_derives_trust_tier_from_okf_verified_events(self) -> None:
        module = self.load_module(
            self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
            "documentation_query_trust",
        )
        self.assertEqual("unverified", module.trust_tier({}))
        self.assertEqual(
            "machine-confirmed",
            module.trust_tier({"verified": {"by": "process:ci", "at": "2026-08-15T08:00:00Z"}}),
        )
        self.assertEqual(
            "human-reviewed",
            module.trust_tier(
                {
                    "verified": [
                        {"by": "process:ci", "at": "2026-08-15T08:00:00Z"},
                        {"by": "human:reviewer", "at": "2026-08-15T09:00:00Z"},
                    ]
                }
            ),
        )

    def test_agent_instruction_files_match(self) -> None:
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(agents, claude)


if __name__ == "__main__":
    unittest.main()
