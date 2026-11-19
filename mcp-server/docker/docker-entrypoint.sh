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
# 容器启动初始化：校验知识根、确保检索索引存在且未过期（必要时在容器内重建），修正卷属主后
# 以非特权用户启动 MCP 服务器；任何校验或构建失败都让容器退出，保持服务 fail-closed。

set -euo pipefail

REPO_ROOT="${CANNBOT_KNOWLEDGE_ROOT:-/data/repo}"
LOG_DIR="${CANNBOT_MCP_LOG_DIR:-/data/logs}"
# Auth state (device/authcode sessions, API keys, the signing key, the
# StateStore sqlite) must survive container restarts: pin it to the auth
# volume instead of the container-local HOME, which is wiped on recreate.
# CANNBOT_MCP_AUTH_SECRET (tokens.env) takes precedence when set; with it,
# the signing key is env-derived and tokens survive even image rebuilds.
AUTH_DIR="${CANNBOT_MCP_AUTH_DIR:-/data/auth}"
# The JWT signing key (auth.key) is written under Path.home(); setpriv only
# changes the uid, not HOME, so without pinning it the server would try
# /root/.local/... as uid 1000, fail, and fall back to an ephemeral key —
# every restart would invalidate all issued tokens. Pin HOME inside the
# auth volume so the key file persists with it.
RUN_HOME="${AUTH_DIR}/home"
INDEX_CLI="${REPO_ROOT}/.agents/skills/knowledge-query/scripts/knowledge_index.py"
SERVER="${REPO_ROOT}/mcp-server/server.py"
ARTIFACTS_DIR="${REPO_ROOT}/artifacts"
INDEX_FILE="${ARTIFACTS_DIR}/indexes/knowledge.sqlite3"
RUN_UID=1000
RUN_GID=1000

if [ ! -d "${REPO_ROOT}/knowledge" ] || [ -z "$(ls -A "${REPO_ROOT}/knowledge")" ]; then
    echo "[docker-entrypoint] knowledge/ is missing or empty under ${REPO_ROOT}; check the KNOWLEDGE_ROOT mount" >&2
    exit 1
fi

mkdir -p "${LOG_DIR}" "${ARTIFACTS_DIR}" "${AUTH_DIR}" "${RUN_HOME}"
rm -f "${ARTIFACTS_DIR}/indexes/"*.tmp

if [ ! -f "${INDEX_FILE}" ] || ! python3 "${INDEX_CLI}" --knowledge-root "${REPO_ROOT}" verify >/dev/null 2>&1; then
    echo "[docker-entrypoint] knowledge index missing or stale; rebuilding in container" >&2
    python3 "${INDEX_CLI}" --knowledge-root "${REPO_ROOT}" build
fi

chown -R "${RUN_UID}:${RUN_GID}" "${LOG_DIR}" "${ARTIFACTS_DIR}" "${AUTH_DIR}"
export CANNBOT_MCP_AUTH_DB="${CANNBOT_MCP_AUTH_DB:-${AUTH_DIR}/auth.db}"

echo "[docker-entrypoint] starting cannbot-knowledge mcp server (uid ${RUN_UID})" >&2
exec setpriv --reuid="${RUN_UID}" --regid="${RUN_GID}" --clear-groups \
    env HOME="${RUN_HOME}" \
    python3 "${SERVER}" --transport http
