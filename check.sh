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

# Git hooks export paths for the invoking repository. Child fixtures and
# resource checkouts must discover their own Git directories.
if ! git_local_env_vars="$(git rev-parse --local-env-vars)"; then
  echo "Cannot enumerate Git repository-local environment." >&2
  exit 1
fi
while IFS= read -r git_env_var; do
  unset "$git_env_var"
done <<< "$git_local_env_vars"
unset git_env_var git_local_env_vars

# Vendored dependency copies are upstream-trimmed trees whose internal style
# is owned by cann/cannbot-skills; syncing upstream replaces them wholesale,
# so repository lint rules must not gate them.
python3 .agents/skills/knowledge-lint/scripts/knowledge_lint.py \
  --knowledge-root . --strict-navigation
python3 .agents/skills/knowledge-ingest/scripts/knowledge_ingest.py \
  --knowledge-root . sync-indexes --check
python3 .agents/skills/knowledge-query/scripts/knowledge_index.py \
  --knowledge-root . build
python3 .agents/skills/knowledge-query/scripts/knowledge_index.py \
  --knowledge-root . verify --level full
# Gate recall/ranking by aggregate targets; query and filter contract errors still fail.
python3 evals/run_retrieval.py --quality-gate
python3 evals/run_retrieval.py --cases evals/model_inference_scope_cases.yaml
python3 evals/run_retrieval.py --cases evals/inference_skill_migration_cases.yaml
python3 evals/run_retrieval.py --cases evals/runtime_api_selection_cases.yaml
python3 -m unittest discover -s evals -p 'test_*.py'
python3 -m unittest discover -s .agents/skills/ops-knowledge-trace-ingest/scripts -p 'test_*.py'
python3 -m unittest discover -s .agents/skills/model-knowledge-trace-ingest/scripts -p 'test_*.py'
python3 .agents/skills/ops-knowledge-trace-ingest/scripts/field_notes_lint.py
# ruff 的显式路径列表把 vendored 依赖副本（gitcode-issue-handler、gitcode-toolkit）
# 排除在仓库风格门禁外：它们是上游裁剪副本，风格归上游仓所有，同步时整体替换。
ruff_paths=(governance evals)
for skill_dir in .agents/skills/*/; do
  case "$skill_dir" in
    .agents/skills/gitcode-issue-handler/|.agents/skills/gitcode-toolkit/) ;;
    *) ruff_paths+=("$skill_dir") ;;
  esac
done
ruff check "${ruff_paths[@]}"
bash -n install.sh check.sh get_resources.sh

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  python3 .agents/skills/knowledge-ingest/scripts/fixed_archive_docs.py \
    --knowledge-root . diff-check
fi
