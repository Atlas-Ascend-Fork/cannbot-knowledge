# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Content-aware adoption of a persisted knowledge index after a fresh clone.

Quick verify compares each card's size and mtime_ns against the index
manifest; a fresh ``git clone`` rewrites every file with a new mtime, so a
volume-persisted index always fails verification even when the content is
byte-identical. This tool re-establishes validity without weakening the
fail-closed contract: every drifted card is confirmed by SHA-256 against the
manifest before its mtime is restored; any size, content, or card-set
difference refuses adoption and the caller rebuilds the index instead.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root", required=True)
    arguments = parser.parse_args(argv)
    root = Path(arguments.knowledge_root).resolve()
    # The retrieval package lives in the same checkout as this tool, next to
    # knowledge_index.py; the knowledge root may be any directory (fixture,
    # mounted clone) and need not contain the skill scripts itself.
    scripts = (
        Path(__file__).resolve().parents[1]
        / ".agents"
        / "skills"
        / "knowledge-query"
        / "scripts"
    )
    if not scripts.is_dir():
        print(f"[index-adopt] skill scripts not found: {scripts}", file=sys.stderr)
        return 1
    sys.path.insert(0, str(scripts))
    from retrieval.index import _card_files, index_path  # noqa: E402
    from retrieval.root import sha256_file  # noqa: E402

    path = index_path(root)
    if not path.is_file():
        print(f"[index-adopt] index missing: {path}", file=sys.stderr)
        return 1
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        print(f"[index-adopt] cannot open index: {exc}", file=sys.stderr)
        return 1
    try:
        connection.row_factory = sqlite3.Row
        manifest = {
            row["relative_path"]: (row["size"], row["mtime_ns"], row["file_sha256"])
            for row in connection.execute(
                "SELECT relative_path, size, mtime_ns, file_sha256 FROM manifest"
            )
        }
    except sqlite3.Error as exc:
        print(f"[index-adopt] cannot read manifest: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()

    current = {
        card.relative_to(root).as_posix(): card for card in _card_files(root)
    }
    if set(manifest) != set(current):
        missing = sorted(set(manifest) - set(current))[:3]
        extra = sorted(set(current) - set(manifest))[:3]
        print(
            f"[index-adopt] card set differs (manifest={len(manifest)}, "
            f"current={len(current)}); "
            f"missing_from_disk={missing} not_in_index={extra}",
            file=sys.stderr,
        )
        return 1

    restored = 0
    already_current = 0
    for relative, card_path in current.items():
        expected_size, expected_mtime_ns, expected_sha256 = manifest[relative]
        stat = card_path.stat()
        if stat.st_size != expected_size:
            print(f"[index-adopt] size differs: {relative}", file=sys.stderr)
            return 1
        if stat.st_mtime_ns == expected_mtime_ns:
            already_current += 1
            continue
        if sha256_file(card_path) != expected_sha256:
            print(f"[index-adopt] content differs: {relative}", file=sys.stderr)
            return 1
        os.utime(card_path, ns=(expected_mtime_ns, expected_mtime_ns))
        if card_path.stat().st_mtime_ns != expected_mtime_ns:
            print(
                f"[index-adopt] filesystem refused mtime restore: {relative}",
                file=sys.stderr,
            )
            return 1
        restored += 1
    print(
        f"[index-adopt] adopted index: {len(current)} cards "
        f"({restored} mtimes restored, {already_current} already current; "
        "every card verified by sha256)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
