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

"""Synchronize and verify Registry-governed API/Guide transformations."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, unquote

import yaml


LINK_LIST_RE = re.compile(r"(?:- \[[^\]\n]+\]\([^\n)]+\)[ \t]*\n?)+\Z")


def split_link_suffix(text: str) -> tuple[str, str | None]:
    """Separate an optional trailing list of ordinary links, without block markers."""
    boundary = text.rfind("\n\n")
    if boundary >= 0 and LINK_LIST_RE.fullmatch(text[boundary + 2:]):
        return text[:boundary], text[boundary + 2:]
    return text, None

FRONTMATTER_RE = re.compile(r"\A---\n(?P<metadata>.*?)\n---\n\n", re.DOTALL)
INLINE_LINK_RE = re.compile(r"(!?)\[(?:\\.|[^\]\\\n])*\]\(([^)\n]+)\)")
REFERENCE_DEFINITION_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[((?:\\.|[^\]\\\n])+)]" r":[ \t]*(?:<([^>\n]+)>|(\S+))"
)
HTML_ATTRIBUTE_RE = re.compile(
    r"(?is)<(?P<tag>img|a)\b[^>]*?\b(?P<attr>src|href)\s*=\s*"
    r"(?P<q>[\"'])(?P<value>.*?)(?P=q)"
)
ESCAPED_PUNCTUATION_RE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~])")
FUNCTION_SECTION_RE = re.compile(r"(?ms)^## \u529f\u80fd\u8bf4\u660e[^\n]*\n(.*?)(?=^## |\Z)")
FENCED_CODE_RE = re.compile(r"(?ms)(?:```|~~~).*?(?:```|~~~)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[([^]]*)]\([^)]*\)")
MARKDOWN_LINK_RE = re.compile(r"\[([^]]+)]\([^)]*\)")
HEADING_RE = re.compile(
    r"(?m)^(?P<marks>#{1,6})[ \t]+(?P<title>[^\n]*)(?:\n|\Z)"
)
HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
HTML_TABLE_RE = re.compile(r"(?is)<table\b.*?</table>")
HTML_TAG_RE = re.compile(r"(?is)<[^>]+>")
NAVIGATION_PLACEHOLDER_RE = re.compile(
    r"^\s*#\s+[^\n]+\n+\s*本文件为文档发布时所需的索引文件。?\s*$"
)
TECHNICAL_SECTION_PREFIXES = (
    "功能说明",
    "函数原型",
    "参数说明",
    "返回值说明",
    "约束说明",
    "调用示例",
)
WEAK_DESCRIPTION_RE = re.compile(
    r"^(?:本文件为文档发布时所需的索引文件。|"
    r"表\s*\d+|"
    r"以下内容针对如下型号生效|"
    r"[-_*]{3,}|"
    r"Ascend C 官方(?:API|指南)文档：)"
)
URI_SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
LINK_FILE_SUFFIXES = {
    ".asc",
    ".c",
    ".cc",
    ".cpp",
    ".gif",
    ".h",
    ".hpp",
    ".jpeg",
    ".jpg",
    ".json",
    ".md",
    ".pdf",
    ".png",
    ".py",
    ".svg",
    ".txt",
    ".webp",
    ".yaml",
    ".yml",
}
API_HEADER_ROOTS = frozenset(
    {"adv_api", "aicpu_api", "basic_api", "c_api", "simt_api", "tensor_api", "utils"}
)
HEADER_PATH_INTRO_RE = re.compile(r"头文件路径(?:为)?\s*[：:]")
QUOTED_HEADER_RE = re.compile(r'"([A-Za-z0-9_./-]+\.h)"')
INCLUDE_HEADER_RE = re.compile(r'#\s*include\s+"([A-Za-z0-9_./-]+\.h)"')


def load_ingest_module():
    module_name = "_cannbot_fixed_archive_ingest"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    source = Path(__file__).with_name("knowledge_ingest.py")
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ingest support module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ingest = load_ingest_module()
mask_code = importlib.import_module(
    f"{ingest.contract_package().__name__}.checks.links"
).mask_code


def load_repair_module():
    module_name = "_cannbot_fixed_archive_repair"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    source = Path(__file__).with_name("repair_fixed_archive.py")
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load fixed archive repair module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def read_utf8(path: Path) -> str:
    """Decode UTF-8 without universal-newline or end-of-file normalization."""

    return path.read_bytes().decode("utf-8")


def platform_module():
    package = ingest.contract_package()
    return importlib.import_module(f"{package.__name__}.checks.platforms")


def mirror_config(root: Path, source_id: str) -> tuple[dict[str, object], dict[str, object]]:
    contract = ingest.load_contract(root)
    definition = contract.local_sources.get(source_id)
    if not isinstance(definition, dict):
        raise ValueError(f"unknown local source: {source_id}")
    mirror = definition.get("mirror")
    if not isinstance(mirror, dict):
        raise ValueError(f"local source is not an API/Guide mirror: {source_id}")
    return definition, mirror


def snake(value: str) -> str:
    leading = "_" if value.startswith("_") else ""
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return leading + (value or "document")


def plain_heading_title(value: str) -> str:
    """Return heading text without publisher anchors or Markdown escaping."""

    value = re.sub(r"<a\b[^>]*>.*?</a>", "", value, flags=re.I)
    value = HTML_TAG_RE.sub("", value)
    return ESCAPED_PUNCTUATION_RE.sub(r"\1", value).strip()


def strip_configured_sections(
    body: str, title_fragments: list[str]
) -> tuple[str, int]:
    """Remove configured source sections while preserving every other byte."""

    if not title_fragments:
        return body, 0
    masked = mask_code(body)
    headings = list(HEADING_RE.finditer(masked))
    ranges: list[tuple[int, int]] = []
    for index, heading in enumerate(headings):
        title = plain_heading_title(body[heading.start("title") : heading.end("title")])
        if not any(fragment in title for fragment in title_fragments):
            continue
        level = len(heading.group("marks"))
        end = len(body)
        for following in headings[index + 1 :]:
            if len(following.group("marks")) <= level:
                end = following.start()
                break
        ranges.append((heading.start(), end))
    merged: list[tuple[int, int]] = []
    for start, end in ranges:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    for start, end in reversed(merged):
        body = body[:start] + body[end:]
    return body, len(ranges)


def _local_document_link_count(body: str) -> int:
    count = 0
    masked = mask_code(body)
    for match in INLINE_LINK_RE.finditer(masked):
        if match.group(1):
            continue
        value = match.group(2)
        start, end = target_token_span(value)
        target = value[start:end]
        if target.startswith(("#", "//")) or URI_SCHEME_RE.match(target):
            continue
        path = target.split("#", 1)[0].strip("<>")
        if not path or Path(unquote(path)).suffix.casefold() == ".md":
            count += 1
    for match in HTML_ATTRIBUTE_RE.finditer(masked):
        if (
            match.group("tag").casefold() != "a"
            or match.group("attr").casefold() != "href"
        ):
            continue
        target = match.group("value")
        if target.startswith(("#", "//")) or URI_SCHEME_RE.match(target):
            continue
        path = target.split("#", 1)[0]
        if not path or Path(unquote(path)).suffix.casefold() == ".md":
            count += 1
    return count


def _navigation_residual(body: str) -> str:
    """Remove headings and link-catalog structures for navigation classification."""

    value = mask_code(body)
    value = HTML_COMMENT_RE.sub("", value)
    value = HEADING_RE.sub("", value)
    value = HTML_TABLE_RE.sub(
        lambda match: (
            ""
            if _local_document_link_count(match.group())
            else HTML_TAG_RE.sub(" ", match.group())
        ),
        value,
    )
    lines: list[str] = []
    raw_lines = value.splitlines()
    index = 0
    while index < len(raw_lines):
        raw = raw_lines[index]
        line = raw.strip()
        index += 1
        if not line:
            continue
        if line.startswith("|") and line.endswith("|"):
            table = [line]
            while index < len(raw_lines):
                following = raw_lines[index].strip()
                if not (following.startswith("|") and following.endswith("|")):
                    break
                table.append(following)
                index += 1
            data_rows = [
                row
                for row in table[1:]
                if not re.fullmatch(r"[|: -]+", row)
            ]
            if data_rows and all(
                _local_document_link_count(row) for row in data_rows
            ):
                continue
            lines.extend(
                value
                for row in table
                if (
                    value := HTML_TAG_RE.sub("", row).strip(" \t|:-")
                )
            )
            continue
        plain = HTML_TAG_RE.sub("", line).strip()
        if not plain or re.fullmatch(r"[-_* |:]+", plain):
            continue
        list_item = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(?P<item>.*)", plain)
        if list_item is not None and INLINE_LINK_RE.search(plain):
            remainder = INLINE_LINK_RE.sub("", list_item.group("item"))
            remainder = remainder.replace("**", "").replace("`", "")
            remainder = remainder.strip(" \t\uff1a:，,。.；;、|-")
            if not remainder:
                continue
            plain = remainder
        without_links = INLINE_LINK_RE.sub("", plain)
        without_links = without_links.replace("**", "").replace("`", "")
        without_links = without_links.strip(" \t\uff1a:，,。.；;、|-")
        if INLINE_LINK_RE.search(plain) and not without_links:
            continue
        if re.match(r"^\*\*表\s*\d+\*\*", without_links):
            continue
        if without_links:
            lines.append(without_links)
    return " ".join(lines)


def navigation_only_source(source: Path, body: str, policy: str) -> bool:
    """Identify publisher navigation pages that must become directory indexes."""

    if policy != "index_only":
        raise ValueError(f"unsupported fixed-archive navigation policy: {policy}")
    if source.name.casefold() == "index.md":
        return True
    if NAVIGATION_PLACEHOLDER_RE.fullmatch(body):
        return True
    masked = mask_code(body)
    headings = [
        plain_heading_title(body[item.start("title") : item.end("title")])
        for item in HEADING_RE.finditer(masked)
    ]
    if any(
        title.startswith(prefix)
        for title in headings[1:]
        for prefix in TECHNICAL_SECTION_PREFIXES
    ):
        return False
    local_links = _local_document_link_count(body)
    residual = _navigation_residual(body)
    if not residual and local_links:
        return True
    if not residual and len(headings) <= 1:
        return True
    stem = snake(source.stem)
    catalog_name = stem.endswith("_list") or stem in {"list", "readme"}
    return bool(
        catalog_name
        and local_links
        and not FENCED_CODE_RE.search(body)
        and not MARKDOWN_IMAGE_RE.search(body)
    )


def selected_sources(root: Path, definition: dict[str, object], mirror: dict[str, object]) -> list[Path]:
    archive_root = root / str(definition["root"])
    source_root = archive_root / str(mirror["source_root"])
    selected: list[Path] = []
    for relative in mirror["api_roots"]:
        selected.extend((source_root / str(relative)).rglob("*.md"))
    for relative in mirror["guide_roots"]:
        selected.extend((source_root / str(relative)).rglob("*.md"))
    selected.extend(source_root / str(relative) for relative in mirror["guide_files"])
    excluded = {str(value) for value in mirror["exclude"]}
    result = sorted(
        path.resolve()
        for path in selected
        if path.is_file() and path.relative_to(source_root).as_posix() not in excluded
    )
    if not result:
        raise ValueError(f"fixed archive contains no selected Markdown below {source_root}")
    return result


def card_path(root: Path, source_root: Path, source: Path, mirror: dict[str, object]) -> Path:
    relative = source.relative_to(source_root)
    api_roots = {Path(str(value)).parts[0] for value in mirror["api_roots"]}
    if relative.parts[0] in api_roots:
        base = root / "knowledge/ops/ascendc/apis"
        parts = relative.parts[1:]
    else:
        base = root / "knowledge/ops/ascendc/guides"
        guide_roots = {Path(str(value)).parts[0] for value in mirror["guide_roots"]}
        parts = relative.parts[1:] if relative.parts[0] in guide_roots else relative.parts
    normalized = [
        snake(part[:-3]) + ".md" if part.endswith(".md") else snake(part)
        for part in parts
    ]
    if normalized[-1] == "index.md":
        normalized[-1] = "guide_overview.md"
    elif normalized[-1] == "readme.md":
        parent = normalized[-2] if len(normalized) > 1 else "ascend_c"
        normalized[-1] = f"{parent}_reference.md"
    return base.joinpath(*normalized)


def legacy_card_path(
    root: Path, source_root: Path, source: Path, mirror: dict[str, object]
) -> Path:
    """Return the card path used before index-only navigation was enforced."""

    output = card_path(root, source_root, source, mirror)
    if source.name.casefold() == "readme.md":
        return output.with_name("readme.md")
    return output


def navigation_index_path(
    source: Path,
    *,
    root: Path,
    source_root: Path,
    mirror: dict[str, object],
    retained_directories: set[Path],
) -> Path:
    """Map a skipped publisher navigation page to its nearest useful index."""

    output = card_path(root, source_root, source, mirror).resolve()
    api_root = (root / "knowledge/ops/ascendc/apis").resolve()
    guide_root = (root / "knowledge/ops/ascendc/guides").resolve()
    boundary = api_root if output.is_relative_to(api_root) else guide_root
    directory = output.parent
    while directory not in retained_directories and directory != boundary:
        directory = directory.parent
    return directory / "index.md"


def target_token_span(value: str) -> tuple[int, int]:
    left = len(value) - len(value.lstrip())
    stripped = value[left:]
    if stripped.startswith("<"):
        closing = stripped.find(">")
        if closing >= 0:
            return left + 1, left + closing
    match = re.match(r"\S+", stripped)
    if match is None:
        return left, left
    return left + match.start(), left + match.end()


def relative_under(path: Path, parent: Path) -> Path | None:
    try:
        return path.relative_to(parent)
    except ValueError:
        return None


def external_target(
    target: Path,
    *,
    image: bool,
    archive_root: Path,
    source_repository_root: Path,
    mirror: dict[str, object],
) -> str:
    repository_relative = relative_under(target, source_repository_root)
    if repository_relative is not None:
        encoded = quote(repository_relative.as_posix(), safe="/")
        repository = str(mirror["upstream_repository"])
        revision = str(mirror["upstream_revision"])
        if image:
            owner_repo = repository.removeprefix("https://gitcode.com/")
            return f"https://raw.gitcode.com/{owner_repo}/raw/{revision}/{encoded}"
        kind = "tree" if target.is_dir() else "blob"
        return f"{repository}/{kind}/{revision}/{encoded}"
    archive_relative = relative_under(target, archive_root)
    if archive_relative is None or not archive_relative.parts:
        raise ValueError(f"relative document link escapes the fixed archive: {target}")
    project = archive_relative.parts[0]
    rest = Path(*archive_relative.parts[1:]).as_posix()
    kind = "tree" if target.is_dir() else "blob"
    suffix = "" if rest == "." else "/" + quote(rest, safe="/")
    return f"https://gitcode.com/cann/{project}/{kind}/master{suffix}"


def rewrite_target(
    raw: str,
    *,
    source: Path,
    output: Path,
    image: bool,
    source_to_card: dict[Path, Path],
    casefold_sources: dict[str, Path],
    archive_root: Path,
    source_repository_root: Path,
    mirror: dict[str, object],
) -> str:
    if raw.startswith(("//", "#")) or URI_SCHEME_RE.match(raw):
        return raw
    path_text, separator, fragment = raw.partition("#")
    target = (source.parent / unquote(path_text)).resolve()
    canonical = (
        target
        if target in source_to_card
        else casefold_sources.get(target.as_posix().casefold())
    )
    if (
        canonical is None
        and not target.exists()
        and "/" not in path_text
        and "\\" not in path_text
        and Path(path_text).suffix.casefold() not in LINK_FILE_SUFFIXES
    ):
        # Markdown-like C/C++ constructs such as ``[capture](float value)``
        # are not link destinations and must stay byte-for-byte unchanged.
        return raw
    if canonical is not None:
        new_target = os.path.relpath(source_to_card[canonical], output.parent).replace(
            os.sep, "/"
        )
    else:
        new_target = external_target(
            target,
            image=image,
            archive_root=archive_root,
            source_repository_root=source_repository_root,
            mirror=mirror,
        )
    return new_target + (separator + fragment if separator else "")


def rewrite_links(
    body: str,
    *,
    source: Path,
    output: Path,
    source_to_card: dict[Path, Path],
    casefold_sources: dict[str, Path],
    archive_root: Path,
    source_repository_root: Path,
    mirror: dict[str, object],
) -> tuple[str, int]:
    masked = mask_code(body)
    edits: list[tuple[int, int, str]] = []

    def replacement(raw: str, image: bool) -> str:
        return rewrite_target(
            raw,
            source=source,
            output=output,
            image=image,
            source_to_card=source_to_card,
            casefold_sources=casefold_sources,
            archive_root=archive_root,
            source_repository_root=source_repository_root,
            mirror=mirror,
        )

    for match in INLINE_LINK_RE.finditer(masked):
        group_start, group_end = match.span(2)
        value = body[group_start:group_end]
        start, end = target_token_span(value)
        raw = value[start:end]
        rewritten = replacement(raw, bool(match.group(1)))
        if rewritten != raw:
            edits.append((group_start + start, group_start + end, rewritten))
    for match in REFERENCE_DEFINITION_RE.finditer(masked):
        group = 2 if match.group(2) is not None else 3
        start, end = match.span(group)
        raw = body[start:end]
        rewritten = replacement(raw, False)
        if rewritten != raw:
            edits.append((start, end, rewritten))
    for match in HTML_ATTRIBUTE_RE.finditer(masked):
        start, end = match.span("value")
        raw = body[start:end]
        rewritten = replacement(raw, match.group("tag").casefold() == "img")
        if rewritten != raw:
            edits.append((start, end, rewritten))
    for start, end, rewritten in sorted(edits, reverse=True):
        body = body[:start] + rewritten + body[end:]
    return body, len(edits)


def source_title(body: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    if match is None:
        raise ValueError("source document has no level-1 heading")
    title = re.sub(r"<a\b[^>]*>.*?</a>", "", match.group(1), flags=re.I)
    title = re.sub(r"<[^>]+>", "", title)
    title = ESCAPED_PUNCTUATION_RE.sub(r"\1", title).strip()
    return title or "Ascend C \u5b98\u65b9\u6587\u6863"


def source_description(body: str, profile: str, title: str) -> str:
    sections: list[str] = []
    if profile == "API" and (match := FUNCTION_SECTION_RE.search(body)) is not None:
        sections.append(match.group(1))
    sections.append(re.sub(r"(?m)^#\s+.*$", "", body, count=1))
    for candidate in sections:
        section = FENCED_CODE_RE.sub("", candidate)
        for paragraph in re.split(r"\n\s*\n", section):
            value = re.sub(r"(?m)^#{1,6}\s+.*$", "", paragraph)
            value = re.sub(r"<a\b[^>]*>.*?</a>", "", value, flags=re.I)
            value = re.sub(r"<[^>]+>", "", value)
            value = MARKDOWN_IMAGE_RE.sub(r"\1", value)
            value = MARKDOWN_LINK_RE.sub(r"\1", value)
            value = re.sub(r"(?m)^\s*>\s*(?:[^一-鿿A-Za-z0-9]\s*)?", "", value)
            value = value.replace("**", "").replace("`", "")
            value = ESCAPED_PUNCTUATION_RE.sub(r"\1", value)
            value = " ".join(value.split()).strip()
            if (
                value
                and not value.startswith(("|", "- ", ">", "**\u8868"))
                and not re.fullmatch(r"[-_*]{3,}", value)
                and not WEAK_DESCRIPTION_RE.match(value)
            ):
                return value
    if profile == "API":
        return f"{title}：汇总该主题的接口入口、功能与约束。"
    return f"{title}：汇总该主题下的官方指南入口与内容范围。"


def guide_tags(relative: str) -> list[str]:
    if "performance" in relative or "tuning_cases/" in relative:
        return ["task.optimization", "topic.performance.analysis"]
    if "debug" in relative or "dump" in relative or "assert" in relative:
        return ["task.debugging", "topic.implementation.debugging"]
    if "migration" in relative:
        return ["task.migration", "topic.quality.compatibility.version_migration"]
    if "compilation" in relative or "deployment" in relative:
        return ["task.implementation", "topic.compilation"]
    if "language_extension" in relative:
        return ["task.implementation", "topic.programming_model.language_extension"]
    if "tiling" in relative or "data_slice" in relative:
        return ["task.design", "topic.tiling"]
    if "memory" in relative or "buffer" in relative:
        return ["task.design", "topic.memory"]
    if "sync" in relative or "pipeline" in relative:
        return ["task.implementation", "topic.implementation.synchronization"]
    if "operator_practice/" in relative or "development/" in relative:
        return ["task.implementation", "topic.implementation"]
    return ["task.lookup", "topic.programming_model"]


def existing_card(path: Path, expected_body: str | None = None) -> tuple[dict[str, object] | None, str | None]:
    if not path.is_file():
        return None, None
    text = read_utf8(path)
    framing = FRONTMATTER_RE.match(text)
    if framing is None:
        raise ValueError(f"invalid existing mirror card: {path}")
    metadata = yaml.safe_load(framing.group("metadata"))
    if not isinstance(metadata, dict):
        raise ValueError(f"invalid existing mirror metadata: {path}")
    body = text[framing.end() :]
    if expected_body is None:
        return metadata, None
    if body.startswith(expected_body):
        suffix = body[len(expected_body):]
        if not suffix:
            return metadata, None
        if suffix.startswith("\n\n") and LINK_LIST_RE.fullmatch(suffix[2:]):
            return metadata, suffix[2:].rstrip("\n")
        raise ValueError(f"mirror additions must be ordinary trailing links: {path}")
    _, suffix = split_link_suffix(body)
    return metadata, suffix.rstrip("\n") if suffix is not None else None


def normalize_api_header(path: str) -> str | None:
    """Return a public AscendC header path relative to the repo root, or None."""

    if path.startswith("include/"):
        path = path[len("include/") :]
    if (
        re.fullmatch(r"[A-Za-z0-9_./-]+\.h", path) is None
        or any(part in {"", ".", ".."} for part in path.split("/"))
        or path.partition("/")[0] not in API_HEADER_ROOTS
    ):
        return None
    return f"include/{path}"


def api_headers(body: str) -> list[str]:
    """Extract the source-declared public header paths, in first-seen order."""

    headers: list[str] = []
    seen: set[str] = set()

    def collect(path: str) -> None:
        normalized = normalize_api_header(path)
        if normalized is not None and normalized not in seen:
            seen.add(normalized)
            headers.append(normalized)

    for line in body.splitlines():
        stripped = line.strip()
        if HEADER_PATH_INTRO_RE.search(stripped):
            for match in QUOTED_HEADER_RE.finditer(stripped):
                collect(match.group(1))
        match = INCLUDE_HEADER_RE.search(stripped)
        if match is not None:
            collect(match.group(1))
    return headers


def metadata_for(
    *,
    source: Path,
    source_root: Path,
    output: Path,
    body: str,
    definition: dict[str, object],
    old: dict[str, object] | None,
    stamp: str,
    description_body: str | None = None,
) -> dict[str, object]:
    profile = "API" if "/apis/" in output.as_posix() else "Guide"
    title = source_title(body)
    supported = platform_module().fixed_archive_platforms(body)
    platforms = supported if supported is not None else []
    if supported is not None and not supported:
        raise ValueError(f"explicit platform scope has no registered supported platform: {source}")
    relative = source.relative_to(source_root).as_posix().casefold()
    if profile == "Guide":
        tags = guide_tags(relative)
    elif relative.startswith("api/ai-cpu-api/"):
        tags = ["task.lookup", "topic.implementation.api_layer.aicpu_api"]
    elif relative.startswith("api/utils-api/"):
        tags = ["task.lookup", "topic.implementation.api_layer.utils_api"]
    elif relative.startswith("api/simt-api/"):
        tags = ["task.lookup", "topic.implementation.api_layer.simt_api"]
    elif "/c_api/" in f"/{relative}":
        tags = ["task.lookup", "topic.implementation.api_layer.c_api"]
    elif "/adv_api/" in f"/{relative}":
        tags = ["task.lookup", "topic.implementation.api_layer.high_level_api"]
    else:
        tags = ["task.lookup", "topic.implementation.api_layer.basic_api"]
    root_name = str(definition["root"])
    generated_description = source_description(
        description_body if description_body is not None else body,
        profile,
        title,
    )
    old_description = old.get("description") if old else None
    description = (
        old_description
        if isinstance(old_description, str)
        and not WEAK_DESCRIPTION_RE.match(old_description.strip())
        else generated_description
    )
    metadata = {
        "type": profile,
        "title": old.get("title", title) if old else title,
        "description": description,
        "tags": old.get("tags", tags) if old else tags,
        "status": "stable" if supported is not None else "draft",
        "sources": [
            {
                "resource": f"{root_name}/{source.relative_to(Path(definition['_archive_root'])).as_posix()}",
                "role": "primary",
            }
        ],
        "created_at": old.get("created_at", stamp) if old else stamp,
        "updated_at": stamp,
        "platforms": platforms,
    }
    if profile == "API":
        headers = api_headers(body)
        # The archive has docs/examples, not an include tree. Source-reviewed
        # enrichment is authored metadata, not reproducible from this archive.
        if not headers and old and "source_headers" in old:
            retained = old["source_headers"]
            if (
                not isinstance(retained, list)
                or any(
                    not isinstance(path, str) or normalize_api_header(path) != path
                    for path in retained
                )
                or len(set(retained)) != len(retained)
            ):
                raise ValueError(f"invalid retained source_headers: {output}")
            old_sources = old.get("sources")
            if retained and (
                not isinstance(old_sources, list)
                or metadata["sources"][0] not in old_sources
            ):
                raise ValueError(f"source_headers source changed; review required: {output}")
            headers = list(retained)
        if headers:
            metadata["source_headers"] = headers
    return metadata


def render_card(metadata: dict[str, object], body: str, navigation: str | None) -> str:
    frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).rstrip()
    suffix = "" if navigation is None else "\n\n" + navigation + "\n"
    return f"---\n{frontmatter}\n---\n\n" + body + suffix


def mirror_card_paths(root: Path, definition: dict[str, object]) -> set[Path]:
    contract = ingest.load_contract(root)
    mirror = definition["mirror"]
    if not isinstance(mirror, dict):
        raise ValueError("fixed archive definition is missing mirror configuration")
    prefix = (
        f"{str(definition['root']).rstrip('/')}/"
        f"{str(mirror['source_root']).strip('/')}/"
    )
    result: set[Path] = set()
    for base in (root / "knowledge/ops/ascendc/apis", root / "knowledge/ops/ascendc/guides"):
        for path in base.rglob("*.md"):
            if path.name == "index.md":
                continue
            try:
                metadata, _ = existing_card(path)
            except (OSError, ValueError, yaml.YAMLError):
                continue
            match = contract.fixed_archive_mirror(metadata) if metadata else None
            if match is not None and match[1].is_relative_to(root / prefix):
                result.add(path.resolve())
    return result


def expected_cards(
    root: Path, source_id: str, stamp: str | None
) -> tuple[dict[Path, str], dict[str, object], set[Path]]:
    definition, mirror = mirror_config(root, source_id)
    resources = importlib.import_module(f"{ingest.contract_package().__name__}.source_resources")
    archive_root = resources.validate_archive(root, definition)
    definition = {**definition, "_archive_root": archive_root}
    source_root = (archive_root / str(mirror["source_root"])).resolve()
    load_repair_module().repair_tree(source_root, write=False)
    repository_directory = Path(str(mirror["source_root"])).parts[0]
    source_repository_root = (archive_root / repository_directory).resolve()
    source_documents = selected_sources(root, definition, mirror)
    navigation_policy = str(mirror["navigation_policy"])
    omitted_titles = [str(value) for value in mirror["omit_section_title_contains"]]
    source_bodies = {source: read_utf8(source) for source in source_documents}
    curated_bodies: dict[Path, str] = {}
    section_counts: dict[Path, int] = {}
    for source, source_body in source_bodies.items():
        curated_bodies[source], section_counts[source] = strip_configured_sections(
            source_body, omitted_titles
        )
    navigation_sources = {
        source
        for source in source_documents
        if navigation_only_source(
            source,
            curated_bodies[source],
            navigation_policy,
        )
    }
    navigation_cards = {
        legacy_card_path(root, source_root, source, mirror).resolve()
        for source in navigation_sources
    }
    sources = [source for source in source_documents if source not in navigation_sources]
    paths = {
        source: card_path(root, source_root, source, mirror).resolve()
        for source in sources
    }
    if len(paths) != len(set(paths.values())):
        raise ValueError("fixed archive source paths collide after snake_case normalization")
    retained_directories: set[Path] = set()
    for output in paths.values():
        boundary = (
            (root / "knowledge/ops/ascendc/apis").resolve()
            if "/apis/" in output.as_posix()
            else (root / "knowledge/ops/ascendc/guides").resolve()
        )
        directory = output.parent
        while True:
            retained_directories.add(directory)
            if directory == boundary:
                break
            directory = directory.parent
    source_to_card = dict(paths)
    source_to_card.update(
        {
            source: navigation_index_path(
                source,
                root=root,
                source_root=source_root,
                mirror=mirror,
                retained_directories=retained_directories,
            )
            for source in navigation_sources
        }
    )
    casefold_sources = {
        source.as_posix().casefold(): source for source in source_documents
    }
    rendered: dict[Path, str] = {}
    rewrites = 0
    for source, output in paths.items():
        source_body = source_bodies[source]
        body, changes = rewrite_links(
            curated_bodies[source],
            source=source,
            output=output,
            source_to_card=source_to_card,
            casefold_sources=casefold_sources,
            archive_root=archive_root,
            source_repository_root=source_repository_root,
            mirror=mirror,
        )
        rewrites += changes
        old, navigation = existing_card(output, body)
        if old is None and source.name.casefold() == "readme.md":
            old, navigation = existing_card(output.with_name("readme.md"), body)
        if stamp is None:
            if old is None or not isinstance(old.get("updated_at"), str):
                raise ValueError(f"missing mirror card or updated_at: {output}")
            card_stamp = str(old["updated_at"])
        else:
            old_stamp = old.get("updated_at") if old else None
            card_stamp = str(old_stamp) if isinstance(old_stamp, str) else stamp
        metadata = metadata_for(
            source=source,
            source_root=source_root,
            output=output,
            body=source_body,
            definition=definition,
            old=old,
            stamp=card_stamp,
            description_body=curated_bodies[source],
        )
        candidate = render_card(metadata, body, navigation)
        if stamp is not None and (not output.is_file() or read_utf8(output) != candidate):
            metadata["updated_at"] = stamp
            candidate = render_card(metadata, body, navigation)
        rendered[output] = candidate
    report = {
        "source_id": source_id,
        "archive_url": definition["archive_url"],
        "upstream_revision": mirror["upstream_revision"],
        "source_documents": len(source_documents),
        "selected": len(sources),
        "navigation_documents_skipped": len(navigation_sources),
        "sections_omitted": sum(section_counts[source] for source in sources),
        "api_cards": sum("/apis/" in path.as_posix() for path in rendered),
        "guide_cards": sum("/guides/" in path.as_posix() for path in rendered),
        "link_targets_rewritten": rewrites,
    }
    return rendered, report, navigation_cards


def mirror_authored_offsets(text: str, source_prefix: str, contract) -> tuple[int, int] | None:
    """Return the transformed source-body byte range for a fixed-archive card."""

    framing = FRONTMATTER_RE.match(text)
    if framing is None:
        return None
    metadata = yaml.safe_load(framing.group("metadata"))
    if not isinstance(metadata, dict):
        return None
    match = contract.fixed_archive_mirror(metadata)
    if match is None or not match[1].is_relative_to(contract.root / source_prefix):
        return None
    body_start = framing.end()
    source_body, _ = split_link_suffix(text[body_start:])
    return body_start, body_start + len(source_body)


def line_offset(text: str, line: int) -> int:
    if line < 1:
        return -1
    offset = 0
    for number, value in enumerate(text.splitlines(keepends=True), start=1):
        if number == line:
            return offset
        offset += len(value)
    return -1


def diff_check(root: Path, source_id: str) -> int:
    """Run Git whitespace checks with a line-scoped mirror-body exception."""

    definition, mirror = mirror_config(root, source_id)
    contract = ingest.load_contract(root)
    source_prefix = (
        f"{str(definition['root']).rstrip('/')}/"
        f"{str(mirror['source_root']).strip('/')}/"
    )
    result = subprocess.run(
        ["git", "diff", "--check", "--", ".", ":(exclude)LICENSE"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        return 0
    lines = result.stdout.splitlines()
    kept: list[str] = []
    index = 0
    diagnostic = re.compile(
        r"^(?P<path>.+):(?P<line>\d+): "
        r"(?P<kind>trailing whitespace|space before tab in indent|"
        r"new blank line at EOF|blank line at EOF)\."
    )
    while index < len(lines):
        current = lines[index]
        match = diagnostic.match(current)
        ignored = False
        if match is not None:
            path = (root / match.group("path")).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                path = root / "__outside_repository__"
            if path.is_file():
                text = read_utf8(path)
                offsets = mirror_authored_offsets(text, source_prefix, contract)
                offset = line_offset(text, int(match.group("line")))
                ignored = (
                    offsets is not None
                    and offset >= offsets[0]
                    and offset < offsets[1]
                )
        if ignored:
            index += 1
            if index < len(lines) and lines[index].startswith("+"):
                index += 1
            continue
        kept.append(current)
        index += 1
    if result.stderr:
        sys.stderr.write(result.stderr)
        return 2
    if kept:
        print("\n".join(kept), file=sys.stderr)
        return 1
    return 0


def command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    if args.command == "diff-check":
        return diff_check(root, args.source_id)
    if args.command == "sync" and not args.updated_at:
        raise ValueError("sync requires an explicit --updated-at UTC timestamp")
    stamp = args.updated_at if args.command == "sync" else None
    rendered, report, navigation_cards = expected_cards(root, args.source_id, stamp)
    definition, _ = mirror_config(root, args.source_id)
    existing = mirror_card_paths(root, definition)
    expected = set(rendered)
    changed = [
        path
        for path, card in rendered.items()
        if not path.is_file() or read_utf8(path) != card
    ]
    stale = sorted(existing - expected)
    if args.command == "verify":
        failures: list[str] = []
        for path in sorted(expected):
            if read_utf8(path) != rendered[path]:
                failures.append(f"mirror differs from fixed source: {path.relative_to(root)}")
        failures.extend(f"stale mirror card: {path.relative_to(root)}" for path in stale)
        if failures:
            print("\n".join(failures[:100]), file=sys.stderr)
            print(f"verified={len(expected)} differences={len(failures)}")
            return 1
        print(f"verified={len(expected)} transformed_body_differences=0 stale=0")
        return 0
    for path in changed:
        ingest.atomic_write(path, rendered[path])
    for path in stale:
        path.unlink()
    report.update(
        {
            "changed": len(changed),
            "removed": len(stale),
            "updated_at": stamp,
        }
    )
    if args.report:
        ingest.atomic_write(Path(args.report), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    result.add_argument("--source-id", default="cann_docs_raw")
    sub = result.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync", help="synchronize the registered fixed archive")
    sync.add_argument("--updated-at", required=True)
    sync.add_argument("--report")
    sub.add_parser(
        "verify", help="verify the governed body transform and generated metadata"
    )
    sub.add_parser(
        "diff-check",
        help="run Git whitespace checks with a source-body-only mirror exception",
    )
    return result


def main() -> int:
    try:
        return command(parser().parse_args())
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
