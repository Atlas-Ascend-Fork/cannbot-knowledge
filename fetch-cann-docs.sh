#!/usr/bin/env bash
# Download and extract the Ascend CANN documentation examples package.
# The package is extracted beside this script and is used as the local source
# for knowledge cards that reference cann-docs-raw/ paths in their sources.
set -euo pipefail

URL="https://ascend-ci.obs.cn-north-4.myhuaweicloud.com/package/doc/Ascend-cann-docs-examples.tar.gz"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TARGET_DIR="$SCRIPT_DIR/cann-docs-raw"
REGISTRIES="$SCRIPT_DIR/governance/schemas/registries.yaml"
TEMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cannbot-docs.XXXXXX")
TMP_TAR="$TEMP_DIR/Ascend-cann-docs-examples.tar.gz"
EXTRACT_DIR="$TEMP_DIR/extracted"

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

if [ ! -f "$REGISTRIES" ]; then
  echo "Missing governance registry: $REGISTRIES" >&2
  exit 1
fi

EXPECTED_SHA256=$(python3 - "$REGISTRIES" <<'PY'
import sys
from pathlib import Path

import yaml

registry = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = registry["local_sources"]["cann_docs_raw"]["archive_sha256"]
if not isinstance(value, str) or len(value) != 64:
    raise SystemExit("invalid local_sources.cann_docs_raw.archive_sha256")
print(value)
PY
)

write_complete_marker() {
  local directory=$1
  printf 'archive_sha256=%s\n' "$EXPECTED_SHA256" > "$directory/.complete"
}

if [ -e "$TARGET_DIR" ]; then
  if [ -f "$TARGET_DIR/.complete" ] && grep -Fqx "archive_sha256=$EXPECTED_SHA256" "$TARGET_DIR/.complete"; then
    echo "cann-docs-raw/ was restored from the registered archive. Skipping download."
    exit 0
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

write_complete_marker "$EXTRACT_DIR"
mv "$EXTRACT_DIR" "$TARGET_DIR"
echo "Done. Documentation package extracted to $TARGET_DIR/"
