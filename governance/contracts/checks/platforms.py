"""Platform scope checks."""

from __future__ import annotations

from ..knowledge import Contract, Issue


def check(contract: Contract, document, context) -> list[Issue]:
    del context
    if document.metadata is None or document.path_info is None:
        return []
    if document.path_info.card_type == "glossaries":
        return []
    platforms = document.metadata.get("platforms")
    if not isinstance(platforms, list) or not all(
        isinstance(item, str) for item in platforms
    ):
        return []
    issues: list[Issue] = []
    if not platforms and document.metadata.get("status") in {"stable", "deprecated"}:
        issues.append(
            Issue("platform.unknown", "empty platforms requires status draft")
        )
    if "agnostic" in platforms and len(platforms) != 1:
        issues.append(
            Issue(
                "platform.agnostic",
                "agnostic cannot be combined with concrete platforms",
            )
        )
    for platform in platforms:
        if platform not in contract.platforms:
            issues.append(
                Issue("platform.unknown", f"unregistered platform: {platform}")
            )
    return issues
