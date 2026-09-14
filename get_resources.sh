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

# Restore rolling documentation and commit-pinned operator source worktrees.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RESOURCE_SCOPE="--all"
REFRESH_DOCS=false
usage() { echo "usage: get_resources.sh [--all|--docs|--code] [--refresh]"; }
for option in "$@"; do
  case "$option" in
    --all|--docs|--code) RESOURCE_SCOPE="$option" ;;
    --refresh) REFRESH_DOCS=true ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown resource option: $option" >&2; usage >&2; exit 2 ;;
  esac
done
if [[ "$RESOURCE_SCOPE" == "--code" && "$REFRESH_DOCS" == "true" ]]; then
  echo "--refresh applies only to documentation" >&2
  exit 2
fi

fetch_documents() (
TARGET_DIR="$SCRIPT_DIR/cann-docs-raw"
REGISTRIES="$SCRIPT_DIR/governance/schemas/registries.yaml"
REPAIR_SCRIPT="$SCRIPT_DIR/.agents/skills/knowledge-ingest/scripts/repair_fixed_archive.py"
URL=$(python3 - "$REGISTRIES" <<'PYTHON'
import re
import sys
from pathlib import Path
import yaml
source = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))["local_sources"]["cann_docs_raw"]
url = source.get("archive_url")
if not isinstance(url, str) or not re.fullmatch(r"https://[^\s/?#@]+/[^\s#]+", url):
    raise SystemExit("local_sources.cann_docs_raw requires an HTTPS archive_url")
print(url)
PYTHON
)

repair_published_code_links() {
  local source_root="$1/asc-devkit/docs/zh"
  [[ -d "$source_root" ]] || return 0
  python3 "$REPAIR_SCRIPT" sync --source-root "$source_root"
}
write_complete_marker() {
  printf 'archive_url=%s\nprepared_at=%s\n' "$URL" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$1/.complete"
}

if [[ -e "$TARGET_DIR" || -L "$TARGET_DIR" ]]; then
  if [[ -L "$TARGET_DIR" || ! -d "$TARGET_DIR" || -L "$TARGET_DIR/.complete" || ! -f "$TARGET_DIR/.complete" ]]; then
    echo "Refusing to overwrite incomplete source directory: $TARGET_DIR" >&2
    exit 1
  fi
  # Older completed caches recorded hashes. They remain reusable without hash checks.
  if ! grep -Fqx "archive_url=$URL" "$TARGET_DIR/.complete" \
     && ! grep -q '^archive_sha256=' "$TARGET_DIR/.complete"; then
    echo "Documentation source URL does not match Registry: $TARGET_DIR" >&2
    exit 1
  fi
  if [[ "$REFRESH_DOCS" != "true" ]]; then
    repair_published_code_links "$TARGET_DIR"
    write_complete_marker "$TARGET_DIR"
    echo "Reusing completed cann-docs-raw/. Use --docs --refresh to download current documents."
    exit 0
  fi
fi

TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cannbot-docs.XXXXXX")
trap 'rm -rf "$TEMP_DIR"' EXIT
TMP_TAR="$TEMP_DIR/Ascend-cann-docs-examples.tar.gz"
EXTRACT_DIR="$TEMP_DIR/extracted"
echo "Downloading current Ascend documentation ..."
curl -fSL -o "$TMP_TAR" "$URL"
mkdir -p "$EXTRACT_DIR"
tar -xzf "$TMP_TAR" -C "$EXTRACT_DIR"
[[ -d "$EXTRACT_DIR/asc-devkit/docs/zh" ]] || {
  echo "Downloaded archive has no asc-devkit/docs/zh directory" >&2
  exit 1
}
repair_published_code_links "$EXTRACT_DIR"
write_complete_marker "$EXTRACT_DIR"
if [[ -d "$TARGET_DIR" ]]; then
  mv "$TARGET_DIR" "$TEMP_DIR/previous"
fi
if ! mv "$EXTRACT_DIR" "$TARGET_DIR"; then
  [[ ! -d "$TEMP_DIR/previous" ]] || mv "$TEMP_DIR/previous" "$TARGET_DIR"
  exit 1
fi
echo "Done. Documentation restored to $TARGET_DIR/"
)

if [[ "$RESOURCE_SCOPE" != "--code" ]]; then
  fetch_documents
fi
if [[ "$RESOURCE_SCOPE" != "--docs" ]]; then
  python3 "$SCRIPT_DIR/.agents/skills/knowledge-ingest/scripts/source_resources.py" \
    --knowledge-root "$SCRIPT_DIR" fetch
fi
