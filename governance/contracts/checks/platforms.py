# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Platform scope checks."""

from __future__ import annotations

from ..knowledge import Contract, Issue


def check(contract: Contract, document, context) -> list[Issue]:
    del context
    if document.metadata is None or document.path_info is None:
        return []
    if document.path_info.card_type == "glossaries":
        return []
    platforms = document.metadata.get("platforms")
    if not isinstance(platforms, list) or not all(
        isinstance(item, str) for item in platforms
    ):
        return []
    issues: list[Issue] = []
    if not platforms and document.metadata.get("status") in {"stable", "deprecated"}:
        issues.append(
            Issue("platform.unknown", "empty platforms requires status draft")
        )
    if "agnostic" in platforms and len(platforms) != 1:
        issues.append(
            Issue(
                "platform.agnostic",
                "agnostic cannot be combined with concrete platforms",
            )
        )
    for platform in platforms:
        if platform not in contract.platforms:
            issues.append(
                Issue("platform.unknown", f"unregistered platform: {platform}")
            )
    return issues
