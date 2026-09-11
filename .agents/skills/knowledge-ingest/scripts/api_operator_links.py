#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Synchronize auditable API-to-Operator links from explicit invocation evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import yaml


FRONTMATTER_RE = re.compile(r"\A---\n(?P<metadata>.*?)\n---\n\n", re.DOTALL)
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_:]*\Z")
TEMPLATE_ARGUMENTS = r"<(?:[^<>;()\n]|<[^<>;()\n]{0,400}>){0,400}>"
TEMPLATE_ARGUMENTS_RE = re.compile(TEMPLATE_ARGUMENTS)
MAX_CALL_ARGUMENT_LINES = 64
MAX_CALL_ARGUMENT_CHARS = 32_768
CALL_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?P<name>(?:AscendC::)?[A-Za-z_][A-Za-z0-9_:]*)[ \t]*"
    rf"(?:{TEMPLATE_ARGUMENTS})?[ \t]*\("
)
NEGATED_CALL_RE = re.compile(
    r"(?:不|未|没有)(?:会|再|直接|实际)?(?:调用|使用)[^。；;\n]{0,40}$|"
    r"(?:does\s+not|doesn't|do\s+not|don't|without)\s+(?:call(?:ing)?|use|using)"
    r"[^.;\n]{0,40}$",
    re.IGNORECASE,
)
IMPLEMENTATION_NEGATION_RE = re.compile(
    r"(?:没有|未)(?:被)?(?:拆成|写成|实现为|改写为|替换为|采用)"
    r"[^，,。；;\n]{0,80}$"
)
DECLARATION_PREFIX_RE = re.compile(
    r"(?:^|[;{}])\s*"
    r"(?:(?:inline|constexpr|static|const|volatile|__aicore__|__host__)\s+)*"
    r"[A-Za-z_][A-Za-z0-9_:]*(?:\s*<[^;{}()\n]{1,200}>)?"
    r"\s*[*&]?\s*$"
)
FUNCTION_PROTOTYPE_SECTION_RE = re.compile(
    r"(?ms)^##\s+函数原型[^\n]*\n(?P<body>.*?)(?=^##\s|\Z)"
)
MEMBER_RECEIVER_RE = re.compile(
    r"(?:this\s*->\s*)?(?P<receiver>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\.|->)\s*$"
)
OWNER_ALIASES = {
    "custom_t_buf_pool": {"customtbufpool", "bufpool"},
    "global_tensor": {"globaltensor", "global", "gm"},
    "local_tensor": {"localtensor", "local", "ub"},
    "matmul_kernel": {"matmulkernel", "matmul", "mm"},
    "t_buf_pool": {"tbufpool", "bufpool"},
    "t_pipe": {"tpipe", "pipe"},
    "t_que": {"tque", "queue", "que"},
    "t_que_bind": {"tquebind", "queuebind", "quebind"},
    "tscm": {"tscm"},
}


def load_ingest_module():
    module_name = "_cannbot_api_operator_ingest"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    source = Path(__file__).with_name("knowledge_ingest.py")
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ingest support module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ingest = load_ingest_module()
resources = importlib.import_module(f"{ingest.contract_package().__name__}.source_resources")


@dataclass(frozen=True)
class Card:
    path: Path
    relative: str
    title: str
    body: str
    platforms: tuple[str, ...]
    sources: tuple[str, ...] = ()

    @property
    def heading(self) -> str:
        heading = next(
            (line[2:].strip() for line in self.body.splitlines() if line.startswith("# ")),
            self.title,
        )
        heading = re.sub(r"<a\b[^>]*>.*?</a>", "", heading, flags=re.I)
        heading = re.sub(r"<[^>]+>", "", heading).strip()
        return re.sub(r"\\([_:\[\]])", r"\1", heading)

    @property
    def symbol(self) -> str:
        heading = self.heading
        return heading if IDENTIFIER_RE.fullmatch(heading) else self.title

    @property
    def fallback_symbol(self) -> str | None:
        heading = re.split(r"[（(]", self.heading, maxsplit=1)[0].strip()
        return heading if IDENTIFIER_RE.fullmatch(heading) else None

    @property
    def fingerprint(self) -> str:
        value = json.dumps([self.body, self.platforms, self.sources], ensure_ascii=False)
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Invocation:
    api: Card
    operator: Card
    symbol: str
    api_anchor: str
    operator_anchor: str
    confidence: str
    source: dict[str, object] | None = None


def read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def split_card(path: Path, root: Path) -> Card:
    text = read_utf8(path)
    if not text.startswith("---\n"):
        raise ValueError(f"missing frontmatter: {path.relative_to(root)}")
    framing = FRONTMATTER_RE.match(text)
    if framing is None:
        raise ValueError(f"invalid card framing: {path.relative_to(root)}")
    metadata = yaml.safe_load(framing.group("metadata"))
    if not isinstance(metadata, dict) or not isinstance(metadata.get("title"), str):
        raise ValueError(f"invalid card metadata: {path.relative_to(root)}")
    platforms = metadata.get("platforms", [])
    if not isinstance(platforms, list) or not all(
        isinstance(value, str) for value in platforms
    ):
        raise ValueError(f"invalid card platforms: {path.relative_to(root)}")
    body = text[framing.end() :]
    return Card(
        path=path.resolve(),
        relative=path.relative_to(root).as_posix(),
        title=str(metadata["title"]).strip(),
        body=body,
        platforms=tuple(platforms),
        sources=tuple(str(source["resource"]) for source in metadata.get("sources", [])),
    )


def source_mirror(root: Path) -> dict[str, object]:
    contract = ingest.load_contract(root)
    source = contract.local_sources.get("cann_docs_raw")
    if not isinstance(source, dict) or not isinstance(source.get("mirror"), dict):
        raise ValueError("cann_docs_raw is not configured as a fixed document mirror")
    return source["mirror"]


def cards_below(root: Path, relative: str) -> list[Card]:
    base = root / relative
    return [
        split_card(path, root)
        for path in sorted(base.rglob("*.md"))
        if path.name != "index.md"
    ]


def call_names(body: str) -> dict[str, list[re.Match[str]]]:
    result: dict[str, list[re.Match[str]]] = defaultdict(list)
    for match in CALL_RE.finditer(body):
        qualified = match.group("name")
        result[qualified].append(match)
        if "::" in qualified:
            result[qualified.rsplit("::", 1)[1]].append(match)
    return result


def call_shape(body: str, match: re.Match[str]) -> tuple[int, str] | None:
    """Return top-level argument count and normalized arguments."""

    opening = match.end() - 1
    depth = 0
    template_depth = 0
    braces = 0
    brackets = 0
    commas = 0
    has_value = False
    quote_char: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    line_count = 0
    offset = opening + 1
    while offset < len(body):
        if offset - opening > MAX_CALL_ARGUMENT_CHARS:
            return None
        value = body[offset]
        following = body[offset + 1] if offset + 1 < len(body) else ""
        if line_comment:
            if value == "\n":
                line_comment = False
                line_count += 1
            offset += 1
            if line_count > MAX_CALL_ARGUMENT_LINES:
                return None
            continue
        if block_comment:
            if value == "\n":
                line_count += 1
            if value == "*" and following == "/":
                block_comment = False
                offset += 2
            else:
                offset += 1
            if line_count > MAX_CALL_ARGUMENT_LINES:
                return None
            continue
        if quote_char is not None:
            if value == "\n":
                line_count += 1
            if escaped:
                escaped = False
            elif value == "\\":
                escaped = True
            elif value == quote_char:
                quote_char = None
            offset += 1
            if line_count > MAX_CALL_ARGUMENT_LINES:
                return None
            continue
        if value == "/" and following == "/":
            line_comment = True
            offset += 2
            continue
        if value == "/" and following == "*":
            block_comment = True
            offset += 2
            continue
        if value in {'"', "'"}:
            quote_char = value
            has_value = True
        elif value == "(":
            depth += 1
            has_value = True
        elif value == ")":
            if depth == 0:
                arguments = re.sub(
                    r"/\*.*?\*/|//[^\n]*",
                    "",
                    body[opening + 1 : offset],
                    flags=re.DOTALL,
                ).strip()
                if arguments == "void":
                    return 0, arguments
                return (0 if not has_value else commas + 1), arguments
            depth -= 1
        elif value == "<" and TEMPLATE_ARGUMENTS_RE.match(body, offset) is not None:
            template_depth += 1
            has_value = True
        elif value == ">" and template_depth:
            template_depth -= 1
        elif value == "{":
            braces += 1
            has_value = True
        elif value == "}" and braces:
            braces -= 1
        elif value == "[":
            brackets += 1
            has_value = True
        elif value == "]" and brackets:
            brackets -= 1
        elif value == "," and not (depth or template_depth or braces or brackets):
            commas += 1
        elif not value.isspace():
            has_value = True
        if value == "\n":
            line_count += 1
        if line_count > MAX_CALL_ARGUMENT_LINES:
            return None
        offset += 1
    return None


def call_arity(body: str, match: re.Match[str]) -> int | None:
    """Return top-level argument count for a call-like expression."""

    shape = call_shape(body, match)
    return shape[0] if shape is not None else None


def api_arities(api: Card, symbol: str) -> set[int]:
    return {
        arity
        for match in call_names(api.body).get(symbol, [])
        if (arity := call_arity(api.body, match)) is not None
    }


def api_is_variadic(api: Card, symbol: str) -> bool:
    section = FUNCTION_PROTOTYPE_SECTION_RE.search(api.body)
    if section is None:
        return False
    prototype = section.group("body")
    return any(
        shape is not None and "..." in shape[1]
        for match in call_names(prototype).get(symbol, [])
        for shape in (call_shape(prototype, match),)
    )


def constructor_symbols(api: Card) -> tuple[str, ...]:
    """Return constructor identifiers declared by a constructor API card."""

    if "构造" not in api.title and "constructor" not in api.title.casefold():
        return ()
    section = FUNCTION_PROTOTYPE_SECTION_RE.search(api.body)
    if section is None:
        return ()
    symbols: list[str] = []
    for line in section.group("body").splitlines():
        match = CALL_RE.search(line)
        if match is None or call_arity(line, match) is None:
            continue
        symbol = match.group("name").rsplit("::", 1)[-1]
        if symbol not in symbols:
            symbols.append(symbol)
    return tuple(symbols)


def api_qualified_names(api: Card, symbol: str) -> set[str]:
    return {
        normalized_qualified_name(match.group("name"))
        for match in call_names(api.body).get(symbol, [])
        if "::" in match.group("name")
    }


def normalized_qualified_name(value: str) -> str:
    return value.removeprefix("AscendC::")


def identifier_terms(value: str) -> set[str]:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    parts = [part.lower() for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    result = set(parts)
    compact = "".join(parts)
    if compact:
        result.add(compact)
        result.add(re.sub(r"\d+$", "", compact))
    for part in tuple(result):
        if part == "mm":
            result.add("matmul")
        elif part == "gm":
            result.update({"global", "globaltensor"})
        elif part == "ub":
            result.update({"local", "localtensor"})
        elif part == "pipe":
            result.add("tpipe")
        elif part in {"que", "queue"}:
            result.add("tque")
    return {term for term in result if term}


def compact_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value).lower()


def api_owner_terms(api: Card) -> set[str]:
    owner = Path(api.relative).parent.name
    aliases = OWNER_ALIASES.get(owner)
    if aliases is not None:
        return aliases
    base = re.sub(r"_(?:kernel|tiling|interface|functions?)$", "", owner)
    return {compact_identifier(owner), compact_identifier(base)}


def member_receiver(body: str, match: re.Match[str]) -> str | None:
    line_start = body.rfind("\n", 0, match.start()) + 1
    prefix = body[line_start : match.start()].replace("`", "")
    receiver = MEMBER_RECEIVER_RE.search(prefix)
    return receiver.group("receiver") if receiver is not None else None


def receiver_matches_owner(api: Card, receiver: str) -> bool:
    owner = Path(api.relative).parent.name
    compact = compact_identifier(receiver)
    terms = identifier_terms(receiver)
    if owner == "matmul_kernel":
        return "matmul" in terms or re.fullmatch(
            r"(?:mm\d*|matmul[a-z]?\d*)", compact
        ) is not None
    if owner == "global_tensor":
        return bool(terms & {"gm", "global", "globaltensor"})
    if owner == "local_tensor":
        return bool(terms & {"ub", "local", "localtensor"})
    if owner == "t_pipe":
        return re.fullmatch(r"t?pipe(?:ptr)?\d*", compact) is not None
    if owner in {"t_buf_pool", "custom_t_buf_pool"}:
        return "bufpool" in compact
    if owner == "t_que_bind":
        return "bind" in terms and bool(terms & {"que", "queue", "tque"})
    if owner == "t_que":
        return "bind" not in terms and bool(terms & {"que", "queue", "tque"})
    if owner == "tscm":
        return "tscm" in terms
    return compact in api_owner_terms(api)


def call_has_api_owner(api: Card, body: str, match: re.Match[str]) -> bool:
    owners = api_owner_terms(api)
    qualified = normalized_qualified_name(match.group("name"))
    if "::" in qualified:
        qualifier = qualified.rsplit("::", 1)[0].rsplit("::", 1)[-1]
        if compact_identifier(qualifier) in owners:
            return True
    receiver = member_receiver(body, match)
    return receiver is not None and receiver_matches_owner(api, receiver)


def call_has_strong_api_identity(
    api: Card,
    body: str,
    match: re.Match[str],
    qualified_names: set[str],
) -> bool:
    original = match.group("name")
    qualified = normalized_qualified_name(original)
    if "::" in original and qualified in qualified_names:
        return True
    if "/reg_vector_compute/" in f"/{api.relative}" and "::" in original:
        namespace = qualified.rsplit("::", 1)[0] if "::" in qualified else ""
        if namespace in {"MicroAPI", "Reg"}:
            return True
    return call_has_api_owner(api, body, match)


def call_matches_api(
    api: Card,
    body: str,
    match: re.Match[str],
    qualified_names: set[str],
) -> bool:
    """Reject qualified calls that identify a different API family."""

    if "::" not in match.group("name"):
        return True
    qualified = normalized_qualified_name(match.group("name"))
    if "::" not in qualified:
        # ``AscendC::Api(...)`` is the canonical top-level namespace spelling
        # of the same API symbol, not a competing sub-family.
        return True
    qualifier = qualified.rsplit("::", 1)[0]
    if (
        match.start() > 0
        and body[match.start() - 1] == "."
        and qualifier in {"c", "cc", "cpp", "cxx", "h", "hpp"}
    ):
        # Operator cards sometimes anchor a call as
        # ``op_definition.cpp::AICore()``.  The apparent qualifier is a file
        # suffix in a source-location shorthand, not a C++ namespace.
        return True
    if (
        Path(api.relative).parent.name == "op_def"
        and re.fullmatch(r"[A-Z][A-Za-z0-9_]*", qualifier) is not None
    ):
        # Operator definitions commonly document inherited builder calls as
        # ``ConcreteOp::AICore()``.  The capitalized type is a receiver class,
        # not a namespace that identifies a competing API family.
        return True
    return call_has_strong_api_identity(api, body, match, qualified_names)


def platform_compatible(api: Card, operator: Card) -> bool:
    api_platforms = set(api.platforms)
    operator_platforms = set(operator.platforms)
    if "agnostic" in api_platforms or "agnostic" in operator_platforms:
        return True
    if not api_platforms or not operator_platforms:
        return True
    return bool(api_platforms & operator_platforms)


def anchor(body: str, match: re.Match[str]) -> str:
    start = body.rfind("\n", 0, match.start()) + 1
    end = body.find("\n", match.end())
    if end < 0:
        end = len(body)
    value = " ".join(body[start:end].strip().split())
    if len(value) <= 300:
        return value
    call = " ".join(match.group(0).split())
    offset = value.find(call)
    if offset < 0:
        return value[:297] + "..."
    left = max(0, offset - 120)
    right = min(len(value), offset + len(call) + 120)
    return value[left:right]


def is_negated(body: str, match: re.Match[str]) -> bool:
    prefix = body[max(0, match.start() - 100) : match.start()]
    prefix = prefix.replace("`", "")
    return (
        NEGATED_CALL_RE.search(prefix) is not None
        or IMPLEMENTATION_NEGATION_RE.search(prefix) is not None
    )


def is_declaration(body: str, match: re.Match[str]) -> bool:
    line_start = body.rfind("\n", 0, match.start()) + 1
    prefix = body[line_start : match.start()].replace("`", "")
    if re.search(r"\b(?:return|co_return|throw)\s*$", prefix):
        return False
    return DECLARATION_PREFIX_RE.search(prefix) is not None


def api_anchor(api: Card, symbol: str) -> str:
    matches = call_names(api.body).get(symbol, [])
    if matches:
        return anchor(api.body, matches[0])
    heading = next(
        (line.strip() for line in api.body.splitlines() if line.startswith("# ")),
        "",
    )
    if not heading:
        raise ValueError(f"API body has no heading: {api.relative}")
    return heading


SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hxx", ".inl", ".cuh", ".cu"}
CPP_NONCODE_RE = re.compile(
    r'(?P<comment>//(?:\\\r?\n|[^\n])*|/\*.*?(?:\*/|\Z))'
    r'|(?:u8|[uUL])?R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\(.*?\)(?P=delimiter)"'
    r'|(?:u8|[uUL])?"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\\n])*'", re.S,
)
SOURCE_DECLARATION_RE = re.compile(
    r"(?P<type>(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)[ \t]*"
    rf"(?:{TEMPLATE_ARGUMENTS})?[ \t]+(?:[*&][ \t]*)*"
    r"(?P<receiver>[A-Za-z_]\w*)\s*(?=[;,=){])"
)


def mask_source(text: str) -> str:
    """Mask comments, literals, directives and known #if 0 arms; keep offsets."""
    def blank(value: str) -> str:
        return "".join("\n" if char == "\n" else " " for char in value)

    def replace(match: re.Match[str]) -> str:
        value = blank(match.group())
        # A literal still counts as one call argument after its contents are masked.
        return value if match.group("comment") is not None else "0" + value[1:]

    masked = CPP_NONCODE_RE.sub(replace, text)
    active: list[bool] = []
    result: list[str] = []
    continuation = False
    for raw, line in zip(text.splitlines(keepends=True), masked.splitlines(keepends=True)):
        directive = re.match(r"\s*#\s*(\w+)\b(.*)", line)
        if directive:
            name, condition = directive.groups()
            if name in {"if", "ifdef", "ifndef"}:
                active.append(not (name == "if" and re.fullmatch(r"\s*\(?\s*0\s*\)?\s*", condition)))
            elif name in {"else", "elif"} and active:
                # Unknown preprocessing conditions retain both possible arms.
                active[-1] = not (name == "elif" and re.fullmatch(r"\s*0\s*", condition))
            elif name == "endif" and active:
                active.pop()
        if directive or continuation or not all(active):
            result.append(blank(line))
        else:
            result.append(line)
        continuation = bool((directive or continuation) and raw.rstrip("\r\n").endswith("\\"))
    return "".join(result)


def source_receivers(body: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for match in SOURCE_DECLARATION_RE.finditer(body):
        result[match.group("receiver")].add(match.group("type"))
    return result


def source_identity(api: Card, body: str, match: re.Match[str], qualified_names: set[str], receivers: dict[str, set[str]], using_ascendc: bool | None = None) -> bool:
    if using_ascendc is None:
        using_ascendc = re.search(r"\busing\s+namespace\s+AscendC\s*;", body) is not None
    if "::" in match.group("name"):
        original = match.group("name")
        qualified = normalized_qualified_name(original)
        if "::" in qualified and qualified in qualified_names:
            return True
        scope = original.rsplit("::", 1)[0]
        imported_owner = using_ascendc and (
            scope in {"MicroAPI", "Reg"} or compact_identifier(scope) in api_owner_terms(api)
        )
        if original.startswith("AscendC::") or imported_owner:
            # Empty context deliberately disables variable-name heuristics.
            return call_has_strong_api_identity(api, "", match, qualified_names)
        return False
    receiver = member_receiver(body, match)
    types = receivers.get(receiver or "", set())
    if len(types) != 1:
        return False
    owner = next(iter(types))
    if not owner.startswith("AscendC::") and not (
        "::" not in owner and (
            using_ascendc
            or re.search(rf"\busing\s+AscendC::{re.escape(owner)}\s*;", body)
        )
    ):
        return False
    return compact_identifier(owner.rsplit("::", 1)[-1]) in api_owner_terms(api)


def source_inputs(root: Path, operators: list[Card]):
    """Read only declared, tracked C/C++ files from registered pinned snapshots."""
    contract = ingest.load_contract(root)
    definitions = {item["root"]: item for item in contract.local_sources.values() if item.get("kind") == "git"}
    for definition in definitions.values():
        for revision in definition["revisions"]:
            resources.validate_checkout(root, definition, revision)
    owners: dict[str, list[Card]] = defaultdict(list)
    locations = {}
    for operator in operators:
        for resource in operator.sources:
            source = resources.git_source(contract, resource)
            if source is None or Path(source.path).suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if set(Path(source.path).parts) & {"tests", "test", "examples", "docs"}:
                continue
            if operator not in owners[source.resource]:
                owners[source.resource].append(operator)
            locations[source.resource] = source
    manifests: list[dict[str, object]] = []
    tree_cache: dict[Path, dict[str, tuple[str, str]]] = {}
    for resource in sorted(locations):
        source = locations[resource]
        path = source.local_path(root)
        if not path.is_file():
            manifests.append({"resource": resource, "missing": True})
            continue
        checkout = source.checkout(root)
        if checkout not in tree_cache:
            entries = resources.git_read(checkout, "ls-tree", "-rz", source.revision).split("\0")
            tree_cache[checkout] = {}
            for entry in entries:
                if not entry:
                    continue
                attributes, name = entry.split("\t", 1)
                mode, kind, oid = attributes.split()
                if kind == "blob":
                    tree_cache[checkout][name] = (mode, oid)
        mode, oid = tree_cache[checkout].get(source.path, ("", ""))
        data = path.read_bytes()
        actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if mode not in {"100644", "100755"} or actual != oid:
            raise ValueError(f"source file does not match pinned Git blob: {resource}")
        raw = data.decode("utf-8")
        evidence = {"resource": resource, "repository": source.repository, "revision": source.revision, "path": source.path, "sha256": hashlib.sha256(data).hexdigest()}
        manifests.append(evidence)
        yield owners[resource], raw, mask_source(raw), evidence, manifests
    # Include missing/non-matching files in the audit, not just successful edges.
    yield [], "", "", None, manifests


def invocations(
    root: Path,
) -> tuple[list[Card], list[Card], list[Invocation], list[str], dict[str, object]]:
    mirror = source_mirror(root)
    ambiguous = [str(value) for value in mirror["ambiguous_relation_symbols"]]
    ambiguous_set = {compact_identifier(value) for value in ambiguous}
    rejected = {
        (str(value["api"]), str(value["operator"]))
        for value in mirror.get("reviewed_relation_rejections", [])
        if isinstance(value, dict) and "api" in value and "operator" in value
    }
    apis = cards_below(root, "knowledge/ops/ascendc/apis")
    operators = cards_below(root, "knowledge/ops/ascendc/operators")
    by_symbol: dict[str, list[Card]] = defaultdict(list)
    for api in apis:
        if IDENTIFIER_RE.fullmatch(api.symbol):
            by_symbol[api.symbol].append(api)
    strong_symbols = set(by_symbol)
    for api in apis:
        fallback = api.fallback_symbol
        if fallback is not None and fallback not in strong_symbols:
            by_symbol[fallback].append(api)
    constructor_aliases: dict[str, list[Card]] = defaultdict(list)
    for api in apis:
        for symbol in constructor_symbols(api):
            constructor_aliases[symbol].append(api)
    for symbol, constructor_cards in constructor_aliases.items():
        # A navigational class/index page often owns the exact identifier but
        # contains no callable prototype. Route constructor calls to the
        # dedicated constructor card while retaining any genuinely callable
        # same-name cards for the normal ambiguity checks.
        callable_existing = [
            api for api in by_symbol[symbol] if api_arities(api, symbol)
        ]
        by_symbol[symbol] = list(
            dict.fromkeys([*callable_existing, *constructor_cards])
        )
    api_arity_by_key = {
        (api.path, symbol): api_arities(api, symbol)
        for symbol, candidates in by_symbol.items()
        for api in candidates
    }
    api_qualified_by_key = {
        (api.path, symbol): api_qualified_names(api, symbol)
        for symbol, candidates in by_symbol.items()
        for api in candidates
    }
    api_variadic_by_key = {
        (api.path, symbol): api_is_variadic(api, symbol)
        for symbol, candidates in by_symbol.items()
        for api in candidates
    }
    result_by_pair: dict[tuple[Path, Path], Invocation] = {}
    counters: Counter[str] = Counter()
    anchor_cache: dict[tuple[Path, str], str] = {}

    def record_invocation(
        api: Card,
        operator: Card,
        symbol: str,
        selected: re.Match[str],
        confidence: str,
        body: str,
        source: dict[str, object] | None,
        raw: str,
    ) -> None:
        pair = (api.path, operator.path)
        current = result_by_pair.get(pair)
        if current is not None and (source is not None, confidence == "high") <= (current.source is not None, current.confidence == "high"):
            return
        anchor_key = (api.path, symbol)
        if anchor_key not in anchor_cache:
            anchor_cache[anchor_key] = api_anchor(api, symbol)
        source_evidence = None
        if source is not None:
            line = body.count("\n", 0, selected.start()) + 1
            source_evidence = {**source, "line": line, "anchor": raw.splitlines()[line - 1].strip()}
        invocation = Invocation(
            api=api,
            operator=operator,
            symbol=symbol,
            api_anchor=anchor_cache[anchor_key],
            operator_anchor=anchor(body, selected) if source is None else "",
            confidence=confidence,
            source=source_evidence,
        )
        result_by_pair[pair] = invocation

    def collect(operator: Card, body: str, calls, source=None, raw="", receivers=None):
        using_ascendc = source is not None and re.search(r"\busing\s+namespace\s+AscendC\s*;", body) is not None
        imported_symbols = set(re.findall(r"\busing\s+AscendC::([A-Za-z_]\w*)\s*;", body)) if source is not None else set()
        declared = {name for name, matches in calls.items() if any(is_declaration(body, match) for match in matches)} if source is not None else set()
        for symbol in sorted(set(calls) & set(by_symbol)):
            positive = [
                match
                for match in calls[symbol]
                if not is_negated(body, match)
                and not is_declaration(body, match)
            ]
            if not positive:
                continue
            for selected in positive:
                arity = call_arity(body, selected)
                if source is not None and "::" not in selected.group("name") and member_receiver(body, selected) is None and symbol in declared:
                    counters["source_local_shadow"] += 1
                    continue
                identity_family = by_symbol[symbol]
                compatible_family = [
                    api
                    for api in identity_family
                    if (api.relative, operator.relative) not in rejected
                    and platform_compatible(api, operator)
                ]
                identity_pool = [
                    api
                    for api in identity_family
                    if (call_has_strong_api_identity(
                        api,
                        body,
                        selected,
                        api_qualified_by_key[(api.path, symbol)],
                    ) if source is None else source_identity(api, body, selected, api_qualified_by_key[(api.path, symbol)], receivers, using_ascendc))
                ]
                candidates = [
                    api
                    for api in compatible_family
                    if (
                        arity in api_arity_by_key[(api.path, symbol)]
                        or (
                            arity is not None
                            and api_variadic_by_key[(api.path, symbol)]
                        )
                    )
                    and call_matches_api(
                        api,
                        body,
                        selected,
                        api_qualified_by_key[(api.path, symbol)],
                    )
                ]
                # Owner or namespace evidence is only discriminating when it
                # identifies exactly one API card before overload arity is
                # considered. Several directional pages intentionally share a
                # qualified function name; namespace plus arity must not turn
                # those pages into independent, high-confidence matches.
                owned = (
                    [api for api in candidates if api.path == identity_pool[0].path]
                    if len(identity_pool) == 1
                    else []
                )
                if owned:
                    candidates = owned
                    counters["owner_resolved_call_sites"] += 1
                elif compact_identifier(symbol) in ambiguous_set:
                    counters["generic_without_owner"] += 1
                    continue
                elif len(by_symbol[symbol]) > 1:
                    # Platform and arity only reject incompatible overloads;
                    # neither proves which same-name API family owns an
                    # unqualified call. This includes directional pages such as
                    # GM->UB and UB->GM variants. Require namespace or receiver
                    # evidence that is unique across the complete identifier
                    # family, otherwise abstain for this call site.
                    counters["duplicate_without_owner"] += 1
                    continue
                if len(candidates) != 1:
                    counters[
                        "unresolved_ambiguous"
                        if len(candidates) > 1
                        else "filtered_calls"
                    ] += 1
                    continue
                api = candidates[0]
                if source is not None and not owned:
                    if member_receiver(body, selected) is not None or not (
                        selected.group("name") == f"AscendC::{symbol}"
                        or ("::" not in selected.group("name") and using_ascendc)
                        or ("::" not in selected.group("name") and symbol in imported_symbols)
                    ):
                        counters["source_without_api_scope"] += 1
                        continue
                record_invocation(
                    api,
                    operator,
                    symbol,
                    selected,
                    "high" if owned else "medium",
                    body,
                    source,
                    raw,
                )
    for operator in operators:
        collect(operator, operator.body, call_names(operator.body))
    manifests = []
    for source_operators, raw, body, source, manifests in source_inputs(root, operators):
        if source is None:
            continue
        calls = call_names(body)
        receivers = source_receivers(body)
        for operator in source_operators:
            collect(operator, body, calls, source, raw, receivers)
    result = list(result_by_pair.values())
    result.sort(key=lambda item: (item.api.relative, item.operator.relative))
    counters["duplicate_identifier_cards"] = sum(
        len(candidates) for candidates in by_symbol.values() if len(candidates) > 1
    )
    counters["constructor_identifier_aliases"] = sum(
        len(cards) for cards in constructor_aliases.values()
    )
    counters["reviewed_rejections"] = len(rejected)
    counters["source_backed_invocations"] = sum(item.source is not None for item in result)
    counters["source_files"] = sum(not item.get("missing") for item in manifests)
    counters["missing_source_files"] = sum(bool(item.get("missing")) for item in manifests)
    return apis, operators, result, ambiguous, {"counts": dict(counters), "source_files": manifests}


def reason(symbol: str, source: dict[str, object] | None = None) -> str:
    if source is not None:
        return f"算子声明的固定版本源码包含对 `{symbol}(...)` 的直接调用（第 {source['line']} 行）；不表示所有编译分支均执行该调用。"
    return f"算子正文包含对 `{symbol}(...)` 的直接调用；本卡提供该接口契约。"


def invocation_evidence(item: Invocation) -> dict[str, object]:
    evidence: dict[str, object] = {"api_anchor": item.api_anchor}
    if item.source is not None:
        evidence["source"] = item.source
    else:
        evidence["operator_anchor"] = item.operator_anchor
    return evidence


def artifact_payload(
    apis: list[Card],
    operators: list[Card],
    items: list[Invocation],
    ambiguous: list[str],
    audit: dict[str, object],
    limit: int,
) -> dict[str, object]:
    displayed = displayed_invocations(apis, items, limit)
    displayed_pairs = {(item.api.relative, item.operator.relative) for item in displayed}
    return {
        "schema_version": 4,
        "generated_by": "deterministic-explicit-api-invocation-v6",
        "display_limit_per_api": limit,
        "source_files": audit["source_files"],
        "policy": (
            "Prefer direct calls in declared tracked C/C++ source files from clean registered pinned Git snapshots. "
            "Comments, literals, directives and known #if 0 arms are excluded; this is syntactic evidence, "
            "not proof of runtime reachability or exhaustive transitive include coverage. Source evidence binds "
            "repository, revision, path, SHA-256, physical line and exact source anchor. Full accepted pairs "
            "are audited, while optional link suggestions use a deterministic bounded "
            "projection, source-first and round-robin by Operator family. Body-only matches remain separately labeled. "
            "The operator body must contain non-negated, non-declaration call syntax with balanced "
            "template brackets and the identifier, optional template arguments, and opening "
            "parenthesis must remain on one physical line; a sole void prototype parameter has zero "
            "arity; balanced argument lists may span at most 64 physical lines and comments do not "
            "contribute delimiters or arguments; less-than operators only open template nesting when "
            "a bounded balanced template suffix follows; an ellipsis inside the matching function-prototype "
            "parameter list accepts any balanced arity; API arity and "
            "explicit namespace must be compatible; member receivers and API-family namespace "
            "aliases narrow each call site independently and count as strong identity only when they "
            "select one API card across the complete same-symbol family before platform and arity "
            "filtering; platform and arity never establish family identity; a candidate is rejected "
            "for platform scope "
            "only when both scopes are known, concrete, and disjoint; generic symbols require strong "
            "owner evidence using case- and separator-insensitive registry matching; unowned calls for "
            "multi-card symbols and other unresolved calls abstain; capitalized OpDef subclass qualifiers "
            "and .c/.cc/.cpp/.cxx/.h/.hpp source-anchor suffixes are receivers or location anchors rather "
            "than competing namespaces; an exact top-level AscendC namespace prefix is compatible but does "
            "not by itself disambiguate same-symbol cards; constructor cards take callable aliases from the first call-like "
            "declaration on each line of their function-prototype section and replace same-symbol index "
            "cards that have no callable prototype; reviewed rejected pairs are excluded."
        ),
        "api_corpus_fingerprint": hashlib.sha256(
            "".join(f"{card.relative}\0{card.fingerprint}\n" for card in apis).encode("utf-8")
        ).hexdigest(),
        "operator_corpus_fingerprint": hashlib.sha256(
            "".join(
                f"{card.relative}\0{card.fingerprint}\n" for card in operators
            ).encode("utf-8")
        ).hexdigest(),
        "ambiguous_symbols": ambiguous,
        "counts": {
            "api_cards": len(apis),
            "operator_cards": len(operators),
            "api_cards_with_relations": len({item.api.relative for item in items}),
            "accepted_invocations": len(items),
            "displayed_invocations": len(displayed),
            **audit["counts"],
        },
        "relations": [
            {
                "api": item.api.relative,
                "operator": item.operator.relative,
                "relation": "suggested_link",
                "symbol": item.symbol,
                "api_fingerprint": item.api.fingerprint,
                "operator_fingerprint": item.operator.fingerprint,
                "evidence": invocation_evidence(item),
                "reason": reason(item.symbol, item.source),
                "displayed": (item.api.relative, item.operator.relative) in displayed_pairs,
                "confidence": item.confidence,
            }
            for item in items
        ],
    }


def displayed_invocations(apis: list[Card], items: list[Invocation], limit: int) -> list[Invocation]:
    """Bound optional suggestions; graph edges always come from actual card links."""
    if type(limit) is not int or limit < 1:
        raise ValueError("API Operator display limit must be a positive integer")
    grouped: dict[Path, list[Invocation]] = defaultdict(list)
    for item in items:
        grouped[item.api.path].append(item)
    result = []
    for path in sorted(grouped):
        selected = []
        for source_backed in (True, False):
            buckets: dict[str, list[Invocation]] = defaultdict(list)
            for item in sorted(grouped[path], key=lambda value: value.operator.relative):
                if (item.source is not None) == source_backed:
                    parts = Path(item.operator.relative).parts
                    buckets[parts[5] if len(parts) > 5 else ""].append(item)
            for offset in range(max(map(len, buckets.values()), default=0)):
                for family in sorted(buckets):
                    if offset < len(buckets[family]) and len(selected) < limit:
                        selected.append(buckets[family][offset])
        result.extend(selected)
    return result


def command(args: argparse.Namespace) -> int:
    root = ingest.resolve_root(args.knowledge_root)
    report_path = ingest.graph_artifact_path(root, args.report)
    apis, operators, items, ambiguous, audit_counts = invocations(root)
    limit = source_mirror(root)["api_operator_display_limit"]
    payload = artifact_payload(apis, operators, items, ambiguous, audit_counts, limit)
    payload["suggested_markdown"] = [
        {
            "card": item.api.relative,
            "link": f"[{item.operator.title}]({quote(os.path.relpath(item.operator.path, item.api.path.parent), safe='/._-')})",
            "evidence": invocation_evidence(item),
        }
        for item in displayed_invocations(apis, items, limit)
    ]
    ingest.atomic_write(report_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        f"checked_api_cards={len(apis)} accepted_invocations={len(items)} "
        f"suggestions={len(payload['suggested_markdown'])} report={report_path.relative_to(root)}"
    )
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--knowledge-root")
    result.add_argument(
        "--report", default="artifacts/graphs/api_operator_links.json"
    )
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("suggest", help="write optional source-backed link suggestions without editing cards")
    return result


def main() -> int:
    try:
        return command(parser().parse_args())
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
