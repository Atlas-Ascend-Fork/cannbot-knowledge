# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Trusted dimension handlers; Registry selects kinds, never executable modules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import re
from typing import Any, Protocol


VALUE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def object_fields(value: Any, allowed: set[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{location} must be an object with string keys")
    extra = set(value) - allowed
    if extra:
        raise ValueError(f"{location} has unknown fields: {', '.join(sorted(extra))}")
    return value


def string_list(value: Any, location: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError(f"{location} must be a non-empty string list")
    if len(value) != len(set(value)):
        raise ValueError(f"{location} contains duplicates")
    return value


@dataclass
class DimensionMatch:
    """Empty reasons mean match; otherwise conflict wins over unknown."""

    reasons: list[dict[str, Any]] = field(default_factory=list)
    matched_values: Any = None

    def __post_init__(self):
        if not isinstance(self.reasons, list) or any(
            not isinstance(reason, dict)
            or reason.get("state") not in {"unknown", "conflict"}
            or not isinstance(reason.get("reason"), str)
            or not reason["reason"].strip()
            for reason in self.reasons
        ):
            raise ValueError("Scope matcher must return explicit unknown/conflict reasons")


class DimensionMatcher(Protocol):
    """A kind owns definition validation, canonical values and comparison semantics."""

    def normalize(self, value: Any, *, query: bool, location: str) -> Any: ...

    def compare(self, query: Any, card: Any) -> DimensionMatch: ...


class _Choices:
    def __init__(self, definition: dict[str, Any], location: str):
        object_fields(definition, {"kind", "values", "aliases", "query_none_of", "card_none_of"}, location)
        self.definition = definition
        self.values = string_list(definition.get("values"), f"{location}.values")
        if any(not VALUE_RE.fullmatch(item) or item == "any" for item in self.values):
            raise ValueError(f"{location} values must be canonical IDs, excluding any")
        for permission in ("query_none_of", "card_none_of"):
            negative = definition.get(permission, False)
            if not isinstance(negative, bool) or (negative and definition["kind"] != "required_set"):
                raise ValueError(f"{location}.{permission} requires a required_set")
        aliases = definition.get("aliases", {})
        if not isinstance(aliases, dict):
            raise ValueError(f"{location}.aliases must be an object")
        self.aliases = {item.casefold(): item for item in self.values}
        for alias, canonical in aliases.items():
            if not isinstance(alias, str) or not alias.strip() or alias.casefold() == "any":
                raise ValueError(f"invalid alias in {location}")
            if not isinstance(canonical, str) or canonical not in self.values:
                raise ValueError(f"unknown alias target in {location}: {canonical}")
            key = alias.casefold()
            if key in self.aliases and self.aliases[key] != canonical:
                raise ValueError(f"ambiguous alias in {location}: {alias}")
            self.aliases[key] = canonical

    def _values(self, raw: Any, *, query: bool, location: str, allow_any: bool = False) -> list[str]:
        items = string_list(raw, location)
        if allow_any and items == ["any"]:
            return items
        canonical = []
        for item in items:
            candidate = self.aliases.get(item.casefold()) if query else item
            if candidate not in self.values:
                raise ValueError(f"unknown scope value at {location}: {item}")
            canonical.append(candidate)
        if len(set(canonical)) != len(canonical):
            raise ValueError(f"{location} contains equivalent duplicate values")
        return sorted(canonical)


def _missing_query(card: Any) -> DimensionMatch:
    return DimensionMatch([{"state": "unknown", "reason": "missing_query_condition", "required": card}])


class EnumMatcher(_Choices):
    """Alternatives match on intersection; only an explicit card any is universal."""

    def normalize(self, value: Any, *, query: bool, location: str) -> list[str]:
        return self._values(value, query=query, location=location, allow_any=True)

    def compare(self, query: Any, card: list[str]) -> DimensionMatch:
        if card == ["any"]:
            return DimensionMatch()
        if query is None or query == ["any"]:
            return _missing_query(card)
        overlap = sorted(set(query) & set(card))
        if overlap:
            return DimensionMatch(matched_values=overlap)
        return DimensionMatch([{"state": "conflict", "reason": "disjoint_values", "query": query, "required": card}])


class RequiredSetMatcher(_Choices):
    """Presence and absence each require explicit query evidence."""

    def normalize(self, value: Any, *, query: bool, location: str) -> dict[str, list[str]]:
        allowed = {"all_of"}
        if self.definition.get("query_none_of" if query else "card_none_of"):
            allowed.add("none_of")
        value = object_fields(value, allowed, location)
        if not value:
            raise ValueError(f"{location} requires all_of or an allowed none_of")
        result = {key: self._values(items, query=query, location=location) for key, items in sorted(value.items())}
        if set(result.get("all_of", [])) & set(result.get("none_of", [])):
            raise ValueError(f"{location} requires and excludes the same feature")
        return result

    def compare(self, query: Any, card: dict[str, list[str]]) -> DimensionMatch:
        if query is None:
            return _missing_query(card)
        needed = set(card.get("all_of", []))
        forbidden = set(card.get("none_of", []))
        enabled = set(query.get("all_of", []))
        disabled = set(query.get("none_of", []))
        reasons = []
        absent, missing = needed & disabled, needed - enabled
        if absent:
            reasons.append({"state": "conflict", "reason": "excluded_required_features", "features": sorted(absent)})
        elif missing:
            reasons.append({"state": "unknown", "reason": "missing_query_features", "features": sorted(missing)})
        prohibited, unconfirmed = forbidden & enabled, forbidden - disabled
        if prohibited:
            reasons.append({"state": "conflict", "reason": "present_forbidden_features", "features": sorted(prohibited)})
        elif unconfirmed:
            reasons.append({"state": "unknown", "reason": "missing_query_absences", "features": sorted(unconfirmed)})
        return DimensionMatch(reasons)


# Extend only in the installed Contract package with reviewed, deterministic code.
# Registry/card/query data cannot name a Python module, import path or executable.
DIMENSION_MATCHERS: dict[str, Callable[[dict[str, Any], str], DimensionMatcher]] = {
    "enum": EnumMatcher,
    "required_set": RequiredSetMatcher,
}
