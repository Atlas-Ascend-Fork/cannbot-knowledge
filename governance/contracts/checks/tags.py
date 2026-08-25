"""Registered tag checks."""

from __future__ import annotations

from ..knowledge import Contract, Issue


def check(contract: Contract, document, context) -> list[Issue]:
    del context
    if document.metadata is None or document.path_info is None:
        return []
    tags = document.metadata.get("tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        return []

    issues: list[Issue] = []
    dimensions: set[str] = set()
    for tag in tags:
        definition = contract.tags.get(tag)
        if not isinstance(definition, dict):
            issues.append(Issue("tag.unknown", f"unregistered tag: {tag}"))
        else:
            dimensions.add(str(definition.get("dimension")))
    for required in ("task", "topic"):
        if required not in dimensions:
            issues.append(
                Issue(f"tag.{required}", f"at least one {required} tag is required")
            )
    return issues
