#!/usr/bin/env python3
# -----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# -----------------------------------------------------------------------------------------------------------

"""Generic component machine-search provisioning for knowledge-query.

Components registered in ``governance/schemas/component_search.yaml`` publish a
machine search skill inside the official raw archive. This module downloads and
verifies that archive once, extracts only the registered component whitelists,
builds or reuses the machine index, and invokes the component's search entry,
returning its native JSON. Every failure becomes a structured status; the caller
decides whether to continue with the original knowledge-query workflow.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import errno
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request

if os.name == "nt":
    import msvcrt
else:
    import fcntl

import yaml

ROOT = Path(__file__).resolve().parents[4]
REGISTRY_RELPATH = "governance/schemas/component_search.yaml"
DEFAULT_COMPONENT = "ascendc-devkit"
DEFAULT_ARCHIVE_URL = (
    "https://ascend.devcloud.huaweicloud.com/artifactory/cann-run-mirror/cann-docs/master/latest/"
)
MAX_CHECKSUMS_BYTES = 64 * 1024
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
DOWNLOAD_CHUNK = 1024 * 1024
SESSION_MAX_FILES = 128
SESSION_MAX_AGE = 7 * 24 * 60 * 60
CHECKSUM_LINE = re.compile(r"([0-9a-fA-F]{64})[ \t]+\*?([^\s/]+\.tar\.gz)[ \t]*$")
TARBALL_LINK = re.compile(r"^[A-Za-z0-9._+-]+\.tar\.gz$")
STRING_FILTERS = (
    "stage",
    "operation",
    "category",
    "api_class",
    "dtype",
    "kw",
    "feature",
    "changed_in",
    "api",
    "deps_of",
    "kind",
    "param",
    "enum",
    "gap",
)


class UnsupportedArchive(ValueError):
    """The official archive exists but cannot support the requested component."""


class RegistryError(ValueError):
    """The component search registry is missing or malformed."""


# Provisioning is best-effort: every failure becomes a structured fallback
# status, never a traceback in the caller's user-facing flow.
PREPARE_ERRORS = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    subprocess.SubprocessError,
    tarfile.TarError,
    EOFError,
    http.client.HTTPException,
)


def run(command, cwd=None, timeout=120):
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def config(key, default="", root=None):
    if os.environ.get(key):
        return os.environ[key]
    base = Path(root).resolve() if root else ROOT
    # Match project knowledge-root configuration without evaluating shell text.
    for parent in (Path.cwd(), *Path.cwd().parents, base):
        path = parent / ".cannbot/knowledge.env"
        if path.is_file():
            for raw in path.read_text(encoding="utf-8").splitlines():
                tokens = shlex.split(raw, comments=True)
                for token in tokens:
                    if token.startswith(key + "="):
                        return token.split("=", 1)[1]
    return default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        temporary = Path(stream.name)
    temporary.replace(path)


def process_session():
    """Use a caller-provided Agent ID, or a persistent non-shell process ancestor."""
    explicit = os.environ.get("CANNBOT_AGENT_SESSION_ID")
    if explicit:
        return explicit
    pid = os.getppid()
    while pid > 1:
        try:
            raw = Path(f"/proc/{pid}/stat").read_text()
            tail = raw[raw.rfind(")") + 2 :].split()
            name = raw.split("(", 1)[1].rsplit(")", 1)[0]
            parent = int(tail[1])
            if name not in {"bash", "sh", "dash", "zsh", "timeout"}:
                return f"{pid}:{tail[19]}"
            pid = parent
        except (OSError, ValueError, IndexError):
            break
    # Unknown launchers do not share a permanent global session.
    return f"invocation:{os.getpid()}"


def archive_base(value):
    """Validate an archive directory URL (or a direct tarball URL)."""
    raw = (value or "").strip()
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("archive URL must be an http(s) URL")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("archive URL must not contain credentials, query or fragment")
    if raw.endswith(".tar.gz"):
        base = raw[: raw.rfind("/") + 1]
        name = raw[raw.rfind("/") + 1 :]
        return base, name
    if not raw.endswith("/"):
        raw += "/"
    return raw, ""


def open_url(url, timeout):
    # Build the opener per request so proxy configuration is read from the
    # current environment (tests and agents may change it in-process).
    opener = urllib.request.build_opener(urllib.request.ProxyHandler())
    request = urllib.request.Request(url, headers={"User-Agent": "cannbot-knowledge-devtools/1"})
    return opener.open(request, timeout=timeout)


def fetch_checksums(base_url, explicit_name=""):
    checksum_url = urllib.parse.urljoin(base_url, "checksums.txt")
    with open_url(checksum_url, timeout=60) as response:
        payload = response.read(MAX_CHECKSUMS_BYTES + 1)
    if len(payload) > MAX_CHECKSUMS_BYTES:
        raise ValueError(f"checksums.txt is unexpectedly large: {checksum_url}")
    entries = []
    for line in payload.decode("utf-8", errors="replace").splitlines():
        match = CHECKSUM_LINE.search(line.strip())
        if match:
            entries.append((match.group(1).lower(), match.group(2)))
    if explicit_name:
        entries = [item for item in entries if item[1] == explicit_name]
    if len(entries) != 1:
        raise ValueError(f"checksums.txt must list exactly one docs archive: {checksum_url}")
    sha256, name = entries[0]
    if not TARBALL_LINK.fullmatch(name):
        raise ValueError(f"refusing unexpected archive name: {name}")
    return sha256, name, urllib.parse.urljoin(base_url, name)


def download_archive(url, sha256, destination):
    if destination.is_file():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=destination.name + ".part-", dir=destination.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        digest = hashlib.sha256()
        size = 0
        try:
            with open_url(url, timeout=300) as response:
                while True:
                    block = response.read(DOWNLOAD_CHUNK)
                    if not block:
                        break
                    size += len(block)
                    if size > MAX_ARCHIVE_BYTES:
                        raise ValueError("archive exceeds the size limit")
                    digest.update(block)
                    stream.write(block)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    if digest.hexdigest() != sha256:
        temporary.unlink(missing_ok=True)
        raise ValueError("archive SHA-256 does not match checksums.txt")
    temporary.replace(destination)
    return destination


def registry_path(root, registry=None):
    if registry:
        return Path(registry).expanduser().resolve()
    return (Path(root).resolve() / REGISTRY_RELPATH)


def validate_component_entry(name, entry):
    prefix = f"components.{name}"

    def require(value, valid, field, expected):
        if not valid(value):
            raise RegistryError(f"{prefix}.{field} must be {expected}")
        return value

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def strings(value):
        return isinstance(value, list) and bool(value) and all(text(item) for item in value)

    for field in ("cache_dir", "archive_prefix"):
        require(entry.get(field), text, field, "a non-empty string")
    require(entry.get("status"), lambda value: value in ("active", "pending"), "status", "active or pending")
    for field in ("extraction", "machine", "index", "search", "coverage"):
        require(entry.get(field), lambda value: isinstance(value, dict), field, "a mapping")
    extraction = entry["extraction"]
    paths = require(extraction.get("paths"), lambda value: isinstance(value, list) and bool(value),
                    "extraction.paths", "a non-empty list of mappings")
    for position, item in enumerate(paths):
        location = f"extraction.paths[{position}]"
        require(item, lambda value: isinstance(value, dict), location, "a mapping with archive and kind")
        for field in ("archive", "kind"):
            require(item.get(field), text, f"{location}.{field}", "a non-empty string")
    if "data_dir" in extraction:
        require(extraction["data_dir"], text, "extraction.data_dir", "a non-empty string")
    if "required_kinds" in extraction:
        require(extraction["required_kinds"], strings, "extraction.required_kinds", "a non-empty string list")
    machine = entry["machine"]
    for field in ("dir", "detect", "build", "search"):
        require(machine.get(field), text, f"machine.{field}", "a non-empty string")
    require(machine.get("required"), strings, "machine.required", "a non-empty string list")
    require(entry["index"].get("build_command"), strings, "index.build_command", "a non-empty string list")
    if "required_files" in entry["index"]:
        def safe_json_paths(value):
            return strings(value) and all(
                not PurePosixPath(item).is_absolute() and ".." not in PurePosixPath(item).parts
                and "\\" not in item and ":" not in item and item.endswith(".json")
                for item in value
            )
        require(entry["index"]["required_files"], safe_json_paths,
                "index.required_files", "a non-empty list of safe relative JSON paths")
    if "validation_command" in entry["index"]:
        require(entry["index"]["validation_command"], strings,
                "index.validation_command", "a non-empty string list")
    if "meta" in entry["index"]:
        require(entry["index"]["meta"], lambda value: isinstance(value, dict)
                and all(text(key) and isinstance(item, str) for key, item in value.items()),
                "index.meta", "a string mapping")
    search = entry["search"]
    require(search.get("schema"), text, "search.schema", "a non-empty string")
    require(search.get("command"), strings, "search.command", "a non-empty string list")
    if "filters" in search:
        raise RegistryError(f"{prefix}.search.filters is unsupported; filters are defined by the CLI")
    if "env" in search:
        require(search["env"], lambda value: isinstance(value, dict)
                and all(text(key) and isinstance(item, str) for key, item in value.items()),
                "search.env", "a string mapping")
    coverage = entry["coverage"]
    for alias in ("pending", "products"):
        if alias in coverage:
            raise RegistryError(f"{prefix}.coverage.{alias} is unsupported; use pending_no_okf/product_markers")
    if "require_products" in coverage:
        require(coverage["require_products"], lambda value: type(value) is bool,
                "coverage.require_products", "a boolean")
    required_coverage = ["doc_count", "pending_no_okf"]
    if coverage.get("require_products", True):
        required_coverage.append("product_markers")
    for field in required_coverage:
        require(coverage.get(field), strings, f"coverage.{field}", "a non-empty string path list")
    if "product_markers" in coverage:
        require(coverage["product_markers"], strings, "coverage.product_markers", "a non-empty string path list")


def load_registry(root, registry=None):
    path = registry_path(root, registry)
    if not path.is_file():
        raise RegistryError(f"component search registry is missing: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryError(f"component search registry is unreadable: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != "component-search/1":
        raise RegistryError(f"component search registry must use schema component-search/1: {path}")
    archive = data.get("archive")
    if not isinstance(archive, dict) or not isinstance(archive.get("url"), str):
        raise RegistryError("component search registry requires archive.url")
    if archive.get("checksums", "checksums.txt") != "checksums.txt":
        raise RegistryError("archive.checksums must be checksums.txt; custom checksum names are unsupported")
    if "env" in archive:
        raise RegistryError("archive.env is unsupported; configure components.<name>.archive_env instead")
    components = data.get("components")
    if not isinstance(components, dict) or not components:
        raise RegistryError("component search registry requires at least one component")
    required_entry = ("status", "cache_dir", "archive_prefix", "extraction", "machine", "index", "search")
    for name, entry in components.items():
        if not isinstance(entry, dict):
            raise RegistryError(f"component registry entry must be a mapping: {name}")
        absent = [field for field in required_entry if field not in entry]
        if absent:
            raise RegistryError(
                f"component registry entry {name} lacks fields: {', '.join(absent)}"
            )
        validate_component_entry(name, entry)
    return data


def component_entry(root, component=DEFAULT_COMPONENT, registry=None):
    data = load_registry(root, registry)
    entry = (data.get("components") or {}).get(component)
    if not isinstance(entry, dict):
        raise RegistryError(f"component is not registered for machine search: {component}")
    required = ("status", "cache_dir", "archive_prefix", "extraction", "machine", "index", "search")
    absent = [name for name in required if name not in entry]
    if absent:
        raise RegistryError(f"component registry entry lacks fields: {', '.join(absent)}")
    return dict(entry)


def active_components(root, registry=None):
    data = load_registry(root, registry)
    return [
        name
        for name, entry in (data.get("components") or {}).items()
        if isinstance(entry, dict) and entry.get("status") == "active"
    ]


def machine_name(entry):
    return str(entry.get("machine_name") or entry["machine"].get("dir", "").rsplit("/", 1)[-1])


def human_extension(entry):
    value = entry.get("human_extension")
    return str(value) if value else ""


def resource_kind(entry, relative):
    extraction = entry["extraction"]
    for item in extraction.get("paths", []):
        prefix = str(item.get("archive", ""))
        if not prefix:
            continue
        if relative == prefix or relative.startswith(prefix + "/"):
            return prefix, str(item.get("kind") or "docs")
    return None, None


def cache_contract_digest(entry):
    contract = {name: entry[name] for name in ("archive_prefix", "extraction", "machine", "index")}
    contract["coverage"] = {
        key: value for key, value in entry.get("coverage", {}).items() if key != "messages"
    }
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def extract_snapshot(archive, staging, sha256, archive_url, entry):
    extraction = entry["extraction"]
    data_dir = str(extraction.get("data_dir") or "component")
    kinds = [str(item.get("kind") or "docs") for item in extraction.get("paths", [])]
    counts = {kind: 0 for kind in kinds}
    sizes = {kind: 0 for kind in kinds}
    prefix_root = entry["archive_prefix"]
    extraction_root = (staging / data_dir).resolve()
    if not extraction_root.is_relative_to(staging.resolve()):
        raise ValueError(f"unsafe extraction directory: {data_dir}")
    with tarfile.open(archive, mode="r:gz") as tar:
        for member in tar:
            name = member.name
            if not name.startswith(prefix_root):
                continue
            relative = name[len(prefix_root) :].rstrip("/")
            if not relative:
                continue
            path = PurePosixPath(relative)
            if (
                path.is_absolute() or ".." in path.parts or "" in path.parts
                or "\\" in relative or ":" in relative
            ):
                raise ValueError(f"unsafe archive path: {name}")
            prefix, kind = resource_kind(entry, relative)
            if prefix is None:
                continue
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"archive resource contains a non-regular entry: {name}")
            if member.isdir():
                continue
            if member.size < 0 or sizes[kind] + member.size > MAX_ARCHIVE_BYTES:
                raise ValueError(f"archive resource exceeds the size limit: {name}")
            target = (extraction_root / relative).resolve()
            if not target.is_relative_to(extraction_root):
                raise ValueError(f"unsafe archive path: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is None:
                raise ValueError(f"cannot read archive entry: {name}")
            with source, target.open("wb") as stream:
                shutil.copyfileobj(source, stream, DOWNLOAD_CHUNK)
            target.chmod(member.mode & 0o755)
            counts[kind] += 1
            sizes[kind] += member.size
    required = extraction.get("required_kinds") or kinds
    missing = [kind for kind in required if not counts.get(kind)]
    messages = entry.get("messages") or {}
    if missing:
        template = messages.get(
            "missing_resources", "archive lacks required component resources: {missing}"
        )
        raise UnsupportedArchive(template.format(missing=", ".join(missing)))
    machine_dir = staging / data_dir / str(entry["machine"]["dir"])
    absent = [
        name for name in entry["machine"].get("required", []) if not (machine_dir / name).is_file()
    ]
    if absent:
        template = messages.get(
            "missing_machine", "official archive lacks the component machine core: {missing}"
        )
        raise UnsupportedArchive(template.format(missing=", ".join(absent)))
    manifest = {
        "archive_url": archive_url,
        "archive_sha256": sha256,
        "cache_contract_sha256": cache_contract_digest(entry),
        "resources": counts,
        "bytes": sizes,
    }
    write_json(staging / ".complete.json", manifest)
    return manifest


def ensure_snapshot(archive, sha256, archive_url, cache, entry, refresh=False):
    data_dir = str(entry["extraction"].get("data_dir") or "component")
    snapshot = cache / "snapshots" / sha256
    marker = snapshot / ".complete.json"
    if marker.is_file() and (snapshot / data_dir).is_dir() and not refresh:
        try:
            manifest = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = None
        if (isinstance(manifest, dict) and manifest.get("archive_sha256") == sha256
            and manifest.get("cache_contract_sha256") == cache_contract_digest(entry)):
            return snapshot / data_dir, manifest
    cache.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="snapshot-", dir=cache))
    try:
        staging = temporary / data_dir
        staging.mkdir()
        manifest = extract_snapshot(archive, temporary, sha256, archive_url, entry)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        if snapshot.exists():
            stale = snapshot.with_name(f"{snapshot.name}.stale-{os.getpid()}")
            snapshot.rename(stale)
            temporary.replace(snapshot)
            shutil.rmtree(stale, ignore_errors=True)
        else:
            temporary.replace(snapshot)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return snapshot / data_dir, manifest


def _link_or_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination
    try:
        os.link(source, destination)
    except OSError:
        shutil.copyfile(source, destination)
    return destination


def resolve_archive(archive_url, cache, shared_downloads=None):
    base, explicit_name = archive_base(archive_url)
    sha256, _, file_url = fetch_checksums(base, explicit_name)
    destination = cache / "downloads" / f"{sha256}.tar.gz"
    if destination.is_file():
        if shared_downloads is not None:
            shared = shared_downloads / f"{sha256}.tar.gz"
            if not shared.is_file():
                _link_or_copy(destination, shared)
        return base, file_url, sha256, destination
    if shared_downloads is not None:
        shared = shared_downloads / f"{sha256}.tar.gz"
        if not shared.is_file():
            download_archive(file_url, sha256, shared)
        _link_or_copy(shared, destination)
    else:
        download_archive(file_url, sha256, destination)
    return base, file_url, sha256, destination


def detect_context(data_root, entry, platform, version):
    machine_dir = data_root / str(entry["machine"]["dir"])
    command = [sys.executable, str(machine_dir / str(entry["machine"]["detect"]))]
    if platform:
        command += ["--platform", platform]
    if version:
        command += ["--cann-version", version]
    process = run(command, timeout=60)
    payload = json.loads(process.stdout)
    if not isinstance(payload, dict) or payload.get("error"):
        raise ValueError("machine core context detection failed")
    return payload


def normalize_version(value):
    if not isinstance(value, str):
        return ""
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", value)
    return match.group(1) if match else ""


def read_index(index_dir, entry):
    marker = str(entry["index"].get("marker") or "index.json")
    path = index_dir / marker
    return json.loads(path.read_text(encoding="utf-8"))


def _values(entry, prepared):
    data_root = Path(prepared["data_root"])
    machine_dir = data_root / str(entry["machine"]["dir"])

    def text(name, default=""):
        value = prepared.get(name)
        return default if value is None else str(value)

    return {
        "python": sys.executable,
        "component": str(entry.get("id") or DEFAULT_COMPONENT),
        "knowledge_root": text("knowledge_root"),
        "data_root": str(data_root),
        "machine_dir": str(machine_dir),
        "machine_skill_dir": str(machine_dir),
        "build_script": str(machine_dir / str(entry["machine"]["build"])),
        "detect_script": str(machine_dir / str(entry["machine"]["detect"])),
        "search_script": str(machine_dir / str(entry["machine"]["search"])),
        "index_dir": text("index_dir"),
        "cache": text("cache"),
        "sha256": text("archive_sha256"),
        "platform": text("platform"),
        "cann_version": text("cann_version"),
        "arch": text("arch"),
        "repository": text("archive_url"),
    }


def expand_command(template, values):
    return [str(item).format(**values) for item in template]


def validate_index(entry, prepared, require_contract=True):
    """Check actual outputs and component freshness before any ready/reuse decision."""
    index_dir = Path(prepared["index_dir"])
    values = _values(entry, prepared)
    if require_contract:
        recorded = json.loads((index_dir / ".component-contract.json").read_text(encoding="utf-8"))
        if recorded != {"cache_contract_sha256": cache_contract_digest(entry)}:
            raise ValueError("index cache contract changed")
    marker = str(entry["index"].get("marker") or "index.json")
    for name in set([marker, *entry["index"].get("required_files", [])]):
        path = index_dir / name
        path.resolve().relative_to(index_dir.resolve())
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"index artifact must be a JSON object: {name}")
    index = read_index(index_dir, entry)
    meta = index.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("machine index meta must be an object")
    for key, value in (entry["index"].get("meta") or {}).items():
        expected = str(value).format(**values)
        if meta.get(key) != expected:
            raise ValueError(f"machine index meta.{key} does not match requested target: {expected}")
    command = entry["index"].get("validation_command")
    if command:
        run(expand_command(command, values), cwd=prepared["data_root"], timeout=120)
    coverage = coverage_report(entry, index)
    for name in ("doc_count", "pending_no_okf"):
        if type(coverage.get(name)) is not int or coverage[name] < 0:
            raise ValueError(f"invalid coverage.{name}")
    return index, coverage


def build_index(data_root, index_dir, entry, sha256, cann_version, arch, context=None):
    contract_marker = index_dir / ".component-contract.json"
    prepared = {
        "data_root": str(data_root),
        "index_dir": str(index_dir),
        "archive_sha256": sha256,
        "cann_version": cann_version,
        "arch": arch,
        **(context or {}),
    }
    try:
        validate_index(entry, prepared)
        return []
    except PREPARE_ERRORS:
        pass
    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    try:
        command = expand_command(entry["index"]["build_command"], _values(entry, prepared))
        run(command, cwd=data_root, timeout=600)
        validate_index(entry, prepared, require_contract=False)
        write_json(contract_marker, {"cache_contract_sha256": cache_contract_digest(entry)})
    except PREPARE_ERRORS:
        shutil.rmtree(index_dir, ignore_errors=True)
        raise
    return ["built"]


def resolve_field(payload, path):
    value = payload
    for part in path:
        value = value[part]
    return value


def coverage_report(entry, index):
    coverage = {}
    spec = entry.get("coverage") or {}
    for name, path in spec.items():
        if name in {"require_products", "messages"}:
            continue
        if not isinstance(path, list):
            continue
        value = resolve_field(index, path)
        if name == "product_markers":
            coverage[name] = len(value) if isinstance(value, (dict, list)) else 0
        else:
            coverage[name] = value
    return coverage


def prune_stale_cache(cache, sha256):
    """Keep only the cache of the current archive snapshot."""
    for name in ("downloads", "snapshots"):
        directory = cache / name
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.name == f"{sha256}.tar.gz" or path.name == sha256:
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
    indices = cache / "indices"
    if indices.is_dir():
        for path in indices.iterdir():
            if path.name == sha256:
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)


def prune_session_cache(cache, now=None):
    """Bound session metadata without touching resource caches; called under the preparation lock."""
    sessions = cache / "sessions"
    if not sessions.is_dir():
        return
    current = time.time() if now is None else now
    retained = []
    for path in sessions.glob("*.json"):
        if not path.is_file():
            continue
        modified = path.stat().st_mtime
        if current - modified > SESSION_MAX_AGE:
            path.unlink(missing_ok=True)
        else:
            retained.append((modified, path.name, path))
    retained.sort()
    for _, _, path in retained[:-SESSION_MAX_FILES]:
        path.unlink(missing_ok=True)


def fallback(status, reason, **details):
    payload = {"status": status, "reason": reason, "fallback": "knowledge-query"}
    payload.update(details)
    return payload


def prepare(
    root,
    component=DEFAULT_COMPONENT,
    registry=None,
    archive_url=None,
    platform=None,
    arch=None,
    version=None,
    cache=None,
    session_id=None,
    refresh=False,
):
    try:
        return _prepare_session(
            root,
            component,
            registry,
            archive_url,
            platform,
            arch,
            version,
            cache,
            session_id,
            refresh,
        )
    except PREPARE_ERRORS as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        return {"status": "error", "error": detail[-4000:], "fallback": "knowledge-query"}


def _prepare_session(
    root,
    component,
    registry,
    archive_url,
    platform,
    arch,
    version,
    cache,
    session_id,
    refresh,
):
    entry = component_entry(root, component, registry)
    if str(entry.get("status") or "pending") != "active":
        return {
            "status": "unavailable",
            "reason": f"component machine search is not active: {component}",
            "fallback": "knowledge-query",
        }
    root = root.resolve()
    artifacts = (root / "artifacts").resolve()
    artifacts.relative_to(root)
    cache_env = str(entry.get("cache_env") or "")
    configured_cache = (
        Path(cache).expanduser()
        if cache
        else Path(
            config(cache_env, str(root / entry["cache_dir"]), root)
            if cache_env
            else str(root / entry["cache_dir"])
        )
    )
    if not configured_cache.is_absolute():
        configured_cache = root / configured_cache
    cache_path = configured_cache.resolve()
    cache_path.relative_to(artifacts)
    archive_env = str(entry.get("archive_env") or "")
    data = load_registry(root, registry)
    default_archive = str((data.get("archive") or {}).get("url") or DEFAULT_ARCHIVE_URL)
    archive_url = archive_url or (
        config(archive_env, default_archive, root) if archive_env else default_archive
    )
    if not archive_url or archive_url.startswith("-"):
        raise ValueError("invalid archive URL")
    session_id = session_id or process_session()
    persistent_session = not str(session_id).startswith("invocation:")
    session_key = hashlib.sha256(
        json.dumps([component, archive_url, session_id, platform, arch, version,
                cache_contract_digest(entry)]).encode()
    ).hexdigest()[:32]
    session_path = cache_path / "sessions" / (session_key + ".json")
    with preparation_lock(cache_path):
        prune_session_cache(cache_path)
        if persistent_session and not refresh and session_path.is_file():
            try:
                cached = json.loads(session_path.read_text(encoding="utf-8"))
                snapshot_manifest = json.loads(
                    (Path(cached["data_root"]).parent / ".complete.json").read_text(encoding="utf-8")
                )
                index_contract = json.loads(
                    (Path(cached["index_dir"]) / ".component-contract.json").read_text(encoding="utf-8")
                )
            except (OSError, ValueError, KeyError, TypeError):
                cached = None
            if isinstance(cached, dict):
                if cached.get("status") == "ready" and Path(cached.get("index_dir", "")).is_dir() and Path(
                    cached.get("data_root", "")
                ).is_dir() and isinstance(snapshot_manifest, dict) and (
                    snapshot_manifest.get("archive_sha256") == cached.get("archive_sha256")
                    and snapshot_manifest.get("cache_contract_sha256") == cache_contract_digest(entry)
                    and index_contract == {"cache_contract_sha256": cache_contract_digest(entry)}
                ):
                    try:
                        _, coverage = validate_index(entry, cached)
                        supported = (coverage["doc_count"] > 0 and coverage["pending_no_okf"] == 0
                                     and (not entry["coverage"].get("require_products", True)
                                          or coverage.get("product_markers", 0) > 0))
                        if supported and coverage == cached.get("coverage"):
                            return cached
                    except PREPARE_ERRORS:
                        pass
            session_path.unlink(missing_ok=True)
        shared_downloads = None
        download_cache = (data.get("archive") or {}).get("download_cache")
        if download_cache:
            shared_downloads = (root / str(download_cache)).resolve()
            shared_downloads.relative_to(artifacts)
        try:
            result = _prepare(
                cache_path,
                entry,
                archive_url,
                platform,
                arch,
                version,
                refresh,
                shared_downloads=shared_downloads,
            )
        except PREPARE_ERRORS as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            result = {
                "status": "error",
                "error": detail[-4000:],
                "fallback": "knowledge-query",
            }
        if persistent_session and result.get("status") == "ready":
            write_json(session_path, result)
            prune_session_cache(cache_path)
        else:
            session_path.unlink(missing_ok=True)
        return result


def _prepare(cache, entry, archive_url, platform, arch, version, refresh, shared_downloads=None):
    base, file_url, sha256, archive = resolve_archive(archive_url, cache, shared_downloads)
    try:
        data_root, manifest = ensure_snapshot(archive, sha256, file_url, cache, entry, refresh)
    except UnsupportedArchive as exc:
        return fallback(
            "unsupported",
            str(exc),
            archive_url=base,
            archive_file=file_url,
            archive_sha256=sha256,
        )
    context = detect_context(data_root, entry, platform, version)
    resolved_platform = platform or context.get("platform")
    resolved_version = normalize_version(version or context.get("cann_version") or "")
    resolved_arch = arch or context.get("arch")
    if arch and context.get("arch") and arch != context.get("arch"):
        raise ValueError("explicit architecture conflicts with the target platform")
    details = {
        "archive_url": base,
        "archive_file": file_url,
        "archive_sha256": sha256,
        "data_root": str(data_root),
        "resources": manifest.get("resources", {}),
    }
    if not resolved_platform or not resolved_version or not resolved_arch:
        return fallback(
            "needs_context",
            "platform or CANN version is not confirmed",
            context=context,
            **details,
        )
    prune_stale_cache(cache, sha256)
    surface = str(entry["index"].get("surface") or "default")
    index_dir = cache / "indices" / sha256 / resolved_version / str(resolved_arch) / surface
    actions = build_index(
        data_root,
        index_dir,
        entry,
        sha256,
        resolved_version,
        str(resolved_arch),
        context={"knowledge_root": str(cache.parent.parent), "cache": str(cache)},
    )
    index = read_index(index_dir, entry)
    coverage = coverage_report(entry, index)
    messages = (entry.get("coverage") or {}).get("messages") or {}
    if not coverage.get("doc_count"):
        return fallback(
            "unsupported",
            str(messages.get("empty") or "official archive has no usable knowledge heads"),
            coverage=coverage,
            **details,
        )
    if coverage.get("pending_no_okf"):
        template = str(
            messages.get("pending")
            or "official archive documents lack usable knowledge heads ({pending_no_okf} pending)"
        )
        return fallback(
            "unsupported",
            template.format(**coverage),
            coverage=coverage,
            **details,
        )
    require_products = bool((entry.get("coverage") or {}).get("require_products", True))
    if require_products and not coverage.get("product_markers"):
        return fallback(
            "unsupported",
            str(
                messages.get("products")
                or "official archive documents lack product support markers"
            ),
            coverage=coverage,
            **details,
        )
    return {
        "status": "ready",
        **details,
        "index_dir": str(index_dir),
        "machine_skill_dir": str(data_root / str(entry["machine"]["dir"])),
        "search_script": str(
            data_root / str(entry["machine"]["dir"]) / str(entry["machine"]["search"])
        ),
        "machine_name": machine_name(entry),
        "platform": resolved_platform,
        "cann_version": resolved_version,
        "arch": str(resolved_arch),
        "coverage": coverage,
        "index_actions": actions,
        "context": context,
    }


@contextmanager
def preparation_lock(cache):
    """Serialize cache preparation across processes on Windows and Unix."""
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / "prepare.lock").open("a+b", buffering=0) as lock:
        if os.name == "nt":
            # Every process locks the same byte, including on an empty new file.
            while True:
                try:
                    if os.fstat(lock.fileno()).st_size == 0:
                        lock.write(b"\0")
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                        raise
                    time.sleep(0.1)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


def build_search_command(entry, prepared, filters):
    values = {
        "python": sys.executable,
        "component": str(entry.get("id") or DEFAULT_COMPONENT),
        "data_root": str(prepared["data_root"]),
        "index_dir": str(prepared["index_dir"]),
        "machine_dir": str(prepared["machine_skill_dir"]),
        "machine_skill_dir": str(prepared["machine_skill_dir"]),
        "search_script": str(prepared["search_script"]),
        "platform": str(prepared["platform"]),
        "cann_version": str(prepared["cann_version"]),
        "arch": str(prepared["arch"]),
        "repository": str(prepared["archive_url"]),
        "sha256": str(prepared["archive_sha256"]),
    }
    command = expand_command(entry["search"]["command"], values)
    for name in STRING_FILTERS:
        value = (filters or {}).get(name)
        if value is not None and value != "":
            command += ["--" + name.replace("_", "-"), str(value)]
    convert = (filters or {}).get("convert")
    if convert:
        command += ["--convert", str(convert[0]), str(convert[1])]
    if (filters or {}).get("reverse"):
        command.append("--reverse")
    keywords = (filters or {}).get("keywords")
    if keywords:
        command += ["--keywords", *[str(value) for value in keywords]]
    limit = (filters or {}).get("limit")
    if limit is not None:
        command += ["--limit", str(limit)]
    return command


def validate_result(entry, result):
    schema = str(entry["search"].get("schema") or "")
    if not isinstance(result, dict) or result.get("schema") != schema:
        raise ValueError(f"component search must return {schema} JSON")
    rows = result.get("results")
    if not isinstance(rows, list) or any(
        not isinstance(row, dict)
        or not (
            isinstance(row.get("path"), str)
            and row["path"]
            or isinstance(row.get("gap_id"), str)
            and row["gap_id"]
        )
        for row in rows
    ):
        raise ValueError("component search must return a valid results list")
    if type(result.get("count")) is not int or result["count"] != len(rows):
        raise ValueError("component search count must match its results list")


def fallback_payload(entry, prepared):
    reason = (
        prepared.get("reason")
        or prepared.get("error")
        or f"{entry.get('label') or entry.get('id') or 'component'} search is unavailable"
    )
    return {
        "status": prepared.get("status", "error"),
        "reason": reason,
        "fallback": "knowledge-query",
    }


def search(
    root,
    component=DEFAULT_COMPONENT,
    registry=None,
    filters=None,
    platform=None,
    version=None,
    archive_url=None,
    session_id=None,
    refresh=False,
):
    try:
        entry = component_entry(root, component, registry)
    except PREPARE_ERRORS as exc:
        return {"status": "error", "reason": str(exc), "fallback": "knowledge-query"}
    prepared = prepare(
        root,
        component=component,
        registry=registry,
        archive_url=archive_url,
        platform=platform,
        version=version,
        cache=None,
        session_id=session_id,
        refresh=refresh,
    )
    if prepared.get("status") != "ready":
        return fallback_payload(entry, prepared)
    command = build_search_command(entry, prepared, filters or {})
    try:
        process = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=300,
            env={**os.environ, **(entry["search"].get("env") or {})},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "error", "error": str(exc), "fallback": "knowledge-query"}
    try:
        payload = json.loads(process.stdout)
    except ValueError:
        payload = None
    if process.returncode != 0 or payload is None:
        detail = (process.stderr or process.stdout or "machine search failed")[-3000:]
        return {"status": "error", "error": detail, "fallback": "knowledge-query"}
    try:
        validate_result(entry, payload)
    except ValueError as exc:
        return {"status": "error", "error": str(exc), "fallback": "knowledge-query"}
    return payload


def capabilities(root, component=DEFAULT_COMPONENT, registry=None):
    try:
        data = load_registry(root, registry)
        entry = component_entry(root, component, registry)
    except PREPARE_ERRORS as exc:
        path = registry_path(root, registry)
        missing = [] if Path(path).is_file() else [str(path)]
        return {
            "available": False,
            "missing": missing,
            "status": "unavailable",
            "error": str(exc),
        }
    status = str(entry.get("status") or "pending")
    return {
        "available": status == "active",
        "missing": [],
        "status": status,
        "machine_skill": machine_name(entry),
        "human_extension": human_extension(entry),
        "components": active_components(root, registry),
        "archive": str((data.get("archive") or {}).get("url") or ""),
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "search", "capabilities"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--knowledge-root", type=Path, default=ROOT)
        sub.add_argument("--registry", type=Path)
        sub.add_argument("--component", default=DEFAULT_COMPONENT)
        if name == "prepare":
            sub.add_argument("--archive-url")
            sub.add_argument("--platform")
            sub.add_argument("--arch")
            sub.add_argument("--cann-version")
            sub.add_argument("--cache", type=Path)
            sub.add_argument("--session-id")
            sub.add_argument("--refresh", action="store_true")
        if name == "search":
            sub.add_argument("--archive-url")
            sub.add_argument("--platform")
            sub.add_argument("--cann-version")
            sub.add_argument("--session-id")
            sub.add_argument("--refresh", action="store_true")
            sub.add_argument("--stage")
            sub.add_argument("--operation")
            sub.add_argument("--category")
            sub.add_argument("--api-class", dest="api_class")
            sub.add_argument("--dtype")
            sub.add_argument("--kw")
            sub.add_argument("--convert", nargs=2, metavar=("SRC", "DST"))
            sub.add_argument("--feature")
            sub.add_argument("--changed-in", dest="changed_in")
            sub.add_argument("--api")
            sub.add_argument("--deps-of", dest="deps_of")
            sub.add_argument("--kind")
            sub.add_argument("--reverse", action="store_true")
            sub.add_argument("--param")
            sub.add_argument("--enum")
            sub.add_argument("--gap")
            sub.add_argument("--keywords", nargs="+")
            sub.add_argument("--limit", type=int)
    return parser


def _filters_from_args(args):
    filters = {}
    for name in STRING_FILTERS:
        value = getattr(args, name, None)
        if value is not None:
            filters[name] = value
    if getattr(args, "convert", None):
        filters["convert"] = list(args.convert)
    if getattr(args, "reverse", None):
        filters["reverse"] = True
    if getattr(args, "keywords", None):
        filters["keywords"] = list(args.keywords)
    if getattr(args, "limit", None) is not None:
        filters["limit"] = args.limit
    return filters


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capabilities":
            result = capabilities(args.knowledge_root, args.component, args.registry)
            code = 0
        elif args.command == "prepare":
            result = prepare(
                args.knowledge_root,
                component=args.component,
                registry=args.registry,
                archive_url=args.archive_url,
                platform=args.platform,
                arch=args.arch,
                version=args.cann_version,
                cache=args.cache,
                session_id=args.session_id,
                refresh=args.refresh,
            )
            code = 0 if result.get("status") == "ready" else 2 if result.get("status") == "error" else 1
        else:
            result = search(
                args.knowledge_root,
                component=args.component,
                registry=args.registry,
                filters=_filters_from_args(args),
                platform=args.platform,
                version=args.cann_version,
                archive_url=args.archive_url,
                session_id=args.session_id,
                refresh=args.refresh,
            )
            code = 0 if result.get("schema") else 2
        print(json.dumps(result, ensure_ascii=False))
        return code
    except PREPARE_ERRORS as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        print(json.dumps({"status": "error", "error": detail, "fallback": "knowledge-query"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
