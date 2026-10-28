# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Validate optional applicability metadata with the shared Scope contract."""

from __future__ import annotations

from ..knowledge import Issue


def check(contract, document, context) -> list[Issue]:
    del context
    if document.metadata is None or document.path_info is None:
        return []
    if "scope" not in document.metadata:
        return []
    try:
        value = contract.scope_registry.normalize(document.metadata["scope"])
        info = document.path_info
        binding = f"{info.domain}/{info.route}"
        if not contract.scope_registry.applies_to(value["schema"], info.domain, info.route):
            raise ValueError(f"scope schema {value['schema']} is not registered for {binding}")
    except ValueError as exc:
        return [Issue("scope.invalid", str(exc))]
    return []
