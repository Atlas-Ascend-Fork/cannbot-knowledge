"""Restored local-source and fetch-script checks."""

from __future__ import annotations

import os
from pathlib import Path

from ..knowledge import Contract, Issue


def check(contract: Contract, document, context) -> list[Issue]:
    if document.metadata is None or document.path.name == "index.md":
        return []
    sources = document.metadata.get("sources")
    if not isinstance(sources, list):
        return []
    definitions = {
        str(definition.get("root")): definition
        for definition in contract.local_sources.values()
        if isinstance(definition, dict)
    }
    issues: list[Issue] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        resource = source.get("resource")
        if not isinstance(resource, str) or resource.startswith(
            ("http://", "https://")
        ):
            continue
        relative = Path(resource)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            continue
        definition = definitions.get(relative.parts[0])
        if not isinstance(definition, dict):
            continue
        source_root = contract.root / relative.parts[0]
        if not source_root.exists():
            continue
        if relative.parts[0] not in context.checked_local_roots:
            context.checked_local_roots.add(relative.parts[0])
            marker = source_root / ".complete"
            expected = f"archive_sha256={definition.get('archive_sha256', '')}"
            if not source_root.is_dir() or not marker.is_file():
                issues.append(
                    Issue(
                        "source.archive_marker",
                        "restored source requires .complete",
                        path=marker,
                    )
                )
            elif expected not in marker.read_text(encoding="utf-8").splitlines():
                issues.append(
                    Issue(
                        "source.archive_marker",
                        "restored source archive SHA-256 does not match Registry",
                        path=marker,
                    )
                )
        if not (contract.root / relative).is_file():
            issues.append(
                Issue(
                    "source.local_missing",
                    f"local source file does not exist: {resource}",
                )
            )
    return issues


def check_repository(contract: Contract) -> list[tuple[Path, Issue]]:
    results: list[tuple[Path, Issue]] = []
    for source_id, definition in contract.local_sources.items():
        fetch_script = contract._safe_repository_path(str(definition["fetch_script"]))
        if not fetch_script.is_file():
            results.append(
                (
                    contract.root / "governance/schemas/registries.yaml",
                    Issue(
                        "source.fetch_script_missing",
                        f"local source {source_id} fetch script does not exist: "
                        f"{fetch_script.relative_to(contract.root)}",
                    ),
                )
            )
        elif not os.access(fetch_script, os.X_OK):
            results.append(
                (
                    fetch_script,
                    Issue(
                        "source.fetch_script_mode",
                        f"local source {source_id} fetch script must be executable",
                    ),
                )
            )
    return results
