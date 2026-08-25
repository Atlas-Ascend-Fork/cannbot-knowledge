"""Require each direct index entry to include a short summary."""

from __future__ import annotations

import re

from ..indexes import direct_entry_target
from ..knowledge import Contract, Issue
from .links import mask_code


INDEX_ENTRY_RE = re.compile(
    r"^\s*-\s+\[[^\]]+\](?:\([^)]+\)|\[[^\]]*\])(?P<tail>.*)$"
)
REFERENCE_DEFINITION_RE = re.compile(r"^[ \t]{0,3}\[[^]\n]+\]:")


def check(contract: Contract, document, context) -> list[Issue]:
    del contract, context
    if document.path.name != "index.md" or document.parse_error is not None:
        return []

    lines = list(zip(document.text.splitlines(), mask_code(document.text).splitlines()))
    reference_definitions = "\n".join(
        masked
        for original, masked in lines
        if not original.startswith(("    ", "\t"))
        and REFERENCE_DEFINITION_RE.match(masked)
    )
    issues: list[Issue] = []
    for line_number, (original, masked) in enumerate(lines, start=1):
        if original.startswith(("    ", "\t")):
            continue
        match = INDEX_ENTRY_RE.match(original)
        if (
            match is None
            or direct_entry_target(masked, reference_definitions) is None
        ):
            continue
        description = match.group("tail").lstrip(" \t:：-–—|").strip()
        if not description:
            issues.append(
                Issue(
                    "index.entry_description",
                    "index entry requires a summary",
                    line=line_number,
                    details=original.strip(),
                )
            )
    return issues
