#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_root"

mirror_args=()
if [[ -n "${CANNBOT_SKILL_MIRROR:-}" ]]; then
  mirror_args=(--skill-mirror "$CANNBOT_SKILL_MIRROR")
fi

python3 .agents/skills/knowledge-lint/scripts/knowledge_lint.py \
  --knowledge-root . "${mirror_args[@]}"
python3 .agents/skills/knowledge-query/scripts/knowledge_index.py \
  --knowledge-root . build
python3 .agents/skills/knowledge-query/scripts/knowledge_index.py \
  --knowledge-root . verify --level full
python3 evals/run_retrieval.py
python3 -m unittest discover -s evals -p 'test_*.py'
python3 -m unittest discover -s .agents/skills/knowledge-ingest/tests -p 'test_*.py'
ruff check .agents/skills governance evals
bash -n init.sh check.sh
python3 .agents/skills/knowledge-ingest/scripts/build_graph.py --knowledge-root .

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
fi
