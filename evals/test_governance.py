from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from governance.contracts.knowledge import (  # noqa: E402
    Contract,
    compare_trees,
    relative_markdown_links,
)


INGEST = ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
LINT = ROOT / ".agents/skills/knowledge-lint/scripts/knowledge_lint.py"
PINNED_SOURCE = (
    "https://gitcode.com/cann/asc-devkit/blob/"
    "c846650eec121f41bd0efa472fc5c84594b8208d/README.md"
)
SYNTHETIC_API_METADATA = {
    "type": "API",
    "title": "Synthetic API",
    "description": "Contract-only API fixture.",
    "tags": ["task.lookup", "topic.compilation"],
    "status": "stable",
    "sources": [{"resource": "https://example.com/cann/synthetic-api"}],
    "created_at": "2026-08-18T00:00:00Z",
    "updated_at": "2026-08-18T00:00:00Z",
    "platforms": ["a2"],
}


class RouteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = Contract(ROOT)

    def test_planned_routes_are_accepted(self) -> None:
        cases = {
            "knowledge/common/platforms/concepts/architecture.md": ("common", "platforms"),
            "knowledge/common/toolchains/runbooks/compilation/environment.md": ("common", "toolchains"),
            "knowledge/graph/torch_compile/concepts/capture.md": ("graph", "torch_compile"),
            "knowledge/graph/ge/apis/graph_api.md": ("graph", "ge"),
            "knowledge/model/inference/concepts/serving.md": ("model", "inference"),
            "knowledge/model/training/runbooks/runtime/oom.md": ("model", "training"),
            "knowledge/ops/triton/runbooks/compilation/missing_symbol.md": (
                "ops",
                "triton",
            ),
            "knowledge/runtime/apis/rt_api.md": ("runtime", None),
            "knowledge/runtime/runbooks/runtime/device_reset.md": ("runtime", None),
        }
        for value, expected in cases.items():
            with self.subTest(path=value):
                info = self.contract.derive_card_path(Path(value))
                self.assertEqual((info.domain, info.route), expected)
                self.assertFalse(info.doc_id.startswith("knowledge/"))

    def test_profiles_define_okf_types(self) -> None:
        expected = {
            "concepts": "Concept",
            "apis": "API",
            "examples": "Example",
            "operators": "Operator",
            "optimizations": "Optimization",
            "runbooks": "Runbook",
            "interoperability": "Interoperability",
            "glossaries": "Glossary",
        }
        self.assertEqual(expected, {name: self.contract.okf_type(name) for name in expected})

    def test_invalid_route_shapes_are_rejected(self) -> None:
        cases = (
            "knowledge/ops/apis/no_dsl.md",
            "knowledge/graph/ascendc/apis/wrong_domain.md",
            "knowledge/ops/ascendc/apis/unplanned/nested.md",
            "knowledge/ops/ascendc/operators/nn/activation/singular.md",
            "knowledge/ops/ascendc/interoperability/not_shared.md",
            "knowledge/common/platforms/chip.md",
            "knowledge/ops/ascendc/runbooks/timeout.md",
        )
        for value in cases:
            with self.subTest(path=value), self.assertRaises(ValueError):
                self.contract.derive_card_path(Path(value))

    def test_current_index_tree_is_complete(self) -> None:
        self.assertEqual(self.contract.validate_index_tree(), [])

    def test_registered_structure_is_materialized(self) -> None:
        expected = {
            "knowledge/common",
            "knowledge/graph",
            "knowledge/model",
            "knowledge/model/inference",
            "knowledge/model/training",
            "knowledge/model/shared",
            "knowledge/ops",
            "knowledge/ops/tilelang",
            "knowledge/ops/pypto",
            "knowledge/ops/triton",
            "knowledge/runtime",
        }
        actual = {path.as_posix() for path in self.contract.structural_directories()}
        self.assertEqual(expected | {"knowledge/ops/ascendc", "knowledge/ops/shared"}, actual)
        self.assertTrue(all((ROOT / path / "index.md").is_file() for path in expected))
        not_precreated = {
            "knowledge/common/toolchains",
            "knowledge/common/observability",
            "knowledge/common/glossaries",
            "knowledge/graph/ge",
            "knowledge/graph/torch_compile",
            "knowledge/graph/shared",
            "knowledge/runtime/concepts",
            "knowledge/runtime/apis",
            "knowledge/runtime/runbooks",
        }
        self.assertTrue(all(not (ROOT / path).exists() for path in not_precreated))

    def test_repository_contains_only_the_empty_skeleton(self) -> None:
        expected_directories = {
            "knowledge",
            "knowledge/common",
            "knowledge/graph",
            "knowledge/model",
            "knowledge/model/inference",
            "knowledge/model/shared",
            "knowledge/model/training",
            "knowledge/ops",
            "knowledge/ops/ascendc",
            "knowledge/ops/pypto",
            "knowledge/ops/shared",
            "knowledge/ops/tilelang",
            "knowledge/ops/triton",
            "knowledge/runtime",
        }
        actual_directories = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "knowledge").rglob("*")
            if path.is_dir()
        } | {"knowledge"}
        cards = [
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "knowledge").rglob("*.md")
            if path.name != "index.md"
        ]
        self.assertEqual(expected_directories, actual_directories)
        self.assertEqual([], cards)
        self.assertFalse(any(path.name == "concepts" for path in (ROOT / "knowledge").rglob("*")))

    def test_precreated_route_policy_is_declared_by_domain(self) -> None:
        enabled = {
            domain
            for domain, definition in self.contract.domains.items()
            if definition.get("precreate_routes", False)
        }
        self.assertEqual(enabled, {"ops", "model"})

    def test_bundle_root_declares_okf_version(self) -> None:
        self.assertEqual(
            [],
            self.contract.validate_index_frontmatter(
                Path("knowledge/index.md"),
                {"okf_version": "0.2"},
            ),
        )
        issues = self.contract.validate_index_frontmatter(Path("knowledge/index.md"), None)
        self.assertEqual(["index.frontmatter"], [issue.code for issue in issues])

    def test_card_type_must_match_path_profile(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["type"] = "Concept"
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("frontmatter.type", {issue.code for issue in issues})

    def test_bundle_absolute_markdown_link_resolves_from_bundle_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.md"
            path.write_text("[API](/ops/ascendc/apis/synthetic_api.md)\n", encoding="utf-8")
            links = relative_markdown_links(path, ROOT / "knowledge")
        self.assertEqual(
            [("/ops/ascendc/apis/synthetic_api.md", ROOT / "knowledge/ops/ascendc/apis/synthetic_api.md")],
            links,
        )

    def test_missing_index_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            (root / "knowledge/ops").mkdir(parents=True)
            (root / "knowledge/index.md").write_text("# Knowledge\n", encoding="utf-8")
            issues = Contract(root).validate_index_tree()
            self.assertIn("index.missing", {issue.code for _, issue in issues})

    def test_skill_mirror_difference_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            mirror = root / "mirror"
            source.mkdir()
            mirror.mkdir()
            (source / "SKILL.md").write_text("source", encoding="utf-8")
            (mirror / "SKILL.md").write_text("mirror", encoding="utf-8")
            self.assertEqual([issue.code for issue in compare_trees(source, mirror)], ["mirror.different"])


class IngestContractTests(unittest.TestCase):
    def run_ingest(
        self,
        extra: list[str],
        *,
        tags: tuple[str, ...] = ("task.lookup", "topic.compilation"),
        platforms: tuple[str, ...] = ("a2",),
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md") as body:
            body.write("# Candidate\n")
            body.flush()
            command = [
                sys.executable,
                str(INGEST),
                "--knowledge-root",
                str(ROOT),
                "create",
                "--path",
                "knowledge/ops/ascendc/concepts/contract_probe.md",
                "--title",
                "Contract probe",
                "--description",
                "Contract probe",
                "--source",
                PINNED_SOURCE,
                "--body-file",
                body.name,
                "--dry-run",
            ]
            for tag in tags:
                command.extend(["--tag", tag])
            for platform in platforms:
                command.extend(["--platform", platform])
            command.extend(extra)
            return subprocess.run(command, check=False, text=True, capture_output=True)

    def test_valid_candidate_is_rendered(self) -> None:
        result = self.run_ingest([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("type: Concept", result.stdout)
        self.assertIn("title: Contract probe", result.stdout)
        self.assertIn("resource: https://gitcode.com/", result.stdout)

    def test_profile_violations_are_rejected(self) -> None:
        cases = {
            "empty title": (["--title", ""], ("task.lookup", "topic.compilation"), ("a2",)),
            "missing topic": ([], ("task.lookup", "task.testing"), ("a2",)),
            "duplicate tag": ([], ("task.lookup", "topic.compilation", "topic.compilation"), ("a2",)),
            "mixed agnostic": ([], ("task.lookup", "topic.compilation"), ("a2", "agnostic")),
            "stable replacement": (
                [
                    "--status",
                    "stable",
                    "--replaced-by",
                    "ops/ascendc/concepts/replacement",
                ],
                ("task.lookup", "topic.compilation"),
                ("a2",),
            ),
        }
        for name, (extra, tags, platforms) in cases.items():
            with self.subTest(case=name):
                result = self.run_ingest(extra, tags=tags, platforms=platforms)
                self.assertEqual(result.returncode, 2, result.stdout)

    def test_verified_actor_contract(self) -> None:
        invalid = self.run_ingest(
            [
                "--verified-by",
                "reviewer",
                "--verified-at",
                "2026-08-15T08:00:00Z",
            ]
        )
        self.assertEqual(invalid.returncode, 2, invalid.stdout)
        self.assertIn("verified.actor", invalid.stderr)

        valid = self.run_ingest(
            [
                "--verified-by",
                "human:reviewer",
                "--verified-at",
                "2026-08-15T08:00:00Z",
            ]
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn("by: human:reviewer", valid.stdout)

        incomplete = self.run_ingest(["--verified-by", "human:reviewer"])
        self.assertEqual(incomplete.returncode, 2, incomplete.stdout)
        self.assertIn("must be provided together", incomplete.stderr)

    def test_unpinned_stable_git_source_is_rejected(self) -> None:
        result = self.run_ingest(
            ["--status", "stable", "--source", "https://github.com/triton-lang/triton-ascend/tree/main"]
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("source.pin", result.stderr)

    def test_pinned_raw_git_sources_are_accepted(self) -> None:
        commit = "c846650eec121f41bd0efa472fc5c84594b8208d"
        urls = (
            f"https://gitee.com/example/project/raw/{commit}/README.md",
            f"https://gitlab.com/example/project/-/raw/{commit}/README.md",
            f"https://raw.githubusercontent.com/example/project/{commit}/README.md",
            f"https://raw.gitcode.com/example/project/raw/{commit}/README.md",
        )
        for url in urls:
            with self.subTest(url=url):
                result = self.run_ingest(["--status", "stable", "--source", url])
                self.assertEqual(result.returncode, 0, result.stderr)


class MigratedSkillContractTests(unittest.TestCase):
    def test_query_receipt_is_versioned_and_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "search.json"
            command = [
                sys.executable,
                str(QUERY),
                "--knowledge-root",
                str(ROOT),
                "search",
                "--query",
                "missing API",
                "--technology",
                "ascendc",
                "--platform",
                "a2",
                "--decision",
                "empty corpus receipt",
                "--receipt",
                str(receipt),
                "--json",
            ]
            first = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "cannbot-knowledge-search.v2")
            self.assertEqual(payload["request"]["platforms"], ["a2"])
            self.assertTrue(payload["request_sha256"])
            self.assertTrue(payload["index"]["content_fingerprint"])
            self.assertTrue(payload["index"]["governance_fingerprint"])
            self.assertEqual(payload["result"]["count"], 0)
            self.assertTrue(all(hit["card_sha256"] for hit in payload["result"]["hits"]))
            self.assertTrue(all(hit["card_lines"] > 0 for hit in payload["result"]["hits"]))
            second = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite receipt", second.stderr)

    def test_strict_navigation_reports_broad_tree_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            card = root / "knowledge/ops/ascendc/operators/nn/activations/synthetic.md"
            card.parent.mkdir(parents=True)
            card.write_text(
                """---
type: Operator
title: Synthetic operator
description: Contract-only broad source fixture.
tags: [task.implementation, topic.activation]
status: draft
sources:
  - resource: https://gitcode.com/cann/ops-nn/tree/54beb3b1f2f32067ac026202546011cd1b03977f/activation/synthetic/
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: [a2]
---

# Synthetic operator

This isolated fixture verifies strict source navigation.
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINT),
                    "--knowledge-root",
                    str(root),
                    "--card",
                    "knowledge/ops/ascendc/operators/nn/activations/synthetic.md",
                    "--strict-navigation",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("source.navigation", result.stdout)


if __name__ == "__main__":
    unittest.main()
