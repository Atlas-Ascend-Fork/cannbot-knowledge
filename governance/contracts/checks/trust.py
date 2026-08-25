"""Verification record checks."""

from __future__ import annotations

import re

from ..knowledge import Contract, Issue


ACTOR_RE = re.compile(r"^(?:human:[^\s/:]+|process:[^\s/:]+|[^\s/:]+/[^\s/]+)$")


def check(contract: Contract, document, context) -> list[Issue]:
    del contract, context
    if document.metadata is None or document.path_info is None:
        return []
    value = document.metadata.get("verified")
    if value is None:
        return []
    events = value if isinstance(value, list) else [value]
    issues: list[Issue] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        actor = event.get("by")
        if not isinstance(actor, str) or not ACTOR_RE.fullmatch(actor):
            issues.append(
                Issue(
                    "verified.actor",
                    f"verified[{index}].by must use human:<id>, process:<id>, or <producer>/<version>",
                )
            )
    return issues
