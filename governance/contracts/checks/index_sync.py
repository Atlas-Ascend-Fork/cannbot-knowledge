"""Generated index consistency check."""

from __future__ import annotations

from pathlib import Path

from ..indexes import index_updates
from ..knowledge import Contract, Issue


def check_repository(contract: Contract) -> list[tuple[Path, Issue]]:
    _, stale = index_updates(contract.root)
    return [
        (update.path, Issue("index.stale", "generated knowledge index is stale"))
        for update in stale
    ]
