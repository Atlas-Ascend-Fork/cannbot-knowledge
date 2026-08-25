"""Strict tree-source to exact blob-source navigation checks."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from ..knowledge import Contract, Issue
from .links import markdown_targets


def check(contract: Contract, document, context) -> list[Issue]:
    del contract
    if (
        not context.strict_navigation
        or document.metadata is None
        or document.path.name == "index.md"
    ):
        return []
    sources = document.metadata.get("sources")
    if not isinstance(sources, list):
        return []
    resources = [
        str(source.get("resource", ""))
        for source in sources
        if isinstance(source, dict)
    ]
    body_links = [target for target, _ in markdown_targets(document.body)]
    candidates = [*resources, *body_links]
    issues: list[Issue] = []
    for resource in resources:
        tree = git_view_location(resource, "tree")
        if tree and not any(
            git_view_location(candidate, "blob") == tree for candidate in candidates
        ):
            issues.append(
                Issue(
                    "source.navigation",
                    "tree source requires a same-repository, same-revision blob source or body link",
                )
            )
    return issues


def git_view_location(value: str, marker: str) -> tuple[str, str, str] | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if marker not in parts:
        return None
    index = parts.index(marker)
    if index + 1 >= len(parts):
        return None
    repository = parts[:index]
    if repository and repository[-1] == "-":
        repository = repository[:-1]
    revision = parts[index + 1]
    if len(repository) < 2 or not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        return None
    return parsed.hostname.lower(), "/".join(repository), revision.lower()
