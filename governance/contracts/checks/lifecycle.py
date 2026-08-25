"""Knowledge lifecycle checks."""

from __future__ import annotations

from pathlib import Path

from ..knowledge import Contract, Issue


def check(contract: Contract, document, context) -> list[Issue]:
    del context
    if document.metadata is None or document.path_info is None:
        return []
    status = document.metadata.get("status")
    replaced_by = document.metadata.get("replaced_by")
    if replaced_by is None:
        return []
    if "status" not in document.metadata:
        return []
    if status != "deprecated":
        return [Issue("status.replaced_by", "replaced_by requires deprecated status")]
    if (
        not isinstance(replaced_by, str)
        or replaced_by.startswith(("/", "knowledge/"))
        or replaced_by.endswith(".md")
        or ".." in Path(replaced_by).parts
    ):
        return [
            Issue(
                "status.replaced_by",
                "replaced_by must be a bundle-relative Concept ID without .md",
            )
        ]

    issues: list[Issue] = []
    if replaced_by == document.path_info.doc_id:
        issues.append(
            Issue("status.replaced_by", "replaced_by cannot reference the current card")
        )
    if not (contract.root / "knowledge" / f"{replaced_by}.md").is_file():
        issues.append(
            Issue(
                "status.replaced_by",
                f"replacement card does not exist: {replaced_by}",
            )
        )
    return issues
