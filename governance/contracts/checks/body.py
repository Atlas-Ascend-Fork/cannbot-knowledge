"""Knowledge body and description hygiene checks."""

from __future__ import annotations

import re

from ..knowledge import Contract, Issue


CONFLICT_RE = re.compile(r"(?m)^(?:<{7}|={7}|>{7})(?: .*)?$")
H1_RE = re.compile(r"(?m)^#\s+\S")
COLLAPSED_TABLE_RE = re.compile(r"(?m)\|[ \t]+\|[ \t]*:?-{3,}")
WEAK_DESCRIPTION_RE = re.compile(
    r"^(?:本文件为文档发布时所需的索引文件。|> \[![^]]+]|表\s*\d+|以下内容针对如下型号生效)"
)


def _outside_fenced_code(body: str) -> str:
    """Return body text with fenced-code contents removed."""
    result: list[str] = []
    fence: str | None = None
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = (
            "```"
            if stripped.startswith("```")
            else "~~~"
            if stripped.startswith("~~~")
            else None
        )
        if marker is not None:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            result.append("\n")
        elif fence is None:
            result.append(line)
        else:
            result.append("\n")
    return "".join(result)


def check(contract: Contract, document, context) -> list[Issue]:
    issues = check_card(contract, document, context)
    if (
        document.parse_error is not None
        or document.path.name == "index.md"
        or document.metadata is None
    ):
        return issues
    if CONFLICT_RE.search(document.body):
        issues.append(
            Issue("body.conflict_marker", "body contains a Git conflict marker")
        )
    prose = _outside_fenced_code(document.body)
    if len(H1_RE.findall(prose)) != 1:
        issues.append(
            Issue(
                "body.h1_count",
                "knowledge card body must contain exactly one level-1 heading outside fenced code",
            )
        )
    if COLLAPSED_TABLE_RE.search(prose):
        issues.append(
            Issue(
                "body.collapsed_table",
                "Markdown table rows appear collapsed onto one physical line",
            )
        )
    description = document.metadata.get("description")
    if isinstance(description, str) and WEAK_DESCRIPTION_RE.match(description.strip()):
        issues.append(
            Issue(
                "frontmatter.description_placeholder",
                "description is publishing markup or a table label, not a standalone summary",
            )
        )
    return issues


def check_card(contract: Contract, document, context) -> list[Issue]:
    del contract, context
    if (
        document.parse_error is not None
        or document.path.name == "index.md"
        or document.metadata is None
        or document.path_info is None
        or document.body.strip()
    ):
        return []
    return [Issue("body.empty", "knowledge card body is empty")]
