# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

FROM python:3.11-slim

ARG PIP_INDEX_URL=https://pypi.org/simple

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN pip install --no-cache-dir --index-url "${PIP_INDEX_URL}" \
        "mcp>=2,<3" "uvicorn>=0.23,<1" "pyyaml>=6,<7" \
    && chmod 0755 /usr/local/bin/docker-entrypoint.sh

ENV CANNBOT_MCP_HOST=0.0.0.0 \
    CANNBOT_MCP_PORT=8090 \
    CANNBOT_KNOWLEDGE_ROOT=/data/repo \
    CANNBOT_MCP_LOG_DIR=/data/logs \
    CANNBOT_MCP_SUBPROC_TIMEOUT=60 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8090

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
