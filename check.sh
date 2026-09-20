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

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_root"

python3 .agents/skills/knowledge-lint/scripts/knowledge_lint.py \
  --knowledge-root . --strict-navigation
python3 .agents/skills/knowledge-ingest/scripts/knowledge_ingest.py \
  --knowledge-root . sync-indexes --check
python3 .agents/skills/knowledge-query/scripts/knowledge_index.py \
  --knowledge-root . build
python3 .agents/skills/knowledge-query/scripts/knowledge_index.py \
  --knowledge-root . verify --level full
python3 evals/run_retrieval.py
python3 -m unittest discover -s evals -p 'test_*.py'
python3 -m unittest discover -s .agents/skills/ops-knowledge-trace-ingest/scripts -p 'test_*.py'
python3 .agents/skills/ops-knowledge-trace-ingest/scripts/field_notes_lint.py
ruff check .agents/skills governance evals
bash -n install.sh check.sh get_resources.sh

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  python3 .agents/skills/knowledge-ingest/scripts/fixed_archive_docs.py \
    --knowledge-root . diff-check
fi
