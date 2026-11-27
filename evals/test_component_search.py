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
"""Offline regression for the component search registry and generic provisioner.

The fixture archive publishes two components, each with a stub machine search
core, and is served from a loopback HTTP server. The tests cover registry
accept/reject, pending components, shared archive download, component isolation,
native search output and protocol rejection without network access.
"""
from __future__ import annotations

import errno
import hashlib
import http.server
import importlib.util
import io
import multiprocessing
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/knowledge-query/scripts"
ARCHIVE_NAME = "components-fixture.tar.gz"
OFFLINE_PROXY = {"no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost"}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


component_search = module("component_search_fixture", SCRIPTS / "component_search.py")

DETECT_STUB = """#!/usr/bin/env python3
import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform")
    parser.add_argument("--cann-version")
    args = parser.parse_args()
    print(json.dumps({
        "platform": args.platform or "950",
        "arch": "3510",
        "cann_version": args.cann_version or "9.2.0",
    }))


if __name__ == "__main__":
    main()
"""

BUILD_STUB = """#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cann-version", required=True)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    docs = sorted((Path(args.root) / "docs").rglob("*.md"))
    index = {
        "meta": {
            "doc_count": len(docs),
            "pending_no_okf": 0,
            "source_commit": args.source_commit,
            "cann_version": args.cann_version,
            "arch": args.arch,
        },
        "views": {"by_product": {"950": [str(path) for path in docs]}},
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.json").write_text(json.dumps(index), encoding="utf-8")


if __name__ == "__main__":
    main()
"""

SEARCH_STUB = """#!/usr/bin/env python3
import json
import sys

SCHEMA = "@SCHEMA@"

print(json.dumps({
    "schema": SCHEMA,
    "count": 1,
    "results": [{"path": "docs/zh/api/demo.md", "why": ["stub"], "argv": sys.argv[1:]}],
}))
"""


def component_files(schema):
    return {
        ".agent/skills/asc-search/SKILL.md": "# stub machine core\n",
        ".agent/skills/asc-search/config/product-map.yaml": "products:\n  - 950\n",
        ".agent/skills/asc-search/config/tag-taxonomy.json": '{"tags": ["vector"]}\n',
        ".agent/skills/asc-search/scripts/detect_context.py": DETECT_STUB,
        ".agent/skills/asc-search/scripts/build_index.py": BUILD_STUB,
        ".agent/skills/asc-search/scripts/search.py": SEARCH_STUB.replace("@SCHEMA@", schema),
        "docs/zh/api/demo.md": "---\nokftype: reference.api\n---\n\n# demo\n",
        "include/c_api/demo.h": "#pragma once\n",
        "examples/demo.asc": "// stub example\n",
    }


MACHINE_FIELDS = """    machine:
      dir: .agent/skills/asc-search
      required:
        - SKILL.md
        - scripts/search.py
        - scripts/build_index.py
        - scripts/detect_context.py
        - config/product-map.yaml
        - config/tag-taxonomy.json
      detect: scripts/detect_context.py
      build: scripts/build_index.py
      search: scripts/search.py
"""

INDEX_FIELDS = """    index:
      surface: c_api
      marker: index.json
      meta:
        source_commit: "artifact:{sha256}"
        cann_version: "{cann_version}"
        arch: "{arch}"
      build_command:
        - "{python}"
        - "{machine_dir}/scripts/build_index.py"
        - "--root"
        - "{data_root}"
        - "--out"
        - "{index_dir}"
        - "--cann-version"
        - "{cann_version}"
        - "--arch"
        - "{arch}"
        - "--source-commit"
        - "artifact:{sha256}"
"""


def registry_text(url, alpha_status="active", beta_status="active", alpha_schema="alpha-results/1"):
    return f"""schema: component-search/1
archive:
  url: {url}
  checksums: checksums.txt
  download_cache: artifacts/component-search/downloads
components:
  alpha:
    status: {alpha_status}
    label: alpha
    machine_name: alpha-search
    cache_dir: artifacts/alpha
    archive_prefix: alpha/
    extraction:
      data_dir: alpha
      paths:
        - archive: .agent/skills/asc-search
          kind: machine
        - archive: docs/zh
          kind: docs
        - archive: include/c_api
          kind: include
        - archive: examples
          kind: examples
      required_kinds: [machine, docs, include, examples]
{MACHINE_FIELDS}{INDEX_FIELDS}    search:
      schema: {alpha_schema}
      command:
        - "{{python}}"
        - "{{search_script}}"
        - "--root"
        - "{{data_root}}"
        - "--index-dir"
        - "{{index_dir}}"
        - "--platform"
        - "{{platform}}"
        - "--version"
        - "{{cann_version}}"
        - "--repository"
        - "{{repository}}"
    coverage:
      doc_count: [meta, doc_count]
      pending_no_okf: [meta, pending_no_okf]
      product_markers: [views, by_product]
      require_products: true
      messages:
        empty: "alpha archive has no usable knowledge heads"
        pending: "alpha archive documents lack usable knowledge heads ({{pending_no_okf}} pending)"
        products: "alpha archive documents lack product support markers"
    messages:
      missing_resources: "archive lacks required alpha resources: {{missing}}"
      missing_machine: "official archive lacks the alpha machine core: {{missing}}"
  beta:
    status: {beta_status}
    label: beta
    machine_name: beta-search
    cache_dir: artifacts/beta
    archive_prefix: beta/
    extraction:
      data_dir: beta
      paths:
        - archive: .agent/skills/asc-search
          kind: machine
        - archive: docs/zh
          kind: docs
        - archive: include/c_api
          kind: include
        - archive: examples
          kind: examples
      required_kinds: [machine, docs, include, examples]
{MACHINE_FIELDS}{INDEX_FIELDS}    search:
      schema: beta-results/1
      command:
        - "{{python}}"
        - "{{search_script}}"
        - "--root"
        - "{{data_root}}"
        - "--index-dir"
        - "{{index_dir}}"
        - "--platform"
        - "{{platform}}"
        - "--version"
        - "{{cann_version}}"
        - "--repository"
        - "{{repository}}"
    coverage:
      doc_count: [meta, doc_count]
      pending_no_okf: [meta, pending_no_okf]
      product_markers: [views, by_product]
      require_products: true
      messages:
        empty: "beta archive has no usable knowledge heads"
        pending: "beta archive documents lack usable knowledge heads ({{pending_no_okf}} pending)"
        products: "beta archive documents lack product support markers"
    messages:
      missing_resources: "archive lacks required beta resources: {{missing}}"
      missing_machine: "official archive lacks the beta machine core: {{missing}}"
"""


def lock_worker(cache, connection):
    """Run the real platform lock in a separate, spawned interpreter."""
    try:
        connection.send("waiting")
        try:
            with component_search.preparation_lock(Path(cache)):
                connection.send("acquired")
                if connection.recv() == "raise":
                    raise RuntimeError("body failed")
        except RuntimeError:
            connection.send("released-after-error")
    finally:
        connection.close()


class PreparationLockTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.cache = Path(temporary.name) / "cache"
        self.context = multiprocessing.get_context("spawn")

    def worker(self, cache):
        parent, child = self.context.Pipe()
        process = self.context.Process(target=lock_worker, args=(str(cache), child))
        process.start()
        child.close()

        def cleanup():
            if process.is_alive():
                process.terminate()
            process.join(timeout=10)
            parent.close()
            process.close()

        self.addCleanup(cleanup)
        self.receive(parent, "waiting")
        return process, parent

    def receive(self, connection, expected):
        self.assertTrue(connection.poll(10), f"timed out waiting for {expected}")
        self.assertEqual(connection.recv(), expected)

    def finish(self, process, connection, command="release"):
        connection.send(command)
        if command == "raise":
            self.receive(connection, "released-after-error")
        process.join(timeout=10)
        self.assertFalse(process.is_alive())
        self.assertEqual(process.exitcode, 0)

    def test_same_cache_waits_until_owner_releases(self):
        owner, first = self.worker(self.cache)
        self.receive(first, "acquired")
        waiter, second = self.worker(self.cache)
        self.assertFalse(second.poll(0.3), "both processes acquired the same cache")
        self.finish(owner, first)
        self.receive(second, "acquired")
        self.finish(waiter, second)

    def test_different_caches_can_be_locked_together(self):
        owner, first = self.worker(self.cache)
        self.receive(first, "acquired")
        other, second = self.worker(self.cache.with_name("other"))
        self.receive(second, "acquired")
        self.finish(other, second)
        self.finish(owner, first)

    def test_exception_releases_the_lock(self):
        owner, first = self.worker(self.cache)
        self.receive(first, "acquired")
        self.finish(owner, first, "raise")
        successor, second = self.worker(self.cache)
        self.receive(second, "acquired")
        self.finish(successor, second)

    def test_terminated_owner_releases_the_lock(self):
        owner, first = self.worker(self.cache)
        self.receive(first, "acquired")
        owner.terminate()
        owner.join(timeout=10)
        self.assertFalse(owner.is_alive())
        successor, second = self.worker(self.cache)
        self.receive(second, "acquired")
        self.finish(successor, second)

    def test_unexpected_lock_error_is_not_retried(self):
        backend = component_search.msvcrt if os.name == "nt" else component_search.fcntl
        function = "locking" if os.name == "nt" else "flock"
        with patch.object(backend, function, side_effect=OSError(errno.EBADF, "bad descriptor")):
            with self.assertRaises(OSError) as caught:
                with component_search.preparation_lock(self.cache):
                    self.fail("lock acquisition should fail")
        self.assertEqual(caught.exception.errno, errno.EBADF)
        # The descriptor was closed even though acquisition failed.
        with component_search.preparation_lock(self.cache):
            pass

    def test_cli_entrypoints_start_without_unix_only_imports(self):
        for script in (
            SCRIPTS / "component_search.py",
        ):
            with self.subTest(script=script.name):
                completed = subprocess.run(
                    [sys.executable, str(script), "--help"],
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("usage:", completed.stdout.lower())


class FixtureServer:
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

    def _record(self, request):
        with self._lock:
            self.requests.append(request)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.httpd.server_address[1]}/latest/"

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


def write_archive(target, components):
    target.mkdir(parents=True, exist_ok=True)
    archive = target / ARCHIVE_NAME
    with tarfile.open(archive, "w:gz") as tar:
        for prefix, files in components.items():
            for relative, content in sorted(files.items()):
                data = content.encode("utf-8")
                info = tarfile.TarInfo(f"{prefix}/{relative}")
                info.size = len(data)
                info.mode = 0o755 if relative.endswith(".py") else 0o644
                tar.addfile(info, io.BytesIO(data))
    return archive


class ComponentSearchCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.knowledge_root = self.base / "knowledge"
        (self.knowledge_root / "governance/schemas").mkdir(parents=True)
        self.publish = self.base / "remote/latest"
        self.publish.mkdir(parents=True)
        self.server = FixtureServer(self.base / "remote")
        self.addCleanup(self.server.stop)
        proxy = patch.dict(os.environ, OFFLINE_PROXY)
        proxy.start()
        self.addCleanup(proxy.stop)
        archive = write_archive(
            self.base / "archives",
            {"alpha": component_files("alpha-results/1"), "beta": component_files("beta-results/1")},
        )
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.digest = digest
        self.registry = self.knowledge_root / "governance/schemas/component_search.yaml"
        self.write_registry()
        shutil.copyfile(archive, self.publish / ARCHIVE_NAME)
        (self.publish / "checksums.txt").write_text(
            f"{digest}  {ARCHIVE_NAME}\n", encoding="utf-8"
        )

    def write_registry(self, **overrides):
        self.registry.write_text(registry_text(self.server.url, **overrides), encoding="utf-8")

    def prepare(self, component):
        return component_search.prepare(self.knowledge_root, component=component)

    def archive_requests(self):
        return [path for path in self.server.requests if path.endswith(".tar.gz")]

    def test_extraction_directory_cannot_escape_staging(self):
        entry = component_search.component_entry(self.knowledge_root, "alpha")
        entry["extraction"]["data_dir"] = "../outside"
        staging = self.base / "staging"
        staging.mkdir()
        with self.assertRaisesRegex(ValueError, "unsafe extraction directory"):
            component_search.extract_snapshot(
                self.publish / ARCHIVE_NAME, staging, self.digest, self.server.url, entry
            )
        self.assertFalse((self.base / "outside").exists())

    def test_registry_accepts_valid_entry_and_rejects_malformed_ones(self):
        data = component_search.load_registry(self.knowledge_root)
        self.assertEqual(data["schema"], "component-search/1")
        self.assertEqual(component_search.active_components(self.knowledge_root), ["alpha", "beta"])

        cases = {
            "schema": self.registry.read_text(encoding="utf-8").replace(
                "schema: component-search/1", "schema: component-search/2"
            ),
            "archive": "schema: component-search/1\ncomponents:\n  alpha: {}\n",
            "component": (
                "schema: component-search/1\n"
                "archive:\n  url: https://example.com/latest/\n"
                "components:\n  alpha:\n    status: active\n"
            ),
        }
        for name, text in cases.items():
            with self.subTest(name):
                self.registry.write_text(text, encoding="utf-8")
                with self.assertRaises(component_search.RegistryError):
                    component_search.load_registry(self.knowledge_root)
                result = component_search.prepare(self.knowledge_root, component="alpha")
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["fallback"], "knowledge-query")
        self.write_registry()

    def test_registry_nested_errors_identify_fields_before_network(self):
        original = self.registry.read_text(encoding="utf-8")
        cases = [
            (("components", "alpha", "extraction", "paths"), ["docs/zh"], "extraction.paths[0]"),
            (("components", "alpha", "extraction", "paths"), [{"archive": "docs/zh"}], "paths[0].kind"),
            (("components", "alpha", "coverage", "pending_no_okf"), None, "coverage.pending_no_okf"),
            (("components", "alpha", "coverage", "pending"), ["meta", "pending_no_okf"], "coverage.pending"),
            (("components", "alpha", "coverage", "product_markers"), None, "coverage.product_markers"),
            (("components", "alpha", "coverage", "require_products"), "false", "coverage.require_products"),
            (("components", "alpha", "search", "schema"), [], "search.schema"),
            (("components", "alpha", "search", "command"), "python search.py", "search.command"),
            (("components", "alpha", "search", "filters"), "default", "search.filters"),
            (("components", "alpha", "machine", "required"), "SKILL.md", "machine.required"),
            (("components", "alpha", "index", "build_command"), [1], "index.build_command"),
            (("components", "alpha", "index", "required_files"), "index.json", "index.required_files"),
            (("components", "alpha", "index", "required_files"), ["../outside.json"], "index.required_files"),
            (("components", "alpha", "index", "validation_command"), [], "index.validation_command"),
            (("archive", "checksums"), "other.txt", "archive.checksums"),
            (("archive", "env"), "UNUSED_ARCHIVE_URL", "archive.env"),
        ]
        for keys, value, expected in cases:
            with self.subTest(field=expected):
                data = component_search.yaml.safe_load(original)
                target = data
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                self.registry.write_text(component_search.yaml.safe_dump(data), encoding="utf-8")
                with self.assertRaises(component_search.RegistryError) as caught:
                    component_search.load_registry(self.knowledge_root)
                self.assertIn(expected, str(caught.exception))
                result = component_search.prepare(self.knowledge_root, component="alpha")
                self.assertEqual(result["status"], "error")
                self.assertIn(expected, result["error"])
                self.assertEqual(self.server.requests, [])
        self.registry.write_text(original, encoding="utf-8")

    def test_registry_allows_omitting_products_when_not_required(self):
        data = component_search.yaml.safe_load(self.registry.read_text(encoding="utf-8"))
        coverage = data["components"]["alpha"]["coverage"]
        coverage["require_products"] = False
        coverage.pop("product_markers")
        self.registry.write_text(component_search.yaml.safe_dump(data), encoding="utf-8")
        loaded = component_search.load_registry(self.knowledge_root)
        self.assertFalse(loaded["components"]["alpha"]["coverage"]["require_products"])
        self.assertEqual(self.server.requests, [])

    def test_capabilities_reports_active_and_pending_without_network(self):
        active = component_search.capabilities(self.knowledge_root, "alpha")
        self.assertTrue(active["available"])
        self.assertEqual(active["status"], "active")
        self.assertEqual(active["machine_skill"], "alpha-search")
        self.assertEqual(self.server.requests, [])

        self.write_registry(beta_status="pending")
        pending = component_search.capabilities(self.knowledge_root, "beta")
        self.assertFalse(pending["available"])
        self.assertEqual(pending["status"], "pending")
        missing = component_search.capabilities(self.base / "bare")
        self.assertFalse(missing["available"])
        self.assertEqual(len(missing["missing"]), 1)
        self.assertIn("component_search.yaml", missing["missing"][0])

    def test_shared_archive_downloads_once_and_components_stay_isolated(self):
        alpha = self.prepare("alpha")
        beta = self.prepare("beta")
        self.assertEqual(alpha["status"], "ready", alpha)
        self.assertEqual(beta["status"], "ready", beta)
        # One archive download for both components: the shared SHA cache is reused.
        self.assertEqual(len(self.archive_requests()), 1, self.server.requests)
        self.assertEqual(len(self.server.requests), 3, self.server.requests)

        alpha_root = Path(alpha["data_root"])
        beta_root = Path(beta["data_root"])
        self.assertTrue((alpha_root / "docs/zh/api/demo.md").is_file())
        self.assertTrue((beta_root / "docs/zh/api/demo.md").is_file())
        self.assertFalse((alpha_root / "beta").exists())
        self.assertFalse((beta_root / "alpha").exists())
        shared = self.knowledge_root / "artifacts/component-search/downloads" / f"{self.digest}.tar.gz"
        self.assertTrue(shared.is_file())
        self.assertTrue(
            (self.knowledge_root / "artifacts/alpha/downloads" / f"{self.digest}.tar.gz").is_file()
        )
        self.assertTrue(
            (self.knowledge_root / "artifacts/beta/downloads" / f"{self.digest}.tar.gz").is_file()
        )
        docs = sorted(
            path.name
            for path in self.knowledge_root.glob("artifacts/**/docs/zh/**/*.md")
        )
        self.assertEqual(docs, ["demo.md", "demo.md"])

    def test_pending_component_is_unavailable_without_network(self):
        self.write_registry(beta_status="pending")
        result = self.prepare("beta")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["fallback"], "knowledge-query")
        self.assertEqual(self.server.requests, [])

    def test_search_returns_native_json_and_maps_filters(self):
        prepared = self.prepare("alpha")
        self.assertEqual(prepared["status"], "ready", prepared)
        payload = component_search.search(
            self.knowledge_root,
            component="alpha",
            filters={
                "operation": "copy",
                "keywords": ["foo", "bar"],
                "convert": ["float", "half"],
                "reverse": True,
                "limit": 3,
            },
        )
        self.assertEqual(payload["schema"], "alpha-results/1")
        self.assertEqual(payload["count"], 1)
        argv = payload["results"][0]["argv"]
        for flag, value in (
            ("--root", prepared["data_root"]),
            ("--index-dir", prepared["index_dir"]),
            ("--platform", "950"),
            ("--version", "9.2.0"),
        ):
            self.assertEqual(argv[argv.index(flag) + 1], value)
        self.assertEqual(
            argv[argv.index("--repository") + 1], prepared["archive_url"]
        )
        self.assertEqual(argv[argv.index("--operation") + 1], "copy")
        self.assertEqual(argv[argv.index("--keywords") + 1 : argv.index("--keywords") + 3], ["foo", "bar"])
        self.assertEqual(argv[argv.index("--convert") + 1 : argv.index("--convert") + 3], ["float", "half"])
        self.assertIn("--reverse", argv)
        self.assertEqual(argv[argv.index("--limit") + 1], "3")

    def test_protocol_mismatch_returns_structured_fallback(self):
        self.write_registry(alpha_schema="other-results/1")
        payload = component_search.search(self.knowledge_root, component="alpha")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["fallback"], "knowledge-query")
        self.assertIn("other-results/1", payload["error"])


if __name__ == "__main__":
    unittest.main()
