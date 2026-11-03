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

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDES = ROOT / "knowledge/ops/catlass/guides"
CATLASS_KNOWLEDGE = ROOT / "knowledge/ops/catlass"


def test_design_reference_selects_one_architecture_ruleset() -> None:
    index = (GUIDES / "index.md").read_text(encoding="utf-8")
    assert not (GUIDES / "stage_design_rules.md").exists()
    for product, filename in (
        ("Atlas A2系列产品和Atlas A3系列产品", "stage_design_atlas_a2_a3.md"),
        ("Ascend 950PR&950DT系列产品", "stage_design_ascend950.md"),
    ):
        assert product in index
        assert f"]({filename})" in index
        assert (GUIDES / filename).is_file()


def test_architecture_rule_numbers_are_continuous() -> None:
    for filename in ("stage_design_atlas_a2_a3.md", "stage_design_ascend950.md"):
        text = (GUIDES / filename).read_text(encoding="utf-8")
        headings = [int(value) for value in re.findall(r"^### R(\d{2}) ", text, re.MULTILINE)]
        assert headings == list(range(1, len(headings) + 1))


def test_precision_policy_remains_shared_reference() -> None:
    precision = (GUIDES / "precision_policy.md").read_text(encoding="utf-8")
    assert "02 标杆生成、04 定向精度验证和 05 全量验收" in precision


def test_catlass_knowledge_does_not_reference_removed_workflow_fields() -> None:
    references = {
        field: [
            path.relative_to(ROOT).as_posix()
            for path in CATLASS_KNOWLEDGE.rglob("*.md")
            if field in path.read_text(encoding="utf-8")
        ]
        for field in ("resume_from", "validation_scope")
    }
    assert references == {"resume_from": [], "validation_scope": []}


def test_sparse_flash_mla_query_is_scoped_to_target_architecture() -> None:
    workflow = (
        CATLASS_KNOWLEDGE
        / "operators/direct/transformer/attention/sparse_flash_mla_workflow.md"
    ).read_text(encoding="utf-8")
    assert "--family sparse_flash_mla --arch atlas_a2_a3" in workflow
