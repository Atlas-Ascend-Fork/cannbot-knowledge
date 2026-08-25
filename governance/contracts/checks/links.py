"""Markdown target parsing and local Bundle link checks."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from ..knowledge import Contract, Issue


INLINE_LINK_RE = re.compile(r"(!?)\[[^\]\n]*\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"(!?)\[([^\]\n]*)\]\[([^\]\n]*)\]")
REFERENCE_DEFINITION_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))"
)
FENCE_RE = re.compile(r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(?P<ticks>`+)[^\n]*?(?P=ticks)")


def mask_code(text: str) -> str:
    """Blank fenced and inline code while retaining source offsets."""

    def blank(value: str) -> str:
        return "".join("\n" if char == "\n" else " " for char in value)

    lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        if fence_char is None:
            if match is None:
                lines.append(line)
                continue
            fence = match.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            lines.append(blank(line))
            continue

        lines.append(blank(line))
        if match is not None:
            fence = match.group("fence")
            if (
                fence[0] == fence_char
                and len(fence) >= fence_length
                and not line[match.end() :].strip()
            ):
                fence_char = None
                fence_length = 0

    return INLINE_CODE_RE.sub(lambda match: blank(match.group()), "".join(lines))


def check(contract: Contract, document, context) -> list[Issue]:
    del context
    if document.parse_error is not None:
        return []
    issues: list[Issue] = []
    try:
        text = document.path.read_text(encoding="utf-8")
        links = links_in_text(
            text,
            document.path,
            contract.root / "knowledge",
        )
    except OSError as exc:
        return [Issue("link.read", str(exc))]

    knowledge_root = (contract.root / "knowledge").resolve()
    for raw, target, line in links:
        try:
            target.relative_to(knowledge_root)
        except ValueError:
            issues.append(
                Issue(
                    "link.outside_bundle",
                    f"local link leaves knowledge/: {raw}",
                    line=line,
                    details=raw,
                )
            )
            continue
        if not target.exists():
            issues.append(
                Issue(
                    "link.missing",
                    f"missing relative link target: {raw}",
                    line=line,
                    details=raw,
                )
            )
        elif not target.is_file():
            issues.append(
                Issue(
                    "link.not_file",
                    f"relative link target is not a file: {raw}",
                    line=line,
                    details=raw,
                )
            )
    return issues


def _reference_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _markdown_destination(value: str) -> str:
    return value.split()[0].strip("<>")


def _targets_with_lines(text: str) -> list[tuple[str, bool, int]]:
    masked = mask_code(text)
    matches: list[tuple[int, str, bool]] = [
        (match.start(), _markdown_destination(match.group(2)), bool(match.group(1)))
        for match in INLINE_LINK_RE.finditer(masked)
    ]
    definitions = {
        _reference_label(match.group(1)): (match.group(2) or match.group(3))
        for match in REFERENCE_DEFINITION_RE.finditer(masked)
    }
    for match in REFERENCE_LINK_RE.finditer(masked):
        label = _reference_label(match.group(3) or match.group(2))
        target = definitions.get(label)
        if target:
            matches.append(
                (
                    match.start(),
                    _markdown_destination(target),
                    bool(match.group(1)),
                )
            )
    return [
        (target, is_image, masked.count("\n", 0, offset) + 1)
        for offset, target, is_image in sorted(matches)
        if target
    ]


def markdown_targets(text: str) -> list[tuple[str, bool]]:
    """Return non-image Markdown destinations outside code spans."""

    return [
        (target, False)
        for target, is_image, _ in _targets_with_lines(text)
        if not is_image
    ]


def links_in_text(
    text: str,
    path: Path,
    bundle_root: Path | None = None,
) -> list[tuple[str, Path, int]]:
    results: list[tuple[str, Path, int]] = []
    for target_text, is_image, line in _targets_with_lines(text):
        if is_image or target_text.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = unquote(target_text.split("#", 1)[0])
        if not clean:
            continue
        if clean.startswith("/") and bundle_root is not None:
            target = (bundle_root / clean.lstrip("/")).resolve()
        else:
            target = (path.parent / clean).resolve()
        results.append((target_text, target, line))
    return results


def relative_markdown_links(
    path: Path,
    bundle_root: Path | None = None,
) -> list[tuple[str, Path]]:
    return [
        (raw, target)
        for raw, target, _ in links_in_text(
            path.read_text(encoding="utf-8"),
            path,
            bundle_root,
        )
    ]
