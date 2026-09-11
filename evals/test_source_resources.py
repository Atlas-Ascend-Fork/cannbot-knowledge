# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Pinned source provenance, extraction and bounded API navigation regressions."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib
import json
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
api_links = importlib.import_module("api_operator_links")
resource_tool = importlib.import_module("source_resources")
resources = api_links.resources
Contract = api_links.ingest.contract_module().Contract
link_checks = resource_tool.links


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
            "repository": "https://gitcode.com/cann/ops-nn", "fetch_script": "get_resources.sh",
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

    def card(self, relative, body, *, title="Fixture", sources=()):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"type": "Operator" if "/operators/" in relative else "API", "title": title,
                    "description": "Fixture", "tags": ["task.lookup", "topic.compilation"],
                    "status": "stable", "sources": [{"resource": value, "role": "implementation"} for value in sources],
                    "platforms": ["a2"], "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z"}
        path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body)
        return api_links.split_card(path, self.root)

    def api(self):
        return self.card("knowledge/ops/ascendc/apis/system/get_block_idx.md", "# GetBlockIdx\n\n## 函数原型\n\n```cpp\nint GetBlockIdx(void);\n```\n", title="GetBlockIdx")

    def operator(self, number=0, body="# Fixture\n", sources=None, family="nn"):
        if sources is None:
            sources = [f"cann-ops-raw/ascendc/ops-nn/{self.revision}/kernel.h"]
        return self.card(f"knowledge/ops/ascendc/operators/aclnn/{family}/fixture/op_{number}.md", body, title=f"Operator {number}", sources=sources)

    def test_remote_variants_and_local_paths_keep_identical_revision(self):
        expected = f"cann-ops-raw/ascendc/ops-nn/{self.revision}/kernel.h"
        for spelling in (f"https://gitcode.com/cann/ops-nn/blob/{self.revision}/kernel.h", f"https://gitcode.com/cann/ops-nn/-/blob/{self.revision}/kernel%2Eh", expected):
            self.assertEqual(expected, resources.git_source(self.contract, spelling).resource)
        self.assertIsNone(resources.git_source(self.contract, "https://gitcode.com/cann/opbase/blob/" + "a" * 40 + "/file.h"))

    def test_source_paths_reject_unknown_commit_traversal_and_git_internals(self):
        for value in (f"cann-ops-raw/ascendc/ops-nn/{'a' * 40}/kernel.h", f"cann-ops-raw/ascendc/ops-nn/{self.revision}/../kernel.h", f"cann-ops-raw/ascendc/ops-nn/{self.revision}/.git/config", f"https://gitcode.com/cann/ops-nn/blob/{self.revision}/%2e%2e/kernel.h"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resources.git_source(self.contract, value)

    def test_git_registry_and_display_limit_have_acceptance_and_rejection_cases(self):
        Contract(self.root)
        for value in (0, -1, True, "10"):
            self.registry["local_sources"]["cann_docs_raw"]["mirror"]["api_operator_display_limit"] = value
            self.save_registry()
            with self.assertRaisesRegex(ValueError, "positive integer"):
                Contract(self.root)
        self.registry["local_sources"]["cann_docs_raw"]["mirror"]["api_operator_display_limit"] = 10
        for revisions in ([], ["main"], [self.revision, self.revision]):
            self.definition["revisions"] = revisions
            self.save_registry()
            with self.assertRaisesRegex(ValueError, "40-hex revisions"):
                Contract(self.root)

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
        source_checks = importlib.import_module(f"{api_links.ingest.contract_package().__name__}.checks.sources")
        restored_checks = importlib.import_module(f"{api_links.ingest.contract_package().__name__}.checks.local_sources")
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

    def test_audit_destinations_reject_escape_and_symlinks(self):
        expected = self.root / "artifacts/graphs/evidence.json"
        self.assertEqual(expected, api_links.ingest.graph_artifact_path(self.root, "artifacts/graphs/evidence.json"))
        for target in ("knowledge/overwritten.md", "artifacts/graphs/../../../outside.json"):
            with self.assertRaises(ValueError):
                api_links.ingest.graph_artifact_path(self.root, target)
        (self.root / "artifacts").symlink_to(self.checkout, target_is_directory=True)
        with self.assertRaises(ValueError):
            api_links.ingest.graph_artifact_path(self.root, "artifacts/graphs/evidence.json")

    def test_local_sources_bind_reference_inventory_without_losing_revision(self):
        inventory = importlib.import_module("reference_inventory")
        record = {"source": {"repo": self.definition["repository"], "commit": self.revision}}
        resource = f"cann-ops-raw/ascendc/ops-nn/{self.revision}/kernel.h"
        self.assertTrue(inventory.source_binds_entry(resource, record, "kernel.h", self.contract))
        self.assertFalse(inventory.source_binds_entry(resource, record, "notes.md", self.contract))
        record["source"]["commit"] = "a" * 40
        self.assertFalse(inventory.source_binds_entry(resource, record, "kernel.h", self.contract))

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

    def test_source_verification_still_requires_restored_clean_checkouts(self):
        self.api()
        self.operator()
        (self.checkout / "kernel.h").write_text(self.raw + "// local change\n")
        with self.assertRaisesRegex(ValueError, "local changes"):
            api_links.invocations(self.root)
        (self.root / "cann-ops-raw/ascendc/ops-nn").rename(self.root / "offline-backup")
        with self.assertRaisesRegex(ValueError, "missing pinned Git checkout"):
            api_links.invocations(self.root)

    def test_suggestions_preserve_cards_and_repeat_without_a_graph_cache(self):
        api = self.api()
        operator = self.operator()
        original = {card.path: card.path.read_bytes() for card in (api, operator)}
        args = SimpleNamespace(knowledge_root=str(self.root), report="artifacts/graphs/api_operator_links.json", command="suggest")
        self.assertEqual(0, api_links.command(args))
        report = self.root / args.report
        payload = json.loads(report.read_text())
        self.assertEqual(1, len(payload["suggested_markdown"]))
        self.assertEqual(api.relative, payload["suggested_markdown"][0]["card"])
        self.assertIn(operator.path.name, payload["suggested_markdown"][0]["link"])
        self.assertIn("source", payload["suggested_markdown"][0]["evidence"])
        before = report.read_bytes()
        self.assertEqual(0, api_links.command(args))
        self.assertEqual(before, report.read_bytes())
        self.assertEqual(original, {path: path.read_bytes() for path in original})
        self.assertFalse((self.root / "artifacts/graphs/graph.json").exists())
        args.report = "knowledge/escaped.json"
        with self.assertRaisesRegex(ValueError, "artifacts/graphs"):
            api_links.command(args)

    def test_source_links_allow_registered_files_but_not_indexes_or_unknown_roots(self):
        card = self.operator()
        target = os.path.relpath(self.checkout / "kernel.h", card.path.parent) + "#L3"
        card.path.write_text(f"# Fixture\n\n[code]({target})\n")
        document = SimpleNamespace(path=card.path, parse_error=None)
        context = SimpleNamespace(checked_local_roots=set())
        self.assertEqual([], link_checks.check(self.contract, document, context))
        index = card.path.with_name("index.md")
        index.write_text(card.path.read_text())
        document.path = index
        self.assertIn("link.outside_bundle", {item.code for item in link_checks.check(self.contract, document, None)})
        document.path = card.path
        card.path.write_text("# Fixture\n\n[x](../../../../../../../../governance/specs/okf.md)\n")
        self.assertTrue(link_checks.check(self.contract, document, None))

    def test_lexer_masks_comments_literals_continuations_and_inactive_arms(self):
        raw = ('// Fake(); \\\nFake();\n/* Fake(); */\n"Fake()"; R"x(Fake())x";\n'
               '#define F Fake() \\\nFake()\n#if 0\nFake();\n#else\nReal();\n#endif\n')
        masked = api_links.mask_source(raw)
        self.assertEqual(len(raw), len(masked))
        self.assertEqual(raw.count("\n"), masked.count("\n"))
        self.assertNotIn("Fake", api_links.call_names(masked))
        self.assertIn("Real", api_links.call_names(masked))

    def test_source_calls_bind_exact_file_hash_line_and_anchor(self):
        self.api()
        self.operator()
        _, _, items, _, audit = api_links.invocations(self.root)
        self.assertEqual(1, len(items))
        evidence = items[0].source
        self.assertEqual(self.revision, evidence["revision"])
        self.assertEqual(3, evidence["line"])
        self.assertEqual(self.raw.splitlines()[2].strip(), evidence["anchor"])
        self.assertEqual(hashlib.sha256(self.raw.encode()).hexdigest(), evidence["sha256"])
        self.assertEqual(1, audit["counts"]["source_backed_invocations"])

    def test_missing_declared_source_does_not_create_source_evidence(self):
        self.api()
        self.operator(sources=[f"cann-ops-raw/ascendc/ops-nn/{self.revision}/missing.h"])
        _, _, items, _, audit = api_links.invocations(self.root)
        self.assertEqual([], items)
        self.assertEqual(1, audit["counts"]["missing_source_files"])

    def test_source_receiver_requires_type_namespace_and_global_family_uniqueness(self):
        api = self.card("knowledge/ops/ascendc/apis/local_tensor/get_size.md", "# GetSize\n\n## 函数原型\n\nint GetSize();\n", title="GetSize")
        for body, expected in (("AscendC::LocalTensor<int> x;\nx.GetSize();", True), ("Other::LocalTensor<int> x;\nx.GetSize();", False), ("localTensor.GetSize();", False)):
            match = api_links.call_names(body)["GetSize"][-1]
            self.assertEqual(expected, api_links.source_identity(api, body, match, set(), api_links.source_receivers(body)))
        body = "using namespace AscendC;\nOther::LocalTensor::GetSize();"
        self.assertFalse(api_links.source_identity(api, body, api_links.call_names(body)["GetSize"][0], set(), {}))
        # Identical same-name families cannot be disambiguated by arity or platform.
        first = self.api()
        second = replace(first, path=first.path.with_name("other.md"), relative=first.relative.replace("get_block_idx", "other"), platforms=("950",))
        op = self.operator()
        with mock.patch.object(api_links, "cards_below", side_effect=[[first, second], [op]]):
            self.assertEqual([], api_links.invocations(self.root)[2])

    def test_projection_is_bounded_source_first_diverse_and_preserves_full_audit(self):
        api = self.api()
        operators = [self.operator(number, family="nn" if number < 12 else "math") for number in range(14)]
        source = {"resource": f"cann-ops-raw/ascendc/ops-nn/{self.revision}/kernel.h", "line": 3}
        items = [api_links.Invocation(api, op, "GetBlockIdx", "int GetBlockIdx(void);", "", "high", source if index else None) for index, op in enumerate(operators)]
        displayed = api_links.displayed_invocations([api], items, 10)
        self.assertEqual(10, len(displayed))
        self.assertTrue(all(item.source for item in displayed))
        self.assertTrue(any("/math/" in item.operator.relative for item in displayed))
        payload = api_links.artifact_payload([api], operators, items, [], {"counts": {}, "source_files": []}, 10)
        self.assertEqual(14, len(payload["relations"]))
        self.assertEqual(10, sum(item["displayed"] for item in payload["relations"]))

    def test_body_only_suggestions_keep_their_evidence_distinct(self):
        api = self.api()
        op = self.operator()
        item = api_links.Invocation(api, op, "GetBlockIdx", "prototype", "GetBlockIdx()", "medium")
        payload = api_links.artifact_payload([api], [op], [item], [], {"counts": {}, "source_files": []}, 10)
        relation = payload["relations"][0]
        self.assertEqual("suggested_link", relation["relation"])
        self.assertEqual("GetBlockIdx()", relation["evidence"]["operator_anchor"])
        self.assertNotIn("source", relation["evidence"])

    def test_localization_preserves_code_fences_roles_and_missing_remote_sources(self):
        remote = f"https://gitcode.com/cann/ops-nn/blob/{self.revision}/kernel.h"
        missing = remote.replace("kernel.h", "missing.h")
        fenced = f"```markdown\n[not a link]({remote})\n```\n"
        op = self.operator(body=f"# Fixture\n\n[code]({remote}#L3)\n\n" + fenced, sources=[remote, missing])
        self.assertEqual(1, resource_tool.localize(self.root, "2026-08-18T00:00:00Z"))
        raw = api_links.read_utf8(op.path)
        self.assertIn(fenced, raw)
        self.assertIn(missing, raw)
        self.assertIn(f"cann-ops-raw/ascendc/ops-nn/{self.revision}/kernel.h#L3", raw)
        self.assertIn("role: implementation", raw)
        self.assertEqual(0, resource_tool.localize(self.root, "2026-08-18T00:00:00Z"))
        self.assertEqual(raw, api_links.read_utf8(op.path))

    def test_source_frontmatter_preserves_unrelated_yaml_formatting(self):
        raw = 'title: "Fixture"\ntags: [a, b] # retain comment\nsources:\n  - resource: "https://example.invalid/code"\n    role: implementation\nupdated_at: "2026-08-18T00:00:00Z"'
        metadata = yaml.safe_load(raw)
        metadata["sources"][0]["resource"] = "cann-ops-raw/ascendc/ops-nn/" + self.revision + "/kernel.h"
        metadata["updated_at"] = "2026-08-19T00:00:00Z"
        result = resource_tool.source_frontmatter(raw, metadata)
        self.assertEqual(raw.replace("https://example.invalid/code", metadata["sources"][0]["resource"]).replace("2026-08-18T00:00:00Z", "2026-08-19T00:00:00Z"), result)

    def test_fetch_refuses_unmanaged_or_symlink_roots_without_mutation(self):
        before = (self.checkout / "kernel.h").read_bytes()
        with self.assertRaisesRegex(ValueError, "unmanaged"):
            resource_tool.fetch_repository(self.root, self.definition)
        self.assertEqual(before, (self.checkout / "kernel.h").read_bytes())
        definition = {**self.definition, "root": "alias-src"}
        (self.root / "alias-src").symlink_to(self.root / "cann-ops-raw/ascendc/ops-nn", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            resource_tool.fetch_repository(self.root, definition)


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



class OperatorSourceCorpusTests(unittest.TestCase):
    """Keep the checked-in Operator corpus aligned with its restored baseline."""

    @classmethod
    def setUpClass(cls):
        cls.contract = Contract(ROOT)
        cls.operators = api_links.cards_below(ROOT, "knowledge/ops/ascendc/operators")
        cls.definitions = {
            item["repository"]: item for item in cls.contract.local_sources.values()
            if item.get("kind") == "git"
        }

    def test_direct_and_aclnn_share_one_registered_baseline_per_repository(self):
        revisions = {name: {"aclnn": set(), "direct": set()} for name in self.definitions}
        for card in self.operators:
            route = Path(card.relative).parts[4]
            for value in card.sources:
                source = resources.git_source(self.contract, value)
                if source is not None:
                    revisions[source.repository][route].add(source.revision)
        for repository, definition in self.definitions.items():
            with self.subTest(repository=repository):
                self.assertEqual(1, len(definition["revisions"]))
                expected = set(definition["revisions"])
                self.assertEqual(expected, revisions[repository]["aclnn"])
                self.assertEqual(expected, revisions[repository]["direct"])

    def test_all_registered_operator_sources_exist_in_restored_snapshots(self):
        # Offline unit runs remain possible; check.sh restores every snapshot first.
        for definition in self.definitions.values():
            for revision in definition["revisions"]:
                if not (ROOT / definition["root"] / revision / ".git").exists():
                    self.skipTest("source snapshots not restored; run get_resources.sh --code")
                resources.validate_checkout(ROOT, definition, revision)
        checked = set()
        for card in self.operators:
            for value in card.sources:
                source = resources.git_source(self.contract, value)
                if source is None or source.resource in checked:
                    continue
                checked.add(source.resource)
                with self.subTest(card=card.relative, source=value):
                    self.assertTrue(source.local_path(ROOT).exists(), "declared source missing in pinned commit")
        self.assertTrue(checked, "no registered Operator sources checked")


if __name__ == "__main__":
    unittest.main()
