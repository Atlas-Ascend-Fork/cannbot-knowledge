# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Pinned source registration, offline links and safe resource restoration."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/knowledge-ingest/scripts"))
resource_tool = importlib.import_module("source_resources")
resources = resource_tool.resources
Contract = resource_tool.ingest.contract_module().Contract
link_checks = importlib.import_module(f"{resource_tool.ingest.contract_package().__name__}.checks.links")


class SourceResourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "governance", self.root / "governance")
        (self.root / "knowledge").mkdir()
        self.checkout = self.root / "cann-ops-raw/ascendc/ops-nn/pending"
        self.checkout.mkdir(parents=True)
        self.git("init", "--quiet")
        self.git("remote", "add", "origin", "https://gitcode.com/cann/ops-nn.git")
        self.raw = "// AscendC::GetBlockIdx();\nint kernel() {\n  return AscendC::GetBlockIdx();\n}\n"
        (self.checkout / "kernel.h").write_text(self.raw)
        (self.checkout / "notes.md").write_text("# source notes\n")
        self.git("add", "kernel.h", "notes.md")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture")
        self.revision = self.git("rev-parse", "HEAD")
        destination = self.checkout.with_name(self.revision)
        self.checkout.rename(destination)
        self.checkout = destination
        self.definition = {
            "description": "Pinned fixture", "kind": "git", "root": "cann-ops-raw/ascendc/ops-nn",
            "repository": "https://gitcode.com/cann/ops-nn", "fetch_script": ".agents/skills/knowledge-ingest/scripts/source_resources.py",
            "revisions": [self.revision],
        }
        self.registry_path = self.root / "governance/schemas/registries.yaml"
        self.registry = yaml.safe_load(self.registry_path.read_text())
        archive = self.registry["local_sources"]["cann_docs_raw"]
        self.registry["local_sources"] = {"cann_docs_raw": archive, "ops_nn": self.definition}
        self.save_registry()
        self.contract = Contract(self.root)


    def git(self, *args):
        return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", str(self.checkout), *args], check=True, capture_output=True, text=True).stdout.strip()


    def save_registry(self):
        self.registry_path.write_text(yaml.safe_dump(self.registry, allow_unicode=True, sort_keys=False))

    def test_invalid_git_definitions_fail_closed(self):
        valid = dict(self.definition)
        cases = [
            {"revisions": []}, {"revisions": ["main"]},
            {"revisions": [self.revision, self.revision]},
            {"repository": "https://example.invalid/ops-nn"},
            {"archive_sha256": "a" * 64}, {"kind": "unknown"},
        ]
        for fields in cases:
            with self.subTest(fields=fields):
                self.definition.clear()
                self.definition.update(valid | fields)
                self.save_registry()
                with self.assertRaises(ValueError):
                    Contract(self.root)

    def test_index_and_unregistered_links_cannot_leave_bundle(self):
        card = self.operator()
        for name, destination in (
            ("index.md", self.checkout / "kernel.h"),
            ("fixture.md", self.root / "governance/contracts/knowledge.py"),
        ):
            path = card.path.with_name(name)
            path.write_text(f"# Fixture\n\n[code]({os.path.relpath(destination, path.parent)})\n")
            document = SimpleNamespace(path=path, parse_error=None)
            issues = link_checks.check(self.contract, document, SimpleNamespace(checked_local_roots=set()))
            self.assertIn("link.outside_bundle", {issue.code for issue in issues})

    def test_missing_file_and_invalid_line_fragment_are_rejected(self):
        card = self.operator()
        for filename, fragment in (("missing.h", "#L71"), ("kernel.h", "#invalid")):
            path = os.path.relpath(self.checkout / filename, card.path.parent)
            card.path.write_text(f"# Fixture\n\n[code]({path}{fragment})\n")
            document = SimpleNamespace(path=card.path, parse_error=None)
            self.assertTrue(link_checks.check(self.contract, document, SimpleNamespace(checked_local_roots=set())))

    def test_fetch_refuses_unmanaged_directory_without_running_git(self):
        with mock.patch.object(resource_tool, "run_git") as run:
            with self.assertRaisesRegex(ValueError, "unmanaged"):
                resource_tool.fetch_repository(self.root, self.definition)
        run.assert_not_called()
        self.assertEqual(self.raw, (self.checkout / "kernel.h").read_text())

    def test_verify_cli_is_read_only_and_contract_mismatch_fails_before_fetch(self):
        script = ROOT / ".agents/skills/knowledge-ingest/scripts/source_resources.py"
        command = [sys.executable, str(script), "--knowledge-root", str(self.root)]
        before = (self.checkout / "kernel.h").read_bytes()
        result = subprocess.run([*command, "verify"], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("verified Git snapshots=1", result.stdout)
        self.assertEqual(before, (self.checkout / "kernel.h").read_bytes())
        target = self.root / "governance/contracts/knowledge.py"
        target.write_text(target.read_text() + "\nraise RuntimeError('must not execute')\n")
        result = subprocess.run([*command, "fetch"], capture_output=True, text=True)
        self.assertEqual(2, result.returncode)
        self.assertIn("contract does not match", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.checkout.parent / ".objects.git").exists())


    def operator(self):
        path = self.root / "knowledge/ops/ascendc/operators/aclnn/nn/activation/fixture.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Fixture\n")
        return SimpleNamespace(path=path, sources=[f"{self.definition['root']}/{self.revision}/kernel.h"])

    def test_remote_variants_and_local_paths_keep_identical_revision(self):
        expected = f"cann-ops-raw/ascendc/ops-nn/{self.revision}/kernel.h"
        for spelling in (f"https://gitcode.com/cann/ops-nn/blob/{self.revision}/kernel.h", f"https://gitcode.com/cann/ops-nn/-/blob/{self.revision}/kernel%2Eh", expected):
            self.assertEqual(expected, resources.git_source(self.contract, spelling).resource)
        self.assertIsNone(resources.git_source(self.contract, "https://gitcode.com/cann/opbase/blob/" + "a" * 40 + "/file.h"))


    def test_source_paths_reject_unknown_commit_traversal_and_git_internals(self):
        for value in (f"cann-ops-raw/ascendc/ops-nn/{'a' * 40}/kernel.h", f"cann-ops-raw/ascendc/ops-nn/{self.revision}/../kernel.h", f"cann-ops-raw/ascendc/ops-nn/{self.revision}/.git/config", f"https://gitcode.com/cann/ops-nn/blob/{self.revision}/%2e%2e/kernel.h"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resources.git_source(self.contract, value)


    def test_checkout_reuse_is_read_only_and_rejects_dirty_origin_and_hidden_entries(self):
        before = (self.checkout / "kernel.h").read_bytes()
        resources.validate_checkout(self.root, self.definition, self.revision)
        resources.validate_checkout(self.root, self.definition, self.revision)
        self.assertEqual(before, (self.checkout / "kernel.h").read_bytes())
        (self.checkout / "untracked").write_text("preserve me")
        with self.assertRaisesRegex(ValueError, "local changes"):
            resources.validate_checkout(self.root, self.definition, self.revision)
        (self.checkout / "untracked").unlink()
        self.git("remote", "set-url", "origin", "https://example.invalid/wrong")
        with self.assertRaisesRegex(ValueError, "origin mismatch"):
            resources.validate_checkout(self.root, self.definition, self.revision)
        self.git("remote", "set-url", "origin", self.definition["repository"])
        self.git("update-index", "--assume-unchanged", "kernel.h")
        with self.assertRaisesRegex(ValueError, "hidden or sparse"):
            resources.validate_checkout(self.root, self.definition, self.revision)


    def test_source_symlink_escape_is_rejected(self):
        (self.checkout / "escape.h").symlink_to(self.root / "outside.h")
        with self.assertRaisesRegex(ValueError, "escapes"):
            resources.git_source(self.contract, f"cann-ops-raw/ascendc/ops-nn/{self.revision}/escape.h")


    def test_registry_refuses_reserved_roots_and_duplicate_repositories(self):
        for root in ("/", "knowledge", "../escape", ".git", "knowledge/ops-nn", "cann-ops-raw/../ops-nn", "cann-ops-raw//ops-nn", "cann-ops-raw/.git/ops-nn"):
            self.definition["root"] = root
            self.save_registry()
            with self.assertRaisesRegex(ValueError, "safe relative source path"):
                Contract(self.root)
        self.definition["root"] = "cann-ops-raw/ascendc/ops-nn"
        self.registry["local_sources"]["duplicate"] = {**self.definition, "root": "duplicate-src"}
        self.save_registry()
        with self.assertRaisesRegex(ValueError, "repositories must be unique"):
            Contract(self.root)


    def test_nested_source_roots_are_distinct_and_cannot_overlap(self):
        resource = f"{self.definition['root']}/{self.revision}/kernel.h"
        self.assertEqual(self.definition, self.contract.local_source_definition(resource))
        self.assertIsNone(self.contract.local_source_definition(resource.replace("ops-nn/", "ops-nn-other/")))
        sibling = {**self.definition, "root": "cann-ops-raw/ascendc/ops-math", "repository": "https://gitcode.com/cann/ops-math"}
        self.registry["local_sources"]["ops_math"] = sibling
        self.save_registry()
        Contract(self.root)
        for root in ("cann-ops-raw", self.definition["root"] + "/nested"):
            sibling["root"] = root
            self.save_registry()
            with self.assertRaisesRegex(ValueError, "must not overlap"):
                Contract(self.root)


    def test_nested_frontmatter_sources_check_restored_checkout_and_offline_shape(self):
        source_checks = importlib.import_module(f"{resource_tool.ingest.contract_package().__name__}.checks.sources")
        restored_checks = importlib.import_module(f"{resource_tool.ingest.contract_package().__name__}.checks.local_sources")
        card = self.operator()
        resource = card.sources[0]
        self.assertTrue(source_checks.is_safe_local_resource(self.contract, resource))
        document = SimpleNamespace(path=card.path, metadata={"sources": [{"resource": resource}]})
        self.assertEqual([], restored_checks.check(self.contract, document, SimpleNamespace(checked_local_roots=set())))
        (self.checkout / "kernel.h").write_text(self.raw + "// dirty\n")
        findings = restored_checks.check(self.contract, document, SimpleNamespace(checked_local_roots=set()))
        self.assertEqual(["source.git_checkout"], [item.code for item in findings])
        (self.root / self.definition["root"]).rename(self.root / "offline-backup")
        self.assertEqual([], restored_checks.check(self.contract, document, SimpleNamespace(checked_local_roots=set())))
        self.assertTrue(source_checks.is_safe_local_resource(self.contract, resource))
        self.assertFalse(source_checks.is_safe_local_resource(self.contract, resource.replace(self.revision, "a" * 40)))


    def test_fetch_creates_nested_parents_without_following_ancestor_symlinks(self):
        definition = {**self.definition, "root": "new-raw/ascendc/ops-nn"}
        with (
            mock.patch.object(resource_tool, "run_git") as run,
            mock.patch.object(resources, "git_read", return_value=self.definition["repository"]),
            mock.patch.object(resources, "validate_checkout"),
        ):
            resource_tool.fetch_repository(self.root, definition)
            self.assertTrue((self.root / definition["root"]).is_dir())
            self.assertTrue(any(call.args[0:3] == ("init", "--quiet", "--bare") for call in run.call_args_list))
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "alias-raw").symlink_to(outside, target_is_directory=True)
        definition["root"] = "alias-raw/ascendc/ops-nn"
        with mock.patch.object(resource_tool, "run_git") as run, self.assertRaisesRegex(ValueError, "symlink"):
            resource_tool.fetch_repository(self.root, definition)
        run.assert_not_called()
        self.assertEqual([], list(outside.iterdir()))


    def test_offline_links_validate_registered_revision_without_fetching(self):
        card = self.operator()
        target = os.path.relpath(self.checkout / "kernel.h", card.path.parent)
        (self.root / "cann-ops-raw/ascendc/ops-nn").rename(self.root / "offline-backup")
        card.path.write_text(f"# Fixture\n\n[code]({target})\n")
        document = SimpleNamespace(path=card.path, parse_error=None)
        context = SimpleNamespace(checked_local_roots=set())
        self.assertEqual([], link_checks.check(self.contract, document, context))
        card.path.write_text(card.path.read_text().replace(self.revision, "a" * 40))
        self.assertTrue(link_checks.check(self.contract, document, context))
