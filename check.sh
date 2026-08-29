#!/usr/bin/env bash
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
python3 -m unittest discover -s .agents/skills/knowledge-ingest/tests -p 'test_*.py'
python3 -m unittest discover -s .agents/skills/ops-knowledge-trace-ingest/scripts -p 'test_*.py'
python3 .agents/skills/ops-knowledge-trace-ingest/scripts/field_notes_lint.py
ruff check .agents/skills governance evals
bash -n init.sh check.sh fetch-cann-docs.sh
if [[ -f artifacts/graphs/edge_judgments.json ]]; then
  python3 .agents/skills/knowledge-ingest/scripts/knowledge_graph.py \
    --knowledge-root . build
  python3 .agents/skills/knowledge-ingest/scripts/knowledge_graph.py \
    --knowledge-root . viz
  python3 .agents/skills/knowledge-ingest/scripts/knowledge_graph.py \
    --knowledge-root . verify
elif [[ -e artifacts/graphs/candidates.json \
  || -e artifacts/graphs/graph.json \
  || -d artifacts/graphs/judgment_shards \
  || -d artifacts/graphs/reviews ]]; then
  echo "error: graph rebuild artifacts exist without an aggregated judgment cache" >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
fi
