"""Frontmatter source resource and Git revision checks."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from ..knowledge import Contract, Issue


COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
GIT_VIEW_HOSTS = {
    "bitbucket.org",
    "codeberg.org",
    "gitcode.com",
    "github.com",
    "gitee.com",
    "gitlab.com",
}
RAW_GIT_HOSTS = {"raw.gitcode.com", "raw.githubusercontent.com"}


def check(contract: Contract, document, context) -> list[Issue]:
    del context
    if document.metadata is None or document.path_info is None:
        return []
    metadata = document.metadata
    sources = metadata.get("sources")
    if not isinstance(sources, list):
        return []

    issues: list[Issue] = []
    if metadata.get("status") in {"stable", "deprecated"} and not sources:
        issues.append(
            Issue("source.required", "non-draft card requires at least one source")
        )
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            continue
        resource = source.get("resource")
        if not isinstance(resource, str) or not resource.strip():
            issues.append(
                Issue("source.resource", f"sources[{index}].resource must be non-empty")
            )
        elif re.match(r"^https?://", resource):
            parsed = urlparse(resource)
            if (
                not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
            ):
                issues.append(
                    Issue(
                        "source.resource",
                        f"sources[{index}].resource is not a canonical HTTP(S) URL",
                    )
                )
            elif not git_url_is_pinned(resource):
                issues.append(
                    Issue(
                        "source.pin",
                        f"sources[{index}] Git resource is not pinned to a 40-hex commit",
                    )
                )
        elif not is_safe_local_resource(contract, resource):
            issues.append(
                Issue(
                    "source.resource",
                    f"sources[{index}].resource must be an HTTP(S) URL or registered local source",
                )
            )
    return issues


def is_safe_local_resource(contract: Contract, resource: str) -> bool:
    if resource != resource.strip() or "\\" in resource:
        return False
    parsed = urlparse(resource)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        return False
    relative = Path(resource)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        return False
    if relative.as_posix() != resource or len(relative.parts) < 2:
        return False
    try:
        (contract.root / relative).resolve().relative_to(contract.root)
    except ValueError:
        return False
    registered_roots = {
        str(source["root"]) for source in contract.local_sources.values()
    }
    return relative.parts[0] in registered_roots


def git_url_is_pinned(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host in GIT_VIEW_HOSTS:
        for marker in ("blob", "tree", "raw"):
            if marker in parts:
                index = parts.index(marker)
                return index + 1 < len(parts) and bool(
                    COMMIT_RE.fullmatch(parts[index + 1])
                )
        if host == "bitbucket.org" and "src" in parts:
            index = parts.index("src")
            return index + 1 < len(parts) and bool(
                COMMIT_RE.fullmatch(parts[index + 1])
            )
        if host == "codeberg.org" and "src" in parts:
            index = parts.index("src")
            return (
                index + 2 < len(parts)
                and parts[index + 1] == "commit"
                and bool(COMMIT_RE.fullmatch(parts[index + 2]))
            )
        return False
    if host == "raw.gitcode.com" and "raw" in parts:
        index = parts.index("raw")
        return index + 1 < len(parts) and bool(COMMIT_RE.fullmatch(parts[index + 1]))
    if host == "raw.githubusercontent.com" and len(parts) >= 3:
        return bool(COMMIT_RE.fullmatch(parts[2]))
    return host not in RAW_GIT_HOSTS
