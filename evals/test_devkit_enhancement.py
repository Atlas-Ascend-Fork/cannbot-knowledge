# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------
"""Offline regression for component resource preparation and cache contracts.

A loopback archive containing a stub machine core exercises the generic
provisioner directly. No human extension, router, official network access or
installed Ascend environment is required.
"""
from __future__ import annotations

import hashlib
import http.server
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_SEARCH = ROOT / ".agents/skills/knowledge-query/scripts/component_search.py"
REGISTRY = ROOT / "governance/schemas/component_search.yaml"

ARCHIVE_ROOT = "asc-devkit"
ARCHIVE_PREFIX = ARCHIVE_ROOT + "/"
ARCHIVE_NAME = "asc-devkit-fixture.tar.gz"
OFFLINE_PROXY = {"no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost"}
MACHINE_ROOT = ".agent/skills/asc-search"
MACHINE_SCRIPTS = MACHINE_ROOT + "/scripts"
MACHINE_SEARCH = MACHINE_SCRIPTS + "/search.py"
DEMO_DOC = "docs/zh/api/SIMD-API/c_api/demo.md"


def module(name, path):
    """Load one implementation file by path, as the former regression did."""
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


component_search = module("component_prepare_fixture", COMPONENT_SEARCH)


STUB_DETECT_CONTEXT = textwrap.dedent(
    '''\
    #!/usr/bin/env python3
    """Offline stub: report a fixed or deliberately unknown target context."""
    import argparse
    import json
    import os


    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("--platform")
        parser.add_argument("--cann-version")
        args = parser.parse_args()
        if os.environ.get("STUB_CONTEXT_EMPTY") == "1":
            print(json.dumps({"platform": None, "arch": None, "cann_version": ""}))
            return
        print(
            json.dumps(
                {
                    "platform": args.platform or "950",
                    "arch": "3510",
                    "cann_version": args.cann_version or "9.2.0",
                }
            )
        )


    if __name__ == "__main__":
        main()
    '''
)

STUB_BUILD_INDEX = textwrap.dedent(
    '''\
    #!/usr/bin/env python3
    """Offline stub: write a machine index with configurable coverage."""
    import argparse
    import hashlib
    import json
    import os
    from pathlib import Path
    from types import SimpleNamespace


    SKILL_ROOT = Path(__file__).resolve().parents[1]
    SCOPES = dict(c_api=SimpleNamespace(root="docs/zh", categories=None))

    def input_fingerprints(root):
        sources = list((root / "include/c_api").rglob("*.h"))
        sources += [p for p in (root / "examples").rglob("*")
                    if p.is_file() and p.suffix.lower() in (".asc", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp")]
        result = dict(("repo/" + p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
                      for p in sorted(sources))
        scripts = list((SKILL_ROOT / "scripts").rglob("*.py"))
        scripts += list((SKILL_ROOT / "derive-overrides").glob("*.json"))
        result.update(("skill/" + p.relative_to(SKILL_ROOT).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
                      for p in sorted(scripts))
        return result


    def _int(name, default):
        raw = os.environ.get(name)
        return default if raw is None else int(raw)


    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("--root", required=True)
        parser.add_argument("--out", required=True)
        parser.add_argument("--cann-version", required=True)
        parser.add_argument("--arch", required=True)
        parser.add_argument("--source-commit", required=True)
        args = parser.parse_args()
        root = Path(args.root)
        docs = sorted((root / "docs").rglob("*.md"))
        by_product = {
            "product-%d" % (index + 1): [str(path.relative_to(root)) for path in docs]
            for index in range(_int("STUB_PRODUCT_COUNT", 1))
        }
        index = {
            "schema": "okf-index/5",
            "documents": dict((p.relative_to(root).as_posix(), dict()) for p in docs),
            "scope": dict(primary_docs=[p.relative_to(root).as_posix() for p in docs], navigation_pages=[]),
            "meta": {
                "doc_count": _int("STUB_DOC_COUNT", max(0, len(docs) - _int("STUB_PENDING_NO_OKF", 0))),
                "pending_no_okf": _int("STUB_PENDING_NO_OKF", 0),
                "source_commit": args.source_commit,
                "cann_version": args.cann_version,
                "arch": args.arch,
                "arch_label": args.arch,
                "surface": "c_api",
                "filtered_by_version": max(0, len(docs) - _int("STUB_DOC_COUNT", len(docs)) - _int("STUB_PENDING_NO_OKF", 0)),
                "filtered_by_arch": 0,
            },
            "views": {"by_product": by_product},
        }
        if os.environ.get("STUB_BAD_META") == "1":
            index["meta"] = []
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
        gaps = b'{"scope_out_gaps": [], "relation_gaps": []}'
        (out / "gaps.json").write_bytes(gaps)
        meta = dict(
            schema="okf-index-meta/2",
            source_commit=args.source_commit,
            taxonomy_sha256=hashlib.sha256((SKILL_ROOT / "config/tag-taxonomy.json").read_bytes()).hexdigest(),
            product_map_sha256=hashlib.sha256((SKILL_ROOT / "config/product-map.yaml").read_bytes()).hexdigest(),
            gaps_sha256=hashlib.sha256(gaps).hexdigest(),
            input_sha256=input_fingerprints(root),
            document_sha256=dict((p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in docs),
        )
        (out / "build-meta.json").write_text(json.dumps(meta), encoding="utf-8")


    if __name__ == "__main__":
        main()
    '''
)

STUB_SEARCH = textwrap.dedent(
    '''\
    #!/usr/bin/env python3
    """Offline stub: return one machine result and echo the received arguments."""
    import json
    import os
    import sys


    def main():
        payload = {
            "schema": "asc-search-results/1",
            "count": 1,
            "results": [
                {
                    "path": "docs/zh/api/SIMD-API/c_api/demo.md",
                    "why": ["stub"],
                    "argv": sys.argv[1:],
                }
            ],
            "no_llm": os.environ.get("ASC_SEARCH_NO_LLM"),
        }
        if os.environ.get("STUB_SEARCH_BAD_COUNT") == "1":
            payload["count"] = 2
        print(json.dumps(payload))


    if __name__ == "__main__":
        main()
    '''
)

STUB_ENSURE_INDEX = '''\
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any
import build_index
Scope = object
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "config/tag-taxonomy.json"
PRODUCT_MAP_PATH = Path(__file__).resolve().parents[1] / "config/product-map.yaml"
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def gate_reasons(meta: dict[str, Any], surface: str, cann_version: str, arch_label: str) -> list[str]:
    reasons = []
    if meta.get("surface") != surface:
        reasons.append(f"surface {meta.get('surface')!r} != {surface!r}")
    if meta.get("cann_version") != cann_version:
        reasons.append(f"cann {meta.get('cann_version')} != {cann_version}")
    if meta.get("arch_label") != arch_label:
        reasons.append(f"arch {meta.get('arch_label')} != {arch_label}")
    return reasons

def scope_documents(root: Path, scope: Scope) -> list[str]:
    """scope 内全部 .md（与 load_documents 同一范围语义，含未打头文档）。"""
    base = len(PurePosixPath(scope.root).parts)
    out = []
    for path in sorted((root / scope.root).rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        parts = PurePosixPath(rel).parts
        if scope.categories is not None and (len(parts) <= base or parts[base] not in scope.categories):
            continue
        out.append(rel)
    return out

def light_fresh(instance: Path, root: Path, scope: Scope) -> tuple[bool, list[str]]:
    """轻量指纹：build-meta 哈希逐项 + scope 文档数，毫秒级。"""
    reasons: list[str] = []
    meta_path = instance / "build-meta.json"
    if not meta_path.is_file():
        return False, ["build-meta.json missing"]
    fingerprint = json.loads(meta_path.read_text(encoding="utf-8"))
    for key, path in (
        ("taxonomy_sha256", TAXONOMY_PATH),
        ("product_map_sha256", PRODUCT_MAP_PATH),
        ("gaps_sha256", instance / "gaps.json"),
    ):
        expected = fingerprint.get(key)
        if expected is None:
            reasons.append(f"build-meta missing {key}")
        elif expected != sha256(path):
            reasons.append(f"{key} drift: {path.name} changed since build")
    if fingerprint.get("input_sha256") != build_index.input_fingerprints(root):
        reasons.append("include/examples/scripts/overrides inputs changed since build")
    docs = fingerprint.get("document_sha256")
    if not docs:
        reasons.append("build-meta has no document_sha256")
        docs = {}
    for rel, digest in sorted(docs.items()):
        path = root / rel
        if not path.is_file():
            reasons.append(f"document removed: {rel}")
        elif sha256(path) != digest:
            reasons.append(f"document changed: {rel}")
    index_meta = json.loads((instance / "index.json").read_text(encoding="utf-8"))["meta"]
    expected_count = (
        index_meta["doc_count"]
        + index_meta["pending_no_okf"]
        + index_meta["filtered_by_version"]
        + index_meta["filtered_by_arch"]
    )
    actual = len(scope_documents(root, scope))
    if actual != expected_count:
        reasons.append(f"scope document count {actual} != {expected_count} (docs added/removed since build)")
    return (not reasons), reasons
'''
STUB_QUERY = '''\
import json
from pathlib import Path
def load(index_dir):
    return tuple(json.loads((Path(index_dir) / name).read_text()) for name in ("index.json", "gaps.json"))
'''

FIXTURE_FILES = {
    MACHINE_ROOT + "/SKILL.md": "# asc-search machine core (offline stub)\n",
    MACHINE_ROOT + "/config/product-map.yaml": "products:\n  - 950\n",
    MACHINE_ROOT + "/config/tag-taxonomy.json": '{"tags": ["vector"]}\n',
    MACHINE_SCRIPTS + "/detect_context.py": STUB_DETECT_CONTEXT,
    MACHINE_SCRIPTS + "/build_index.py": STUB_BUILD_INDEX,
    MACHINE_SEARCH: STUB_SEARCH,
    MACHINE_SCRIPTS + "/ensure_index.py": STUB_ENSURE_INDEX,
    MACHINE_SCRIPTS + "/query.py": STUB_QUERY,
    DEMO_DOC: '---\nokf_type: "reference.api"\n---\n\n# demo\n',
    # 知识头 dependency 目标可能位于 docs/zh 下 C API 目录之外。
    "docs/zh/guide/programming_guide/language_extension/simd_builtin_keywords.md": "# stub guide\n",
    "include/c_api/demo.h": "#pragma once\n",
    "examples/02_simd_c_api/demo.asc": "// stub example\n",
    "secret.txt": "outside the extraction whitelist\n",
}


def tar_member(name, payload):
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mode = 0o644
    return info, payload


def tar_symlink(name, target):
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    info.mode = 0o777
    return info, None


def write_archive(target, *, omit=(), extra_files=None, extra_members=()):
    """Create a fake official archive below ``target`` and return the tarball path."""
    target.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="fixture-archive-", dir=target))
    devkit = staging / ARCHIVE_ROOT
    files = dict(FIXTURE_FILES)
    files.update(extra_files or {})
    for relative, content in files.items():
        if relative in omit:
            continue
        path = devkit / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if relative.startswith(MACHINE_SCRIPTS + "/"):
            path.chmod(0o755)
    archive = staging / ARCHIVE_NAME
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(devkit, arcname=ARCHIVE_ROOT)
        for member, payload in extra_members:
            if payload is None:
                tar.addfile(member)
            else:
                tar.addfile(member, io.BytesIO(payload))
    return archive


class FixtureServer:
    """Serve one directory over loopback HTTP and record every requested path."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.requests = []
        self._lock = threading.Lock()
        record = self._record
        directory_text = str(self.directory)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory_text, **kwargs)

            def log_message(self, format, *args):
                pass

            def do_GET(self):
                record(self.path)
                super().do_GET()

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def _record(self, path):
        with self._lock:
            self.requests.append(path)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.httpd.server_address[1]}/latest/"

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


class DevkitOfflineCase(unittest.TestCase):
    """Loopback archive server, temporary knowledge root and offline proxy settings."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.knowledge_root = self.base / "knowledge"
        self.knowledge_root.mkdir()
        self.publish_dir = self.base / "remote/latest"
        self.publish_dir.mkdir(parents=True)
        self.server = FixtureServer(self.base / "remote")
        self.addCleanup(self.server.stop)
        proxy_patch = patch.dict(os.environ, OFFLINE_PROXY)
        proxy_patch.start()
        self.addCleanup(proxy_patch.stop)
        self.artifacts = (self.knowledge_root / "artifacts").resolve()
        self.sha = self.publish_archive()

    @property
    def cache(self):
        return self.artifacts / "ascendc-devkit"

    def publish_archive(self, *, omit=(), extra_files=None, extra_members=()):
        archive = write_archive(
            self.base / "archives",
            omit=omit,
            extra_files=extra_files,
            extra_members=extra_members,
        )
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        shutil.copyfile(archive, self.publish_dir / ARCHIVE_NAME)
        (self.publish_dir / "checksums.txt").write_text(
            f"{digest}  {ARCHIVE_NAME}\n", encoding="utf-8"
        )
        return digest

    def prepare(self, *, session="session", platform="950", version="9.2.0", arch=None, refresh=False):
        return component_search.prepare(
            self.knowledge_root,
            registry=REGISTRY,
            archive_url=self.server.url,
            platform=platform,
            arch=arch,
            version=version,
            session_id=session,
            refresh=refresh,
        )

    @staticmethod
    def files(root):
        return {path.relative_to(root).as_posix() for path in Path(root).rglob("*") if path.is_file()}

    def assert_status(self, result, status):
        self.assertEqual(
            result.get("status"),
            status,
            json.dumps(result, ensure_ascii=False)[:2000],
        )

    def assert_stays_in_artifacts(self, before):
        created = self.files(self.knowledge_root) - before
        outside = {path for path in created if not path.startswith("artifacts/")}
        self.assertEqual(outside, set(), created)


class PreparationTests(DevkitOfflineCase):
    def test_ready_prepare_downloads_verifies_and_extracts_whitelisted_resources(self):
        before = self.files(self.knowledge_root)
        self.assertEqual(before, set())
        result = self.prepare(session="ready")
        self.assert_status(result, "ready")
        data_root = Path(result["data_root"])
        index_dir = Path(result["index_dir"])
        search_script = Path(result["search_script"])
        for path in (data_root, index_dir, search_script):
            self.assertTrue(path.is_absolute(), path)
            self.assertTrue(path.exists(), path)
        self.assertTrue(data_root.is_relative_to(self.artifacts))
        self.assertTrue(index_dir.is_relative_to(self.artifacts))
        self.assertEqual(search_script, data_root / MACHINE_SEARCH)
        if os.name != "nt":
            self.assertTrue(search_script.stat().st_mode & 0o100)
        started = subprocess.run(
            [sys.executable, str(search_script)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(json.loads(started.stdout)["schema"], "asc-search-results/1")
        self.assertEqual(result["archive_url"], self.server.url)
        self.assertEqual(result["archive_sha256"], self.sha)
        self.assertEqual(result["platform"], "950")
        self.assertEqual(result["cann_version"], "9.2.0")
        self.assertEqual(result["arch"], "3510")
        self.assertEqual(
            result["resources"],
            {"machine": 8, "docs": 2, "include": 1, "examples": 1},
        )
        for relative in (
            MACHINE_ROOT + "/SKILL.md",
            MACHINE_ROOT + "/config/product-map.yaml",
            MACHINE_ROOT + "/config/tag-taxonomy.json",
            MACHINE_SCRIPTS + "/detect_context.py",
            MACHINE_SCRIPTS + "/build_index.py",
            DEMO_DOC,
            "docs/zh/guide/programming_guide/language_extension/simd_builtin_keywords.md",
            "include/c_api/demo.h",
            "examples/02_simd_c_api/demo.asc",
        ):
            self.assertTrue((data_root / relative).is_file(), relative)
        self.assertNotIn("secret.txt", self.files(data_root))
        self.assertEqual(
            result["coverage"],
            {"doc_count": 2, "pending_no_okf": 0, "product_markers": 1},
        )
        self.assertEqual(result["index_actions"], ["built"])
        index = json.loads((index_dir / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["meta"]["source_commit"], f"artifact:{self.sha}")
        self.assertEqual(index["meta"]["cann_version"], "9.2.0")
        self.assertEqual(index["meta"]["arch"], "3510")
        self.assertEqual(data_root, self.cache / "snapshots" / self.sha / "devkit")
        self.assertTrue((self.cache / "downloads" / f"{self.sha}.tar.gz").is_file())
        self.assertEqual(
            self.server.requests,
            ["/latest/checksums.txt", f"/latest/{ARCHIVE_NAME}"],
        )
        self.assert_stays_in_artifacts(before)

    def test_same_session_reuses_prepared_result_without_network(self):
        first = self.prepare(session="reuse")
        self.assert_status(first, "ready")
        requests = list(self.server.requests)
        index_file = Path(first["index_dir"]) / "index.json"
        stamp = index_file.stat().st_mtime_ns
        second = self.prepare(session="reuse")
        self.assertEqual(second, first)
        self.assertEqual(list(self.server.requests), requests)
        self.assertEqual(index_file.stat().st_mtime_ns, stamp)

    def test_same_session_recovers_after_transient_prepare_failure(self):
        component = component_search
        with patch.object(component, "_prepare", side_effect=OSError("temporary network failure")):
            self.assert_status(self.prepare(session="recover"), "error")
        self.assertEqual(list((self.cache / "sessions").glob("*.json")), [])
        self.assert_status(self.prepare(session="recover"), "ready")

    def test_old_non_ready_session_is_discarded_and_retried(self):
        self.assert_status(self.prepare(session="old-negative"), "ready")
        session_path = next((self.cache / "sessions").glob("*.json"))
        for status in ("error", "unsupported", "needs_context"):
            with self.subTest(status=status):
                session_path.write_text(json.dumps({"status": status}), encoding="utf-8")
                requests = len(self.server.requests)
                self.assert_status(self.prepare(session="old-negative"), "ready")
                self.assertGreater(len(self.server.requests), requests)
                self.assertEqual(json.loads(session_path.read_text())["status"], "ready")

    def test_refresh_failure_removes_previous_ready_session(self):
        self.assert_status(self.prepare(session="refresh-failure"), "ready")
        with patch.object(component_search, "_prepare", side_effect=OSError("temporary")):
            self.assert_status(self.prepare(session="refresh-failure", refresh=True), "error")
        self.assertEqual(list((self.cache / "sessions").glob("*.json")), [])
        self.assert_status(self.prepare(session="refresh-failure"), "ready")

    def test_invocation_session_does_not_persist_metadata(self):
        with patch.object(component_search, "process_session", return_value="invocation:123"):
            self.assert_status(self.prepare(session=None), "ready")
        self.assertEqual(list((self.cache / "sessions").glob("*.json")), [])
        self.assertTrue((self.cache / "snapshots").is_dir())
        self.assertTrue((self.cache / "indices").is_dir())

    def test_sessions_expire_and_stay_within_count_limit(self):
        component = component_search
        self.assert_status(self.prepare(session="retained"), "ready")
        sessions = self.cache / "sessions"
        expired = sessions / "expired.json"
        expired.write_text('{}', encoding="utf-8")
        os.utime(expired, (1, 1))
        for number in range(5):
            (sessions / f"extra-{number}.json").write_text('{}', encoding="utf-8")
        with patch.object(component, "SESSION_MAX_FILES", 3):
            self.assert_status(self.prepare(session="fresh"), "ready")
        self.assertFalse(expired.exists())
        self.assertLessEqual(len(list(sessions.glob("*.json"))), 3)
        self.assertTrue((self.cache / "snapshots").is_dir())
        self.assertTrue((self.cache / "indices").is_dir())

    def test_registry_extraction_changes_invalidate_all_cache_layers(self):
        component = component_search
        entry = component.component_entry(self.knowledge_root, registry=REGISTRY)
        first = self.prepare(session="contract-change")
        self.assert_status(first, "ready")
        expanded = json.loads(json.dumps(entry))
        expanded["extraction"]["paths"].append({"archive": "secret.txt", "kind": "extra"})
        expanded["extraction"]["required_kinds"].append("extra")
        requests = len(self.server.requests)
        with patch.object(component, "component_entry", return_value=expanded):
            second = self.prepare(session="contract-change")
            self.assert_status(second, "ready")
            self.assertEqual(second["index_actions"], ["built"])
            self.assertTrue((Path(second["data_root"]) / "secret.txt").is_file())
            reused = self.prepare(session="contract-change")
            self.assertEqual(reused, second)
        self.assertEqual(self.server.requests[requests:], ["/latest/checksums.txt"])
        third = self.prepare(session="contract-change", refresh=False)
        self.assert_status(third, "ready")
        self.assertFalse((Path(third["data_root"]) / "secret.txt").exists())
        self.assertEqual(third["index_actions"], ["built"])

    def test_required_resource_changes_revalidate_same_archive(self):
        component = component_search
        entry = component.component_entry(self.knowledge_root, registry=REGISTRY)
        self.assert_status(self.prepare(session="required-change"), "ready")
        for field in ("machine", "kind"):
            changed = json.loads(json.dumps(entry))
            if field == "machine":
                changed["machine"]["required"].append("missing.py")
            else:
                changed["extraction"]["required_kinds"].append("missing-kind")
            with self.subTest(field=field):
                with patch.object(component, "component_entry", return_value=changed):
                    self.assert_status(self.prepare(session="required-change"), "unsupported")

    def test_legacy_snapshot_and_index_markers_are_rebuilt(self):
        first = self.prepare(session="legacy-markers")
        snapshot_marker = Path(first["data_root"]).parent / ".complete.json"
        manifest = json.loads(snapshot_marker.read_text())
        manifest.pop("cache_contract_sha256")
        snapshot_marker.write_text(json.dumps(manifest), encoding="utf-8")
        (Path(first["index_dir"]) / ".component-contract.json").unlink()
        second = self.prepare(session="new-session")
        self.assert_status(second, "ready")
        self.assertEqual(second["index_actions"], ["built"])
        self.assertIn("cache_contract_sha256", json.loads(snapshot_marker.read_text()))

    def test_cache_contract_ignores_description_only_changes(self):
        component = component_search
        entry = component.component_entry(self.knowledge_root, registry=REGISTRY)
        changed = json.loads(json.dumps(entry))
        changed["label"] = "different display label"
        changed["messages"] = {"missing_machine": "different error text"}
        changed["coverage"]["messages"] = {"empty": "different explanation"}
        self.assertEqual(component.cache_contract_digest(entry), component.cache_contract_digest(changed))

    def test_new_session_only_refreshes_checksums(self):
        first = self.prepare(session="first")
        self.assert_status(first, "ready")
        requests = list(self.server.requests)
        second = self.prepare(session="second")
        self.assert_status(second, "ready")
        self.assertEqual(list(self.server.requests)[len(requests):], ["/latest/checksums.txt"])
        self.assertEqual(Path(second["data_root"]), Path(first["data_root"]))
        self.assertEqual(Path(second["index_dir"]), Path(first["index_dir"]))
        self.assertEqual(second["index_actions"], [])

    def test_refresh_rechecks_remote_and_reuses_cached_archive(self):
        first = self.prepare(session="refresh")
        self.assert_status(first, "ready")
        requests = list(self.server.requests)
        refreshed = self.prepare(session="refresh", refresh=True)
        self.assert_status(refreshed, "ready")
        self.assertEqual(
            list(self.server.requests)[len(requests):],
            ["/latest/checksums.txt"],
        )
        self.assertEqual(refreshed["archive_sha256"], first["archive_sha256"])
        self.assertEqual(refreshed["index_actions"], [])
        self.assertTrue((self.cache / "downloads" / f"{self.sha}.tar.gz").is_file())

    def test_invalid_checksums_return_error_before_writing_snapshot(self):
        before = self.files(self.knowledge_root)
        cases = (
            ("mismatch", f"{'0' * 64}  {ARCHIVE_NAME}\n", "SHA-256"),
            ("duplicate", f"{self.sha}  one.tar.gz\n{self.sha}  two.tar.gz\n", "exactly one"),
            ("missing", None, "404"),
        )
        for name, checksums, fragment in cases:
            with self.subTest(name):
                self.publish_archive(
                    extra_files={f"docs/zh/api/SIMD-API/c_api/{name}.md": "# x\n"}
                )
                checksums_path = self.publish_dir / "checksums.txt"
                if checksums is None:
                    checksums_path.unlink()
                else:
                    checksums_path.write_text(checksums, encoding="utf-8")
                result = self.prepare(session="checksum-" + name)
                self.assert_status(result, "error")
                self.assertEqual(result.get("fallback"), "knowledge-query")
                self.assertIn(fragment, result.get("error", ""))
                self.assertFalse((self.cache / "snapshots").exists())
                self.assertFalse((self.cache / "indices").exists())
                downloads = self.cache / "downloads"
                self.assertEqual(
                    sorted(path.name for path in downloads.iterdir()) if downloads.is_dir() else [],
                    [],
                )
        self.assert_stays_in_artifacts(before)

    def test_missing_machine_core_is_unsupported(self):
        before = self.files(self.knowledge_root)
        machine_files = tuple(
            relative for relative in FIXTURE_FILES if relative.startswith(MACHINE_ROOT + "/")
        )
        cases = (
            ("missing-entry", (MACHINE_SEARCH,)),
            ("missing-tree", machine_files),
        )
        for name, omit in cases:
            with self.subTest(name):
                digest = self.publish_archive(omit=omit)
                result = self.prepare(session="machine-" + name)
                self.assert_status(result, "unsupported")
                self.assertEqual(result.get("fallback"), "knowledge-query")
                self.assertEqual(result.get("archive_sha256"), digest)
                self.assertIn("machine", result.get("reason", ""))
                self.assertFalse((self.cache / "snapshots" / digest).exists())
                self.assertTrue(
                    (self.cache / "downloads" / f"{digest}.tar.gz").is_file()
                )
        self.assert_stays_in_artifacts(before)

    def test_insufficient_knowledge_heads_are_unsupported(self):
        cases = (
            ("doc-count-zero", {"STUB_DOC_COUNT": "0"}, "knowledge heads", {"doc_count": 0}),
            ("pending-heads", {"STUB_PENDING_NO_OKF": "2"}, "knowledge heads", {"pending_no_okf": 2}),
            ("no-products", {"STUB_PRODUCT_COUNT": "0"}, "product", {"product_markers": 0}),
        )
        for name, environment, fragment, expected in cases:
            with self.subTest(name):
                digest = self.publish_archive(
                    extra_files={f"docs/zh/api/SIMD-API/c_api/{name}.md": "# x\n"}
                )
                with patch.dict(os.environ, environment):
                    result = self.prepare(session=name)
                self.assert_status(result, "unsupported")
                self.assertEqual(result.get("fallback"), "knowledge-query")
                self.assertEqual(result.get("archive_sha256"), digest)
                self.assertIn(fragment, result.get("reason", ""))
                coverage = result.get("coverage", {})
                for key, value in expected.items():
                    self.assertEqual(coverage.get(key), value)

    def test_missing_target_context_returns_needs_context(self):
        with patch.dict(os.environ, {"STUB_CONTEXT_EMPTY": "1"}):
            result = self.prepare(session="needs-context", platform=None, version=None)
        self.assert_status(result, "needs_context")
        self.assertEqual(result.get("fallback"), "knowledge-query")
        self.assertIn("platform or CANN version", result.get("reason", ""))
        self.assertEqual(
            result.get("context"),
            {"platform": None, "arch": None, "cann_version": ""},
        )
        self.assertNotIn("index_dir", result)

    def test_conflicting_explicit_arch_is_error(self):
        result = self.prepare(session="arch-conflict", arch="2201")
        self.assert_status(result, "error")
        self.assertEqual(result.get("fallback"), "knowledge-query")
        self.assertIn("architecture", result.get("error", ""))

    def test_entries_outside_archive_prefix_are_ignored(self):
        member = tar_member("outside/cannbot-outside.txt", b"outside the archive root")
        digest = self.publish_archive(extra_members=(member,))
        result = self.prepare(session="outside-prefix")
        self.assert_status(result, "ready")
        self.assertEqual(result["archive_sha256"], digest)
        data_root = Path(result["data_root"])
        self.assertEqual(list(data_root.rglob("cannbot-outside.txt")), [])
        self.assertEqual(
            {path for path in self.files(data_root) if path.startswith("outside")},
            set(),
        )

    def test_unsafe_archive_entries_are_rejected(self):
        before = self.files(self.knowledge_root)
        cases = (
            (
                "absolute",
                tar_member(ARCHIVE_PREFIX + "/tmp/cannbot-escape.txt", b"escaped"),
                "unsafe archive path",
            ),
            (
                "parent",
                tar_member(ARCHIVE_PREFIX + "../cannbot-escape.txt", b"escaped"),
                "unsafe archive path",
            ),
            (
                "symlink",
                tar_symlink(ARCHIVE_PREFIX + "include/c_api/evil_link", "/etc/passwd"),
                "non-regular entry",
            ),
            (
                "windows-parent",
                tar_member(ARCHIVE_PREFIX + "include/c_api/..\\..\\cannbot-escape.txt", b"escaped"),
                "unsafe archive path",
            ),
            (
                "windows-drive",
                tar_member(ARCHIVE_PREFIX + "C:/cannbot-escape.txt", b"escaped"),
                "unsafe archive path",
            ),
            (
                "windows-unc",
                tar_member(ARCHIVE_PREFIX + "\\\\server\\share\\escape.txt", b"escaped"),
                "unsafe archive path",
            ),
            (
                "windows-stream",
                tar_member(ARCHIVE_PREFIX + "include/c_api/demo.h:stream", b"escaped"),
                "unsafe archive path",
            ),
        )
        for name, member, fragment in cases:
            with self.subTest(name):
                digest = self.publish_archive(extra_members=(member,))
                result = self.prepare(session="unsafe-" + name)
                self.assert_status(result, "error")
                self.assertEqual(result.get("fallback"), "knowledge-query")
                self.assertIn(fragment, result.get("error", ""))
                self.assertFalse((self.cache / "snapshots" / digest).exists())
                self.assertTrue(
                    (self.cache / "downloads" / f"{digest}.tar.gz").is_file()
                )
        self.assert_stays_in_artifacts(before)
        self.assertEqual(list(self.base.rglob("cannbot-escape.txt")), [])
        self.assertEqual(list(self.knowledge_root.rglob("evil_link")), [])

    def test_new_archive_prunes_old_snapshot_cache(self):
        first = self.prepare(session="cleanup-first")
        self.assert_status(first, "ready")
        first_digest = first["archive_sha256"]
        stale = (
            self.cache / "downloads" / f"{first_digest}.tar.gz",
            self.cache / "snapshots" / first_digest,
            self.cache / "indices" / first_digest,
        )
        for path in stale:
            self.assertTrue(path.exists(), path)
        second_digest = self.publish_archive(
            extra_files={"docs/zh/api/SIMD-API/c_api/demo2.md": "# second archive\n"}
        )
        self.assertNotEqual(second_digest, first_digest)
        second = self.prepare(session="cleanup-second")
        self.assert_status(second, "ready")
        self.assertEqual(second["archive_sha256"], second_digest)
        for path in stale:
            self.assertFalse(path.exists(), path)
        fresh = (
            self.cache / "downloads" / f"{second_digest}.tar.gz",
            self.cache / "snapshots" / second_digest,
            self.cache / "indices" / second_digest,
        )
        for path in fresh:
            self.assertTrue(path.exists(), path)
        self.assertIn(
            "demo2.md",
            {path.name for path in Path(second["data_root"]).rglob("*.md")},
        )
        self.assertEqual(
            sorted(path.name for path in (self.cache / "downloads").iterdir()),
            [f"{second_digest}.tar.gz"],
        )

    def _publish_corrupt_archive(self, payload):
        archive = self.publish_dir / ARCHIVE_NAME
        archive.write_bytes(payload)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (self.publish_dir / "checksums.txt").write_text(
            f"{digest}  {ARCHIVE_NAME}\n", encoding="utf-8"
        )

    def test_malformed_machine_index_metadata_is_a_structured_error(self):
        with patch.dict(os.environ, {"STUB_BAD_META": "1"}):
            result = self.prepare(session="bad-meta")
        self.assert_status(result, "error")
        self.assertEqual(result.get("fallback"), "knowledge-query")
        self.assertNotIn("traceback", json.dumps(result).lower())

    def test_checksum_matched_corrupt_archive_is_a_structured_error(self):
        cases = (
            ("not-gzip", b"not a gzip archive\n"),
            ("truncated", None),
        )
        for name, payload in cases:
            with self.subTest(name):
                if payload is None:
                    original = write_archive(self.base / "archives")
                    payload = original.read_bytes()[:96]
                self._publish_corrupt_archive(payload)
                before = self.files(self.knowledge_root)
                result = self.prepare(session="corrupt-" + name)
                self.assert_status(result, "error")
                self.assertEqual(result.get("fallback"), "knowledge-query")
                self.assertNotIn("traceback", json.dumps(result).lower())
                self.assert_stays_in_artifacts(before)
                self.assertFalse((self.cache / "snapshots").exists())
                self.assertFalse((self.cache / "indices").exists())
                self.publish_archive()


class IndexIntegrityTests(DevkitOfflineCase):
    def assert_rebuilt(self, first, session):
        with patch.object(component_search, "run", wraps=component_search.run) as runner:
            second = self.prepare(session=session)
        self.assert_status(second, "ready")
        builds = [call for call in runner.call_args_list
                  if any(str(arg).endswith("/build_index.py") for arg in call.args[0])]
        self.assertEqual(len(builds), 1, runner.call_args_list)
        self.assertEqual(first["index_dir"], second["index_dir"])
        return second

    def test_empty_real_scope_is_unsupported(self):
        builder = STUB_BUILD_INDEX.replace('root="docs/zh"', 'root="docs/zh/api/SIMD-API/c_api"')
        builder = builder.replace('(root / "docs").rglob("*.md")',
                                  '(root / "docs/zh/api/SIMD-API/c_api").rglob("*.md")')
        self.publish_archive(omit=(DEMO_DOC,), extra_files={MACHINE_SCRIPTS + "/build_index.py": builder})
        result = self.prepare(session="empty-real-scope")
        self.assert_status(result, "unsupported")
        self.assertEqual(result["coverage"]["doc_count"], 0)
        self.assertEqual(list((self.cache / "sessions").glob("*.json")), [])

    def test_same_session_missing_index_is_rebuilt(self):
        first = self.prepare(session="missing-index")
        self.assert_status(first, "ready")
        (Path(first["index_dir"]) / "index.json").unlink()
        self.assert_rebuilt(first, "missing-index")

    def test_same_session_invalid_artifacts_are_rebuilt(self):
        for name in ("index.json", "build-meta.json", "gaps.json"):
            for operation in ("missing", "invalid-json", "wrong-type"):
                with self.subTest(file=name, operation=operation):
                    session = name + operation
                    first = self.prepare(session=session)
                    self.assert_status(first, "ready")
                    path = Path(first["index_dir"]) / name
                    if operation == "missing":
                        path.unlink(missing_ok=True)
                    else:
                        path.write_text("broken" if operation == "invalid-json" else "[]")
                    self.assert_rebuilt(first, session)

    def test_same_and_new_session_wrong_target_is_rebuilt(self):
        for session_hit in (True, False):
            for key in ("source_commit", "cann_version", "arch", "arch_label", "surface"):
                with self.subTest(same_session=session_hit, key=key):
                    session = key + str(session_hit)
                    first = self.prepare(session=session)
                    path = Path(first["index_dir"]) / "index.json"
                    index = json.loads(path.read_text())
                    index["meta"][key] = "wrong-target"
                    path.write_text(json.dumps(index))
                    self.assert_rebuilt(first, session if session_hit else session + "-new")

    def test_parseable_but_invalid_component_structures_are_rebuilt(self):
        for name, key in (("index.json", "documents"), ("index.json", "scope"),
                          ("gaps.json", "scope_out_gaps"), ("build-meta.json", "schema"),
                          ("build-meta.json", "source_commit")):
            with self.subTest(file=name, key=key):
                session = name + key
                first = self.prepare(session=session)
                path = Path(first["index_dir"]) / name
                payload = json.loads(path.read_text())
                payload.pop(key)
                path.write_text(json.dumps(payload))
                self.assert_rebuilt(first, session)

    def test_stale_inputs_are_rebuilt_in_same_session(self):
        paths = ("config/product-map.yaml", "config/tag-taxonomy.json", "scripts/search.py")
        for relative in (*paths, DEMO_DOC, "include/c_api/demo.h",
                         "examples/02_simd_c_api/demo.asc", "new-document"):
            with self.subTest(path=relative):
                first = self.prepare(session="stale-" + relative)
                root = Path(first["data_root"])
                path = root / (MACHINE_ROOT + "/" + relative if relative in paths else relative)
                if relative == "new-document":
                    path = root / "docs/zh/api/SIMD-API/c_api/new.md"
                    path.write_text("# new document\n")
                else:
                    original = path.read_text()
                    path.write_text(original + "\n")
                self.assert_rebuilt(first, "stale-" + relative)

    def test_first_build_invalid_auxiliary_outputs_are_rejected(self):
        for name in ("index.json", "build-meta.json", "gaps.json"):
            for operation in ("missing", "invalid-json", "wrong-type"):
                with self.subTest(file=name, operation=operation):
                    if operation == "missing":
                        damage = f"(out / {name!r}).unlink()"
                    else:
                        content = "broken" if operation == "invalid-json" else "[]"
                        damage = f"(out / {name!r}).write_text({content!r})"
                    builder = STUB_BUILD_INDEX.replace(
                        '    (out / "build-meta.json").write_text(json.dumps(meta), encoding="utf-8")',
                        '    (out / "build-meta.json").write_text(json.dumps(meta), encoding="utf-8")\n    ' + damage,
                    )
                    self.assertNotEqual(builder, STUB_BUILD_INDEX)
                    self.publish_archive(extra_files={MACHINE_SCRIPTS + "/build_index.py": builder})
                    result = self.prepare(session="bad-first-" + name + operation)
                    self.assert_status(result, "error")
                    self.assertEqual(list((self.cache / "sessions").glob("*.json")), [])
                    self.assertEqual(list((self.cache / "indices").rglob("index.json")), [])

    def test_wrong_first_build_is_error_and_not_cached(self):
        for key in ("source_commit", "cann_version", "arch"):
            with self.subTest(key=key):
                builder = STUB_BUILD_INDEX.replace(
                    '"' + key + '": args.' + key,
                    '"' + key + '": "wrong-target"')
                self.publish_archive(extra_files={MACHINE_SCRIPTS + "/build_index.py": builder})
                with patch.object(component_search, "run", wraps=component_search.run) as runner:
                    result = self.prepare(session="wrong-first-" + key)
                self.assert_status(result, "error")
                self.assertEqual(list((self.cache / "sessions").glob("*.json")), [])
                self.assertEqual(list((self.cache / "indices").rglob("index.json")), [])
                builds = [call for call in runner.call_args_list
                          if any(str(arg).endswith("/build_index.py") for arg in call.args[0])]
                self.assertEqual(len(builds), 1)




if __name__ == "__main__":
    unittest.main()
