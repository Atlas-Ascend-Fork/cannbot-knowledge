# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Read-only selected-card reading and resource resolution for the API consumer."""

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml

from evals.test_retrieval_index import make_root


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/ascendc-api-knowledge-query/scripts/resolve_resources.py"
SPEC = importlib.util.spec_from_file_location("ascendc_api_resolve_resources", SCRIPT)
resolver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resolver)


class HeaderResolutionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package = self.root / "CANN package" / "asc-devkit"
        self.relative = "include/basic_api/example.h"
        self.header = self.package / self.relative
        self.header.parent.mkdir(parents=True)
        self.header.write_text("// fixture declaration\n", encoding="utf-8")

    def invoke(self, *headers, package=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "headers", "--package-root", str(package or self.package), *headers],
            cwd=self.root, text=True, capture_output=True, check=False,
        )

    def test_absolute_path_with_spaces_is_resolved_read_only_and_deduplicated(self):
        before = self.header.read_bytes(), self.header.stat().st_mtime_ns
        result = self.invoke(self.relative, self.relative)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(str(self.package), payload["package_root"])
        self.assertEqual([{"relative": self.relative, "absolute_path": str(self.header)}], payload["headers"])
        self.assertEqual(before, (self.header.read_bytes(), self.header.stat().st_mtime_ns))
        self.assertEqual([self.header], [path for path in self.root.rglob("*") if path.is_file()])
        self.assertIn("not checked", payload["version_evidence"])

    def test_package_root_is_not_inferred_from_current_directory(self):
        for package in (Path("asc-devkit"), self.header, self.root / "absent"):
            with self.subTest(package=package):
                result = self.invoke(self.relative, package=package)
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)

    def test_unsafe_relative_paths_are_rejected(self):
        paths = ["/include/example.h", "../example.h", "include/../outside.h", "include//example.h",
                 "include/./example.h", "include\\example.h", "include/example.h#L1",
                 "include/example.h?raw=1", "https://example.invalid/include/x.h", "include/x\n.h",
                 "include", " include/basic_api/example.h", "include/basic_api/example.h "]
        for relative in paths:
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                resolver.resolve_headers(self.package, [relative])

    def test_empty_selection_and_directories_are_not_headers(self):
        for headers in ([], ["include/basic_api"]):
            with self.subTest(headers=headers), self.assertRaises(ValueError):
                resolver.resolve_headers(self.package, headers)

    def test_missing_header_does_not_emit_partial_results_or_search_other_versions(self):
        other = self.root / "other-version/include/basic_api/missing.h"
        other.parent.mkdir(parents=True)
        other.write_text("// unrelated version\n", encoding="utf-8")
        result = self.invoke(self.relative, "include/basic_api/missing.h")
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("confirm the package root and CANN version", result.stderr)
        self.assertNotIn(str(other), result.stderr)

    def test_confirmed_root_symlink_and_internal_symlink_are_supported(self):
        alias = self.root / "confirmed-package"
        alias.symlink_to(self.package, target_is_directory=True)
        link = self.package / "include/alias.h"
        link.symlink_to(self.header)
        result = self.invoke("include/alias.h", package=alias)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(str(self.header), json.loads(result.stdout)["headers"][0]["absolute_path"])

    def test_symlink_escape_dangling_link_and_loop_fail_closed(self):
        outside = self.root / "outside.h"
        outside.write_text("// outside selected SDK\n", encoding="utf-8")
        links = {"outside.h": outside, "dangling.h": self.package / "absent.h",
                 "loop.h": self.package / "include/loop.h"}
        for name, destination in links.items():
            (self.package / "include" / name).symlink_to(destination)
            with self.subTest(name=name):
                result = self.invoke(f"include/{name}")
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)


class CardResourceResolutionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        make_root(self.root)
        self.card = self.root / "knowledge/ops/ascendc/apis/synthetic_api.md"
        self.resource = "cann-docs-raw/fixture/source.h"
        self.raw = self.root / self.resource
        self.raw.parent.mkdir(parents=True)
        self.raw.write_text("// source fixture\n")
        self.write_card()

    def write_card(self, *, resource=None, body="# Fixture\n"):
        self.card.write_text("---\n" + yaml.safe_dump({
            "type": "API", "title": "Fixture",
            "sources": [{"resource": resource or self.resource, "role": "primary"}],
        }) + "---\n" + body)

    def invoke(self, mode, value, *, root=True, cwd=None, card=None):
        command = [sys.executable, str(SCRIPT), mode, "--card", str(card or self.card), value]
        if root:
            command.extend(["--knowledge-root", str(self.root)])
        return subprocess.run(command, cwd=cwd or self.root, capture_output=True, text=True, check=False)

    def test_source_uses_repository_not_bundle_and_is_read_only(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        result = self.invoke("source", self.resource)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(str(self.raw), payload["absolute_path"])
        self.assertEqual(str(self.root), payload["repository_root"])
        self.assertEqual(str(self.root / "knowledge"), payload["bundle_root"])
        self.assertNotIn("card_lines", payload)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_relative_link_and_anchor_use_current_card_directory(self):
        target = self.root / "knowledge/ops/ascendc/runbooks/fixture.md"
        target.parent.mkdir()
        target.write_text("# Fixture\n\n正文第一行\n正文末行", encoding="utf-8")
        link = "../runbooks/fixture.md#details"
        self.write_card(body=f"# Fixture\n[Context]({link})\n")
        result = self.invoke("link", link)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(str(target), json.loads(result.stdout)["absolute_path"])
        self.assertEqual("details", json.loads(result.stdout)["anchor"])
        self.assertEqual(4, json.loads(result.stdout)["card_lines"])

    def test_index_is_navigation_not_a_card_even_when_linked(self):
        target = self.card.parent / "index.md"
        for link in ("index.md", "/" + target.relative_to(self.root / "knowledge").as_posix()):
            with self.subTest(link=link):
                self.write_card(body=f"# Fixture\n[Navigation]({link})\n")
                result = self.invoke("link", link)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(str(target), json.loads(result.stdout)["absolute_path"])
                self.assertNotIn("card_lines", json.loads(result.stdout))

    def test_bundle_root_links_follow_the_same_contract_as_navigation(self):
        target = self.card.parent / "linked.md"
        target.write_text("# Linked\n")
        for link in ("/ops/ascendc/apis/linked.md#details", "/ops/ascendc/apis/%6cinked.md"):
            for body in (f"# Fixture\n[Related]({link})\n", f"# Fixture\n[Related][target]\n\n[target]: {link}\n"):
                with self.subTest(link=link, body=body):
                    self.write_card(body=body)
                    contract, _ = resolver.load_contract(self.root)
                    knowledge = importlib.import_module(type(contract).__module__)
                    expected = dict(knowledge.relative_markdown_links(self.card, self.root / "knowledge"))[link]
                    self.assertEqual(target, expected)
                    result = self.invoke("link", link)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(str(expected), json.loads(result.stdout)["absolute_path"])

    def test_fragment_only_link_resolves_to_current_card(self):
        self.write_card(body="# Fixture\n[Details](#details)\n\n## Details\n")
        result = self.invoke("link", "#details")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(str(self.card), payload["absolute_path"])
        self.assertEqual("details", payload["anchor"])

    def test_bundle_root_link_cannot_escape_through_traversal_or_symlink(self):
        outside = self.root / "outside.md"
        outside.write_text("# Outside\n")
        escaped = self.card.parent / "escaped.md"
        escaped.symlink_to(outside)
        for link in ("/../outside.md", "/%2e%2e/outside.md", "/ops/ascendc/apis/escaped.md", "//example.invalid/card.md"):
            with self.subTest(link=link):
                self.write_card(body=f"# Fixture\n[Invalid]({link})\n")
                result = self.invoke("link", link)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_undeclared_source_link_image_and_code_are_not_reading_targets(self):
        self.write_card(body="# Fixture\n![Image](../image.md)\n```\n[Example](../code.md)\n```\n")
        for mode, value in (("source", "cann-docs-raw/other.h"), ("link", "../image.md"), ("link", "../code.md")):
            with self.subTest(mode=mode, value=value):
                result = self.invoke(mode, value)
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)

    def test_missing_source_reports_only_the_exact_resolved_path(self):
        missing = "cann-docs-raw/fixture/missing.h"
        self.write_card(resource=missing)
        result = self.invoke("source", missing)
        self.assertEqual(2, result.returncode)
        self.assertIn(str(self.root / missing), result.stderr)
        self.assertEqual("", result.stdout)

    def test_registered_git_source_and_link_share_pinned_resolution(self):
        contract, _ = resolver.load_contract(self.root)
        module = importlib.import_module(f"{type(contract).__module__.rsplit('.', 1)[0]}.source_resources")
        definition = next(item for item in contract.local_sources.values() if item.get("kind") == "git")
        revision = definition["revisions"][0]
        resource = f"{definition['root']}/{revision}/kernel.h"
        target = self.root / resource
        target.parent.mkdir(parents=True)
        target.write_text("// fixture\n")
        link = "../../../../" + resource + "#L1"
        remote = f"{definition['repository']}/blob/{revision}/kernel.h"
        for value, source in ((resource, True), (remote, True), (link, False)):
            self.write_card(resource=value, body=f"# Fixture\n[Source]({link})\n")
            with self.subTest(value=value), mock.patch.object(module, "validate_checkout") as validate:
                payload = resolver.resolve_card_resource(self.root, self.card, value, source=source)
                self.assertEqual(str(target), payload["absolute_path"])
                self.assertEqual(revision, payload["revision"])
                validate.assert_called_once_with(self.root, definition, revision)
        with mock.patch.object(module, "validate_checkout", side_effect=ValueError("dirty checkout")):
            with self.assertRaisesRegex(ValueError, "dirty checkout"):
                resolver.resolve_card_resource(self.root, self.card, link, source=False)

    def test_unsafe_or_unknown_sources_and_symlink_escape_fail_closed(self):
        for value in ("../outside.h", "https://example.invalid/source.h", "cann-docs-raw/../outside.h"):
            self.write_card(resource=value)
            self.assertEqual(2, self.invoke("source", value).returncode)
        outside = self.root / "outside.h"
        outside.write_text("// outside registered root\n")
        escaped = self.raw.parent / "escape.h"
        escaped.symlink_to(outside)
        resource = escaped.relative_to(self.root).as_posix()
        self.write_card(resource=resource)
        self.assertEqual(2, self.invoke("source", resource).returncode)

    def test_local_link_cannot_escape_bundle_without_registered_source(self):
        for link in ("../../../../outside.h", "https://example.invalid/remote.md", "/etc/hosts"):
            self.write_card(body=f"# Fixture\n[Link]({link})\n")
            result = self.invoke("link", link)
            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)

    def test_project_config_and_wrong_bundle_root_boundary(self):
        project = self.root / "consumer project"
        (project / ".cannbot").mkdir(parents=True)
        (project / ".cannbot/knowledge.env").write_text(f'CANNBOT_KNOWLEDGE_ROOT="{self.root}"\n')
        result = self.invoke("source", self.resource, root=False, cwd=project)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(str(self.raw), json.loads(result.stdout)["absolute_path"])
        result = self.invoke("source", self.resource, card=Path("knowledge/ops/ascendc/apis/synthetic_api.md"))
        self.assertEqual(2, result.returncode)
        self.root = self.root / "knowledge"
        result = self.invoke("source", self.resource)
        self.assertEqual(2, result.returncode)
        self.assertIn("invalid cannbot-knowledge root", result.stderr)

    def test_mismatched_contract_and_duplicate_frontmatter_fail_cleanly(self):
        self.card.write_text("---\nsources: []\nsources: []\n---\n# Fixture\n")
        result = self.invoke("source", self.resource)
        self.assertEqual(2, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        contract = self.root / "governance/contracts/knowledge.py"
        contract.write_text(contract.read_text() + "\nraise RuntimeError('must not execute')\n")
        result = self.invoke("source", self.resource)
        self.assertEqual(2, result.returncode)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("must not execute", result.stderr)


class CardReadingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        make_root(self.root)
        self.card = self.root / "knowledge/ops/ascendc/apis/synthetic_api.md"

    @staticmethod
    def unpack(page):
        rows = page.splitlines()
        metadata = json.loads(rows[0].removeprefix("CARD_PAGE "))
        end = next(i for i, line in enumerate(rows) if line.startswith("END_CARD_PAGE "))
        content = []
        for row in rows[1:end]:
            number, role, original = row.split("\t", 2)
            navigation = any(first <= int(number) <= last for first, last in metadata["navigation_ranges"])
            if role != ("导航" if navigation else "卡片"):
                raise AssertionError("line role does not match its navigation range")
            content.append((number, original))
        footer = json.loads(rows[end].removeprefix("END_CARD_PAGE "))
        return metadata, content, footer

    def test_pages_preserve_all_lines_and_navigation_without_writing(self):
        body = "\n".join(f"正文 {number}: 字节、元素、块。" for number in range(886))
        nav = "\n\n- [Link](other.md)\n"
        self.card.write_text("---\ntitle: Fixture\ntype: API\n---\n# Fixture\n" + body + nav, encoding="utf-8")
        original = self.card.read_bytes()
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        observed = []
        start = 1
        fingerprint = None
        while start is not None:
            metadata, lines, footer = self.unpack(resolver.read_card_page(self.root, self.card, start, fingerprint))
            self.assertEqual(start, metadata["start_line"])
            self.assertEqual(int(lines[-1][0]), footer["end_line"])
            self.assertNotIn("end_line", metadata)
            self.assertEqual(len(original.decode().splitlines()), metadata["card_lines"])
            self.assertEqual(hashlib.sha256(original).hexdigest(), metadata["file_sha256"])
            self.assertEqual(metadata["file_sha256"], footer["file_sha256"])
            self.assertNotIn("card_sha256", metadata)
            self.assertEqual(footer["next_start_line"] is None, footer["end_of_file"])
            self.assertLessEqual(sum(len(number) + len(line) + 2 for number, line in lines), resolver.PAGE_CHAR_BUDGET)
            observed.extend(lines)
            start = footer["next_start_line"]
            fingerprint = footer["file_sha256"]
        self.assertGreater(int(observed[-1][0]), len(lines))
        self.assertEqual([(str(i), line) for i, line in enumerate(original.decode().splitlines(), 1)], observed)
        self.assertEqual([], metadata["navigation_ranges"])
        self.assertEqual("- [Link](other.md)", observed[-1][1])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_continuation_requires_unchanged_content_not_only_unchanged_length(self):
        metadata, _, _ = self.unpack(resolver.read_card_page(self.root, self.card))
        with self.assertRaisesRegex(ValueError, "continuation requires"):
            resolver.read_card_page(self.root, self.card, 2)
        for value in (0, -1, metadata["card_lines"] + 1):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "start-line"):
                resolver.read_card_page(self.root, self.card, value, metadata["file_sha256"])
        original = self.card.read_bytes()
        replacement = bytes([original[0] ^ 1]) + original[1:]
        self.card.write_bytes(replacement)
        with self.assertRaisesRegex(ValueError, "card changed"):
            resolver.read_card_page(self.root, self.card, 2, metadata["file_sha256"])

    def test_truncated_page_prefix_cannot_advertise_a_future_page_cursor(self):
        self.card.write_text("---\ntitle: Fixture\n---\n" + "original content\n" * 600)
        page = resolver.read_card_page(self.root, self.card)
        metadata, lines, footer = self.unpack(page)
        prefix = page.splitlines()[:10]
        self.assertLess(int(prefix[-1].split("\t", 1)[0]), footer["end_line"])
        self.assertTrue({"end_line", "next_start_line", "next_command", "end_of_file"}.isdisjoint(metadata))
        self.assertEqual(int(lines[-1][0]), footer["end_line"])
        self.assertEqual(footer["end_line"] + 1, footer["next_start_line"])
        with self.assertRaises(StopIteration):
            self.unpack("\n".join(prefix))

    def test_returned_continuation_runs_for_a_quoted_card_path(self):
        import shlex

        self.card = self.card.parent / "a 'quoted' card.md"
        self.card.write_text("---\ntitle: Fixture\n---\n" + "original content\n" * 600)
        _, first_lines, footer = self.unpack(resolver.read_card_page(self.root, self.card))
        self.assertIsNotNone(footer["next_command"])
        seen = list(first_lines)
        while footer["next_command"] is not None:
            command = shlex.split(footer["next_command"])
            self.assertEqual(str(self.card), command[command.index("--card") + 1])
            self.assertEqual(str(self.root), command[command.index("--knowledge-root") + 1])
            result = subprocess.run(command, cwd="/tmp", text=True, capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            _, lines, footer = self.unpack(result.stdout)
            seen.extend(lines)
        self.assertTrue(footer["end_of_file"])
        self.assertEqual([(str(i), line) for i, line in enumerate(self.card.read_text().splitlines(), 1)], seen)

    def test_read_cli_rejects_index_outside_bundle_symlinks_and_nonabsolute_paths(self):
        outside = self.root / "outside.md"
        outside.write_text("not a card\n")
        alias = self.card.parent / "escape.md"
        alias.symlink_to(outside)
        for card in (outside, alias, self.card.parent / "index.md", Path("knowledge/ops/ascendc/apis/synthetic_api.md")):
            with self.subTest(card=card):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "read", "--knowledge-root", str(self.root), "--card", str(card)],
                    cwd=self.root, text=True, capture_output=True, check=False,
                )
                self.assertEqual(2, result.returncode, result.stdout)
                self.assertEqual("", result.stdout)

    def test_read_cli_returns_original_text_and_a_changed_fingerprint_fails_without_partial_output(self):
        command = [sys.executable, str(SCRIPT), "read", "--knowledge-root", str(self.root), "--card", str(self.card)]
        result = subprocess.run(command, cwd=self.root, text=True, capture_output=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        metadata, lines, footer = self.unpack(result.stdout)
        self.assertEqual(self.card.read_text().splitlines(), [line for _, line in lines])
        self.assertTrue(footer["end_of_file"])
        title = yaml.safe_load(self.card.read_text().split("---", 2)[1])["title"]
        self.assertIn("引用此卡：" + resolver.local_markdown_link(title, self.card), result.stdout)
        self.card.write_text(self.card.read_text() + "\nchanged\n")
        result = subprocess.run(command + ["--sha256", metadata["file_sha256"]], cwd=self.root, text=True,
                                capture_output=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("card changed", result.stderr)

    def test_a_long_line_is_not_silently_truncated(self):
        self.card.write_text("---\ntitle: Fixture\n---\n" + "x" * (resolver.PAGE_CHAR_BUDGET + 1))
        first, first_lines, footer = self.unpack(resolver.read_card_page(self.root, self.card))
        _, remaining, last = self.unpack(resolver.read_card_page(
            self.root, self.card, footer["next_start_line"], first["file_sha256"],
        ))
        self.assertTrue(last["end_of_file"])
        self.assertEqual(self.card.read_text().splitlines(), [line for _, line in first_lines + remaining])

    def test_read_selected_link_uses_its_exact_target_and_rejects_undeclared_links(self):
        target = self.card.parent / "linked.md"
        target.write_text("---\ntitle: Linked\ntype: API\n---\n# Linked\nOriginal content.\n")
        root_link = "/" + target.relative_to(self.root / "knowledge").as_posix() + "#detail"
        self.card.write_text(self.card.read_text() + f"\n[Linked](linked.md#detail)\n[Root]({root_link})\n[Self](#self)\n")
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        command = [sys.executable, str(SCRIPT), "read", "--knowledge-root", str(self.root), "--card", str(self.card)]
        for link, expected in (("linked.md#detail", target), (root_link, target), ("#self", self.card)):
            with self.subTest(link=link):
                result = subprocess.run(command + ["--link", link], cwd=self.root, text=True,
                                        capture_output=True, check=False)
                self.assertEqual(0, result.returncode, result.stderr)
                metadata, lines, _ = self.unpack(result.stdout)
                self.assertEqual(str(expected), metadata["card"])
                self.assertEqual(expected.read_text().splitlines(), [line for _, line in lines])
        result = subprocess.run(command + ["--link", "linked.md"], cwd=self.root, text=True,
                                capture_output=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_field_comparison_preserves_ordinary_links_and_excludes_metadata(self):
        other = self.card.parent / "other.md"
        self.card.write_bytes(
            b'---\ntitle: "span metadata only"\nplatforms: [a2]\nstatus: stable\n---\n'
            b'\n# Fixture\n\nspan has an 8-byte unit.\n\n'
            b'- [span related](other.md)\n'
        )
        other.write_bytes(b'---\ntitle: "span = length;"\n---\n\n    span = length;\r\n')
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        result = resolver.compare_card_field(self.root, [self.card, other], "span")
        self.assertTrue(result["partial_context_only"])
        self.assertEqual(2, len(result["cards"]))
        for item, path in zip(result["cards"], (self.card, other)):
            original = path.read_text().splitlines()
            for line in item["numbered_context"]:
                number, raw = line.split("\t", 1)
                self.assertEqual(original[int(number) - 1], raw)
                self.assertNotIn("metadata only", raw)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["file_sha256"])
        self.assertIn("9\tspan has an 8-byte unit.", result["cards"][0]["numbered_context"])
        self.assertIn("11\t- [span related](other.md)", result["cards"][0]["numbered_context"])
        self.assertEqual(["5\t    span = length;"], result["cards"][1]["numbered_context"])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_comparison_rejects_non_cards_duplicates_and_bad_fields(self):
        other = self.card.parent / "other.md"
        other.write_text("# Fixture\nfield\n")
        for cards, field in (([self.card, self.card], "field"), ([self.card], "field"),
                             ([self.card, self.card.parent / "index.md"], "field"),
                             ([self.card, other], ""), ([self.card, other], "field\n")):
            with self.subTest(cards=cards, field=field), self.assertRaises(ValueError):
                resolver.compare_card_field(self.root, cards, field)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "compare", "--knowledge-root", str(self.root),
             "--card", str(self.card), "--card", str(other), "--field", "missing"],
            cwd=self.root, text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([[], []], [item["numbered_context"] for item in json.loads(result.stdout)["cards"]])


if __name__ == "__main__":
    unittest.main()
