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

# Restore fixed documentation and commit-pinned operator source worktrees.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RESOURCE_SCOPE="${1:---all}"
if [[ "$#" -gt 1 ]]; then
  echo "usage: get_resources.sh [--all|--docs|--code]" >&2
  exit 2
fi
case "$RESOURCE_SCOPE" in
  --all|--docs|--code) ;;
  --help|-h)
    echo "usage: get_resources.sh [--all|--docs|--code]"
    exit 0
    ;;
  *) echo "unknown resource scope: $RESOURCE_SCOPE" >&2; exit 2 ;;
esac

fetch_documents() (
URL="https://ascend-ci.obs.cn-north-4.myhuaweicloud.com/package/doc/Ascend-cann-docs-examples.tar.gz"
TARGET_DIR="$SCRIPT_DIR/cann-docs-raw"
REGISTRIES="$SCRIPT_DIR/governance/schemas/registries.yaml"
TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cannbot-docs.XXXXXX")
TMP_TAR="$TEMP_DIR/Ascend-cann-docs-examples.tar.gz"
EXTRACT_DIR="$TEMP_DIR/extracted"
REPAIR_SCRIPT="$SCRIPT_DIR/.agents/skills/knowledge-ingest/scripts/repair_fixed_archive.py"

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

if [ ! -f "$REGISTRIES" ]; then
  echo "Missing governance registry: $REGISTRIES" >&2
  exit 1
fi

readarray -t EXPECTED_HASHES < <(python3 - "$REGISTRIES" <<'PY'
import sys
from pathlib import Path

import yaml

registry = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
source = registry["local_sources"]["cann_docs_raw"]
for name in ("archive_sha256", "tree_sha256"):
    value = source[name]
    if not isinstance(value, str) or len(value) != 64:
        raise SystemExit(f"invalid local_sources.cann_docs_raw.{name}")
    print(value)
PY
)
EXPECTED_SHA256=${EXPECTED_HASHES[0]}
EXPECTED_TREE_SHA256=${EXPECTED_HASHES[1]}

tree_sha256() {
  python3 - "$1" <<'PY'
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
digest = hashlib.sha256()
files = sorted(
    (path for path in root.rglob("*") if path.is_file() and path.name != ".complete"),
    key=lambda path: path.relative_to(root).as_posix(),
)
for path in files:
    relative = path.relative_to(root).as_posix().encode("utf-8")
    digest.update(relative)
    digest.update(b"\0")
    digest.update(hashlib.sha256(path.read_bytes()).digest())
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

repair_published_code_links() {
  local directory=$1
  local source_root="$directory/asc-devkit/docs/zh"
  if [ ! -d "$source_root" ]; then
    return
  fi
  if [ ! -f "$REPAIR_SCRIPT" ]; then
    echo "Missing fixed archive repair script: $REPAIR_SCRIPT" >&2
    exit 1
  fi
  python3 "$REPAIR_SCRIPT" sync --source-root "$source_root"
}

write_complete_marker() {
  local directory=$1
  printf 'archive_sha256=%s\ntree_sha256=%s\n' \
    "$EXPECTED_SHA256" "$EXPECTED_TREE_SHA256" > "$directory/.complete"
}

if [ -e "$TARGET_DIR" ]; then
  if [ -f "$TARGET_DIR/.complete" ] \
    && grep -Fqx "archive_sha256=$EXPECTED_SHA256" "$TARGET_DIR/.complete"; then
    repair_published_code_links "$TARGET_DIR"
    echo "Verifying the extracted documentation tree ..."
    ACTUAL_TREE_SHA256=$(tree_sha256 "$TARGET_DIR")
    if [ "$ACTUAL_TREE_SHA256" = "$EXPECTED_TREE_SHA256" ]; then
      write_complete_marker "$TARGET_DIR"
      echo "cann-docs-raw/ matches the registered archive. Skipping download."
      exit 0
    fi
    echo "Extracted tree SHA-256 mismatch!" >&2
    echo "  expected: $EXPECTED_TREE_SHA256" >&2
    echo "  actual:   $ACTUAL_TREE_SHA256" >&2
    exit 1
  fi
  echo "Refusing to overwrite incomplete source directory: $TARGET_DIR" >&2
  echo "Move or remove that exact directory after inspecting it, then retry." >&2
  exit 1
fi

echo "Downloading Ascend-cann-docs-examples.tar.gz ..."
curl -fSL -o "$TMP_TAR" "$URL"

echo "Verifying SHA-256 ..."
ACTUAL_SHA256=$(sha256sum "$TMP_TAR" | awk '{print $1}')
if [ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]; then
  echo "SHA-256 mismatch!"
  echo "  expected: $EXPECTED_SHA256"
  echo "  actual:   $ACTUAL_SHA256"
  exit 1
fi
echo "SHA-256 verified: $ACTUAL_SHA256"

echo "Extracting to $TARGET_DIR ..."
mkdir -p "$EXTRACT_DIR"
tar -xzf "$TMP_TAR" -C "$EXTRACT_DIR"

repair_published_code_links "$EXTRACT_DIR"

ACTUAL_TREE_SHA256=$(tree_sha256 "$EXTRACT_DIR")
if [ "$ACTUAL_TREE_SHA256" != "$EXPECTED_TREE_SHA256" ]; then
  echo "Extracted tree SHA-256 mismatch!" >&2
  echo "  expected: $EXPECTED_TREE_SHA256" >&2
  echo "  actual:   $ACTUAL_TREE_SHA256" >&2
  exit 1
fi

write_complete_marker "$EXTRACT_DIR"
mv "$EXTRACT_DIR" "$TARGET_DIR"
echo "Done. Documentation package extracted to $TARGET_DIR/"
)

if [[ "$RESOURCE_SCOPE" != "--code" ]]; then
  fetch_documents
fi
if [[ "$RESOURCE_SCOPE" != "--docs" ]]; then
  python3 "$SCRIPT_DIR/.agents/skills/knowledge-ingest/scripts/source_resources.py" \
    --knowledge-root "$SCRIPT_DIR" fetch
fi
