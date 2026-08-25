#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  echo "usage: $0 <python-entrypoint> [args...]" >&2
  exit 2
fi

python_bin="${KNOWLEDGE_CHECK_PYTHON:-python3}"

if [[ -n "${ATOMGIT_STEP_SUMMARY:-}" ]]; then
  "$python_bin" "$@" | tee -a "$ATOMGIT_STEP_SUMMARY"
else
  exec "$python_bin" "$@"
fi
