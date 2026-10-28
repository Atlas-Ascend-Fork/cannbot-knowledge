# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Registry-driven applicability validation and three-valued Scope matching."""

from __future__ import annotations

import re
from typing import Any

from .scope_matchers import (
    DIMENSION_MATCHERS, DimensionMatch, DimensionMatcher, VALUE_RE,
    object_fields as _object, string_list as _strings,
)

NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+\.v[1-9][0-9]*$")
class ScopeRegistry:
    """Shared branch protocol; domains select their own dimension handlers."""

    def __init__(self, definitions: Any):
        if not isinstance(definitions, dict):
            raise ValueError("registries.scope_schemas must be an object")
        self.definitions = definitions
        self.matchers: dict[tuple[str, str], DimensionMatcher] = {}
        for namespace, definition in definitions.items():
            if not isinstance(namespace, str) or not NAMESPACE_RE.fullmatch(namespace):
                raise ValueError(f"invalid scope schema: {namespace}")
            _object(definition, {"description", "routes", "domains", "dimensions"}, namespace)
            if not isinstance(definition.get("description"), str) or not definition["description"].strip():
                raise ValueError(f"{namespace} requires a description")
            if not any(key in definition for key in ("routes", "domains")):
                raise ValueError(f"{namespace} requires routes or direct-profile domains")
            for key in ("routes", "domains"):
                if key in definition:
                    _strings(definition[key], f"{namespace}.{key}")
            dimensions = definition.get("dimensions")
            if not isinstance(dimensions, dict) or not dimensions:
                raise ValueError(f"{namespace}.dimensions must be a non-empty object")
            for name, dimension in dimensions.items():
                if not isinstance(name, str) or not VALUE_RE.fullmatch(name):
                    raise ValueError(f"invalid scope dimension: {name}")
                if not isinstance(dimension, dict):
                    raise ValueError(f"{namespace}.{name} must be an object")
                kind = dimension.get("kind")
                if not isinstance(kind, str) or kind not in DIMENSION_MATCHERS:
                    raise ValueError(f"{namespace}.{name} has an unregistered matcher kind: {kind}")
                self.matchers[namespace, name] = DIMENSION_MATCHERS[kind](dimension, f"{namespace}.{name}")

    def applies_to(self, namespace: str, domain: str, route: str | None) -> bool:
        definition = self.definitions[namespace]
        if route is None:
            return domain in definition.get("domains", [])
        return f"{domain}/{route}" in definition.get("routes", [])

    def normalize(self, value: Any, *, query: bool = False) -> dict[str, Any]:
        value = _object(value, {"schema", "any_of"}, "scope")
        namespace = value.get("schema")
        if not isinstance(namespace, str) or namespace not in self.definitions:
            raise ValueError(f"unknown scope schema: {namespace}")
        profiles = value.get("any_of")
        if not isinstance(profiles, list) or not profiles:
            raise ValueError("scope.any_of must be a non-empty list")
        dimensions = self.definitions[namespace]["dimensions"]
        normalized = []
        for index, profile in enumerate(profiles):
            location = f"scope.any_of[{index}]"
            profile = _object(profile, {"all_of"}, location)
            conditions = profile.get("all_of")
            if not isinstance(conditions, dict) or not conditions:
                raise ValueError(f"{location}.all_of must be a non-empty object")
            if any(not isinstance(key, str) for key in conditions):
                raise ValueError(f"{location}.all_of keys must be strings")
            result = {}
            for name, condition in sorted(conditions.items()):
                if name not in dimensions:
                    raise ValueError(f"unknown scope dimension in {namespace}: {name}")
                target = f"{location}.all_of.{name}"
                result[name] = self.matchers[namespace, name].normalize(condition, query=query, location=target)
            entry = {"all_of": result}
            if entry in normalized:
                raise ValueError("scope.any_of contains equivalent duplicate branches")
            normalized.append(entry)
        return {"schema": namespace, "any_of": normalized}

    def compare(self, query: dict[str, Any], card: Any) -> dict[str, Any]:
        """Compare canonical queries; never merge conditions across branches."""
        if card is None:
            return {"state": "unknown", "reason": "missing_card_scope", "profiles": []}
        card = self.normalize(card)
        if card["schema"] != query["schema"]:
            return {"state": "unknown", "reason": "schema_mismatch", "profiles": []}
        pairs = []
        for qi, query_profile in enumerate(query["any_of"]):
            for ci, card_profile in enumerate(card["any_of"]):
                known, required = query_profile["all_of"], card_profile["all_of"]
                reasons = []
                intersections = {}
                for name in sorted(set(known) | set(required)):
                    qvalue, cvalue = known.get(name), required.get(name)
                    if cvalue is None:
                        reasons.append({"state": "unknown", "dimension": name, "reason": "missing_card_dimension"})
                    else:
                        result = self.matchers[query["schema"], name].compare(qvalue, cvalue)
                        if not isinstance(result, DimensionMatch):
                            raise ValueError(f"Scope matcher for {name} returned an invalid result")
                        reasons.extend({**reason, "dimension": name} for reason in result.reasons)
                        if result.matched_values is not None:
                            intersections[name] = result.matched_values
                states = {item["state"] for item in reasons}
                state = "conflict" if "conflict" in states else "unknown" if states else "match"
                pairs.append({"query_profile": qi, "card_profile": ci, "state": state, "matched_values": intersections, "reasons": reasons})
        states = {pair["state"] for pair in pairs}
        state = "match" if "match" in states else "unknown" if "unknown" in states else "conflict"
        return {"state": state, "profiles": pairs}
