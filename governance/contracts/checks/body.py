"""Knowledge body and description hygiene checks."""

from __future__ import annotations

import re

from ..knowledge import Contract, Issue


CONFLICT_RE = re.compile(r"(?m)^(?:<{7}|={7}|>{7})(?: .*)?$")
WEAK_DESCRIPTION_RE = re.compile(
    r"^(?:本文件为文档发布时所需的索引文件。|> \[![^]]+]|表\s*\d+|以下内容针对如下型号生效)"
)


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
