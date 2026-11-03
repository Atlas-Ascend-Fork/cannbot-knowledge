#!/usr/bin/env bash
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------
# 平台/K8s 容器启动入口：确保检索索引存在（缺失或过期时在容器内重建），随后以 HTTP 传输启动
# MCP 服务器。索引构建或校验失败时直接退出，保持服务 fail-closed。工作目录无关，脚本自行定位仓库根。
#
# 索引采纳（index_adopt.py）：全新克隆会重写所有文件的 mtime，卷上持久化的索引即使内容逐字节
# 一致也会被 quick verify 判为 stale。verify 失败时先做内容级采纳——逐卡 sha256 核验一致后把
# mtime 修回索引记录值，跳过约 4 分钟的重建；任何真实内容/集合差异仍走重建，fail-closed 不降级。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX_CLI="${REPO_ROOT}/.agents/skills/knowledge-query/scripts/knowledge_index.py"
ADOPT_CLI="${REPO_ROOT}/mcp-server/index_adopt.py"

cd "${REPO_ROOT}"
if ! python3 "${INDEX_CLI}" --knowledge-root "${REPO_ROOT}" verify; then
    echo "[platform-start] verify failed; attempting content-aware index adoption" >&2
    if python3 "${ADOPT_CLI}" --knowledge-root "${REPO_ROOT}"; then
        if python3 "${INDEX_CLI}" --knowledge-root "${REPO_ROOT}" verify; then
            echo "[platform-start] persisted index adopted; skipping rebuild" >&2
        else
            echo "[platform-start] verify still failing after adoption; rebuilding in container" >&2
            python3 "${INDEX_CLI}" --knowledge-root "${REPO_ROOT}" build
        fi
    else
        echo "[platform-start] index not adoptable; rebuilding in container" >&2
        python3 "${INDEX_CLI}" --knowledge-root "${REPO_ROOT}" build
    fi
fi

exec python3 "${REPO_ROOT}/mcp-server/server.py" --transport http
