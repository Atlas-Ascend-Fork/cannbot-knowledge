#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Repair known documentation-publisher URL expansion inside code fences."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path


UPSTREAM_BASE = "https://gitcode.com/cann/asc-devkit/tree/master/docs/zh/"
FENCE_RE = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})")
REPAIR_TOKENS: dict[str, set[str]] = {
    "api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor_intro.md": {
        "const",
    },
    "api/SIMD-API/basic_api/data_structures/GlobalTensor/operator.md": {"const"},
    "api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor_intro.md": {
        "const",
    },
    "api/SIMD-API/basic_api/data_structures/LocalTensor/operator.md": {"const"},
    "api/SIMD-API/tensor_api/tensor/tensor.md": {"const", "constexpr"},
    "guide/operator_practice/simd_operator_impl/fusion_operator_programming/"
    "general_fusion/operator_impl.md": {"int64_t"},
    "guide/programming_guide/advanced_programming/ai_framework_adaptation/"
    "tensorflow_framework.md": {
        "InferenceContext",
        "InferenceContext*",
        "InferenceContextPtr",
    },
    "guide/technical_appendix/cpp_standard_support/syntax_restrictions/features.md": {
        "float",
        "float*",
    },
}


def _transform_fenced_lines(
    text: str, transform: Callable[[str], str]
) -> str:
    lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        if fence_char is None:
            lines.append(line)
            if match is not None:
                fence = match.group("fence")
                fence_char = fence[0]
                fence_length = len(fence)
            continue
        lines.append(transform(line))
        if match is not None:
            fence = match.group("fence")
            if (
                fence[0] == fence_char
                and len(fence) >= fence_length
                and not line[match.end() :].strip()
            ):
                fence_char = None
                fence_length = 0
    return "".join(lines)


def _repair_document(text: str, relative: str, tokens: set[str]) -> tuple[str, Counter[str]]:
    prefix = UPSTREAM_BASE + str(Path(relative).parent).replace("\\", "/") + "/"
    alternatives = "|".join(re.escape(token) for token in sorted(tokens, key=len, reverse=True))
    pattern = re.compile(
        rf"(?:{re.escape(prefix)})+(?P<token>{alternatives})(?![A-Za-z0-9_])"
    )
    counts: Counter[str] = Counter()

    def replace(line: str) -> str:
        def replacement(match: re.Match[str]) -> str:
            token = match.group("token")
            counts[token] += 1
            return token

        return pattern.sub(replacement, line)

    return _transform_fenced_lines(text, replace), counts


def _current_directory_urls(text: str, relative: str) -> list[str]:
    prefix = UPSTREAM_BASE + str(Path(relative).parent).replace("\\", "/") + "/"
    pattern = re.compile(re.escape(prefix) + r"[^\s`<>{}\[\]\"']+")
    found: list[str] = []

    def collect(line: str) -> str:
        found.extend(match.group(0) for match in pattern.finditer(line))
        return line

    _transform_fenced_lines(text, collect)
    return found


def repair_tree(source_root: Path, *, write: bool) -> int:
    """Repair known file/token shapes regardless of the rolling archive counts."""

    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise ValueError(f"documentation source root is missing: {source_root}")

    transformed: dict[Path, bytes] = {}
    actual: dict[str, dict[str, int]] = {}
    remaining: list[str] = []
    for relative, tokens in REPAIR_TOKENS.items():
        path = source_root / relative
        if not path.is_file():
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        repaired, counts = _repair_document(text, relative, tokens)
        actual[relative] = dict(counts)
        transformed[path] = repaired.encode("utf-8")

    for path in sorted(source_root.rglob("*.md")):
        relative = path.relative_to(source_root).as_posix()
        content = transformed.get(path, path.read_bytes()).decode("utf-8")
        remaining.extend(
            f"{relative}: {value}"
            for value in _current_directory_urls(content, relative)[:3]
        )

    total = sum(sum(values.values()) for values in actual.values())
    if remaining:
        raise ValueError(
            "fixed archive still contains current-directory URLs inside code fences: "
            + "; ".join(remaining)
        )
    if total and not write:
        raise ValueError(f"fixed archive requires {total} registered code-token repairs")
    if total:
        for path, content in transformed.items():
            if path.read_bytes() != content:
                path.write_bytes(content)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sync", "verify"))
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = repair_tree(args.source_root, write=args.command == "sync")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"fixed archive repair failed: {exc}", file=sys.stderr)
        return 2
    print(f"fixed archive code-token repairs={count} status={'updated' if count else 'clean'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
