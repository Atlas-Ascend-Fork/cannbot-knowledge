from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from governance.contracts.knowledge import (  # noqa: E402
    Contract,
    markdown_targets,
    relative_markdown_links,
)


INGEST = ROOT / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py"
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
INDEX = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
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


def load_lint_module():
    spec = importlib.util.spec_from_file_location("knowledge_lint_test", LINT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LINT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
            "knowledge/ops/ascendc/apis/basic_api/data_copy/example.md": ("ops", "ascendc"),
            "knowledge/ops/ascendc/guides/programming_guide/example.md": ("ops", "ascendc"),
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
            "guides": "Guide",
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
            "knowledge/ops/ascendc/glossaries/unplanned/nested.md",
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

    def test_repository_contains_ascendc_reference_corpus(self) -> None:
        cards = [
            path.relative_to(ROOT)
            for path in (ROOT / "knowledge").rglob("*.md")
            if path.name != "index.md"
        ]
        apis = [path for path in cards if "apis" in path.parts]
        guides = [path for path in cards if "guides" in path.parts]
        self.assertGreaterEqual(len(apis), 2810)
        self.assertGreaterEqual(len(guides), 270)
        self.assertTrue(
            all(path.parts[1:3] == ("ops", "ascendc") for path in [*apis, *guides])
        )
        self.assertNotIn(
            Path("knowledge/common/platforms/concepts/ascend_910b3_atlas_a2.md"),
            cards,
        )
        self.assertFalse((ROOT / "knowledge/common/platforms").exists())

    def test_ascend910b3_runbooks_are_not_scoped_to_a3(self) -> None:
        conflicts: list[str] = []
        runbooks = ROOT / "knowledge/ops/ascendc/runbooks"
        for card in sorted(runbooks.glob("*/*.md")):
            if card.name == "index.md":
                continue
            text = card.read_text(encoding="utf-8")
            metadata = yaml.safe_load(text.split("---", 2)[1])
            if "Ascend910B3" in text and "a3" in metadata.get("platforms", []):
                conflicts.append(card.relative_to(ROOT).as_posix())
        self.assertEqual([], conflicts)

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

    def test_profile_is_the_only_top_level_required_source(self) -> None:
        self.assertNotIn("required", self.contract.schema)
        self.assertEqual(
            {
                "type",
                "title",
                "description",
                "tags",
                "status",
                "sources",
                "created_at",
                "updated_at",
            },
            self.contract.common_fields,
        )
        self.assertEqual(
            ["resource"],
            self.contract.schema["properties"]["sources"]["items"]["required"],
        )

    def test_missing_required_fields_are_not_reported_twice(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for field in SYNTHETIC_API_METADATA:
            with self.subTest(field=field):
                metadata = dict(SYNTHETIC_API_METADATA)
                metadata.pop(field)
                issues = self.contract.validate_card(
                    relative,
                    metadata,
                    "# Synthetic API\n",
                )
                self.assertEqual(
                    ["frontmatter.required"],
                    [issue.code for issue in issues],
                )

    def test_blank_text_and_wrong_type_have_distinct_findings(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for field in ("title", "description"):
            for value in ("", "   "):
                with self.subTest(field=field, value=value):
                    metadata = dict(SYNTHETIC_API_METADATA)
                    metadata[field] = value
                    issues = self.contract.validate_card(
                        relative,
                        metadata,
                        "# Synthetic API\n",
                    )
                    self.assertEqual(
                        ["frontmatter.text"],
                        [issue.code for issue in issues],
                    )

        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["title"] = 7
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertEqual(["frontmatter.schema"], [issue.code for issue in issues])

    def test_missing_interoperability_endpoint_only_reports_required(self) -> None:
        relative = Path("knowledge/ops/shared/interoperability/synthetic.md")
        metadata = {
            **SYNTHETIC_API_METADATA,
            "type": "Interoperability",
            "source_technology": "ascendc",
            "target_technology": "triton",
        }
        for field in ("source_technology", "target_technology"):
            with self.subTest(field=field):
                candidate = dict(metadata)
                candidate.pop(field)
                issues = self.contract.validate_card(
                    relative,
                    candidate,
                    "# Synthetic interoperability\n",
                )
                self.assertEqual(
                    ["frontmatter.required"],
                    [issue.code for issue in issues],
                )

        invalid = dict(metadata)
        invalid["source_technology"] = []
        issues = self.contract.validate_card(
            relative,
            invalid,
            "# Synthetic interoperability\n",
        )
        self.assertEqual(["frontmatter.schema"], [issue.code for issue in issues])

    def test_missing_status_defers_dependent_checks(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = {
            **SYNTHETIC_API_METADATA,
            "sources": [],
            "platforms": [],
            "replaced_by": "ops/ascendc/apis/replacement",
        }
        metadata.pop("status")
        issues = self.contract.validate_card(
            relative,
            metadata,
            "# Synthetic API\n",
        )
        self.assertEqual(
            ["frontmatter.required"],
            [issue.code for issue in issues],
        )

    def test_missing_replacement_is_always_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = {
            **SYNTHETIC_API_METADATA,
            "status": "deprecated",
            "replaced_by": "ops/ascendc/apis/definitely_missing",
        }
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertTrue(
            any(
                issue.message.startswith("replacement card does not exist:")
                for issue in issues
            )
        )

    def test_hierarchical_tag_and_local_source_are_accepted(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/basic_api/data_copy/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["tags"] = ["task.lookup", "topic.implementation.api_layer.basic_api"]
        metadata["sources"] = [
            {
                "resource": "cann-docs-raw/any/fixed-archive/path.md",
                "role": "primary",
            }
        ]
        self.assertEqual([], self.contract.validate_card(relative, metadata, "# Synthetic API\n"))

    def test_stable_runbook_can_use_empty_sources(self) -> None:
        relative = Path("knowledge/ops/ascendc/runbooks/compilation/trajectory_finding.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata.update(
            {
                "type": "Runbook",
                "title": "Trajectory finding",
                "status": "stable",
                "sources": [],
            }
        )
        self.assertEqual([], self.contract.validate_card(relative, metadata, "# Trajectory finding\n"))

    def test_stable_non_runbook_still_requires_source(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["sources"] = []
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("source.required", {issue.code for issue in issues})

    def test_unregistered_local_source_is_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["sources"] = [
            {"resource": "unregistered-source/definitely/missing/source.md", "role": "primary"}
        ]
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("source.resource", {issue.code for issue in issues})

    def test_unsafe_local_sources_are_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        for resource in (
            "../outside.md",
            "/tmp/outside.md",
            "cann-docs-raw\\outside.md",
            "cann-docs-raw",
            "cann-docs-raw//outside.md",
            "https:///missing-host.md",
            "https://user:secret@example.com/source.md",
        ):
            with self.subTest(resource=resource):
                metadata = dict(SYNTHETIC_API_METADATA)
                metadata["sources"] = [{"resource": resource}]
                issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
                self.assertIn("source.resource", {issue.code for issue in issues})

    def test_unknown_hierarchical_tag_is_rejected(self) -> None:
        relative = Path("knowledge/ops/ascendc/apis/synthetic_api.md")
        metadata = dict(SYNTHETIC_API_METADATA)
        metadata["tags"] = ["task.lookup", "topic.implementation.not_registered"]
        issues = self.contract.validate_card(relative, metadata, "# Synthetic API\n")
        self.assertIn("tag.unknown", {issue.code for issue in issues})

    def test_bundle_absolute_markdown_link_resolves_from_bundle_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.md"
            path.write_text("[API](/ops/ascendc/apis/synthetic_api.md)\n", encoding="utf-8")
            links = relative_markdown_links(path, ROOT / "knowledge")
        self.assertEqual(
            [("/ops/ascendc/apis/synthetic_api.md", ROOT / "knowledge/ops/ascendc/apis/synthetic_api.md")],
            links,
        )

    def test_markdown_targets_ignore_inline_and_fenced_code(self) -> None:
        text = """[real](target.md) and `[interval, end)`.

```cpp
auto fn = [](int value) { return value; };
[fake](inside_fence.md)
```
"""
        self.assertEqual([("target.md", False)], markdown_targets(text))

    def test_missing_index_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            (root / "knowledge/ops").mkdir(parents=True)
            (root / "knowledge/index.md").write_text("# Knowledge\n", encoding="utf-8")
            issues = Contract(root).validate_index_tree()
            self.assertIn("index.missing", {issue.code for _, issue in issues})

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

    def test_target_contract_is_compared_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "knowledge").mkdir()
            (root / "governance/contracts").mkdir(parents=True)
            marker = root / "import-executed"
            (root / "governance/contracts/knowledge.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
                encoding="utf-8",
            )
            body = root / "body.md"
            body.write_text("# Candidate\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(INGEST),
                    "--knowledge-root",
                    str(root),
                    "create",
                    "--path",
                    "knowledge/common/glossaries/probe.md",
                    "--title",
                    "Probe",
                    "--description",
                    "Probe",
                    "--tag",
                    "task.lookup",
                    "--tag",
                    "topic.terminology",
                    "--body-file",
                    str(body),
                    "--dry-run",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            executed = marker.exists()
        self.assertEqual(2, result.returncode)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(executed)

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
            f"https://bitbucket.org/example/project/src/{commit}/README.md",
            f"https://codeberg.org/example/project/src/commit/{commit}/README.md",
        )
        for url in urls:
            with self.subTest(url=url):
                result = self.run_ingest(["--status", "stable", "--source", url])
                self.assertEqual(result.returncode, 0, result.stderr)


class LintBehaviorTests(unittest.TestCase):
    def make_root(self, temporary: str) -> Path:
        root = Path(temporary)
        shutil.copytree(ROOT / "governance", root / "governance")
        (root / "knowledge").mkdir()
        return root

    def render_card(
        self,
        *,
        sources: str = "  - resource: https://example.com/source\n    role: primary",
        body: str = "Probe body.",
        created_at: str = "2026-08-22T00:00:00Z",
        title_lines: str = "title: Synthetic API",
    ) -> str:
        return f'''---
type: API
{title_lines}
description: Deterministic lint probe.
tags: [task.lookup, topic.compilation]
status: stable
sources:
{sources}
created_at: "{created_at}"
updated_at: "2026-08-22T00:00:00Z"
platforms: [a2]
---

# Synthetic API

{body}
'''

    def run_lint(
        self,
        root: Path,
        text: str,
        *flags: str,
    ) -> subprocess.CompletedProcess[str]:
        card = root / "knowledge/ops/ascendc/apis/synthetic.md"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(text, encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(LINT),
                "--knowledge-root",
                str(root),
                "--card",
                "knowledge/ops/ascendc/apis/synthetic.md",
                *flags,
            ],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_invalid_calendar_time_is_a_card_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(created_at="2026-02-30T00:00:00Z"),
                "--json",
            )
        self.assertEqual(1, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn(
            "frontmatter.time",
            {finding["code"] for finding in payload["findings"]},
        )

    def test_index_entry_without_summary_is_a_nonblocking_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "knowledge/common").mkdir()
            (root / "knowledge/common/index.md").write_text(
                "# Common\n", encoding="utf-8"
            )
            (root / "knowledge/example.md").write_text(
                "# Example\n", encoding="utf-8"
            )
            (root / "knowledge/index.md").write_text(
                '---\nokf_version: "0.2"\n---\n\n# Knowledge\n\n'
                "- [Common](common/index.md)\n\n"
                "- [External](https://example.com)\n\n"
                "```markdown\n- [Example](example.md)\n```\n\n"
                "    - [Indented](example.md)\n\n"
                "- [Inline summary](example.md)：`DataCopy`\n\n"
                "```markdown\n- [Unclosed](example.md)\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINT),
                    "--knowledge-root",
                    str(root),
                    "--card",
                    "knowledge/index.md",
                    "--json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [
                {
                    "check": "index_entry_description",
                    "tier": "P1",
                    "path": "knowledge/index.md",
                    "line": 7,
                    "code": "index.entry_description",
                    "message": "index entry requires a summary",
                    "details": "- [Common](common/index.md)",
                }
            ],
            payload["findings"],
        )

    def test_duplicate_frontmatter_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(title_lines="title: First\ntitle: Second"),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("frontmatter.parse", result.stdout)
        self.assertIn("duplicate key", result.stdout)

    def test_reference_links_are_checked_but_images_are_allowed(self) -> None:
        body = """[Missing document][missing-doc]

![Missing diagram][missing-image]

<img src="also-missing.png" alt="missing">

[missing-doc]: missing.md
[missing-image]: missing.png"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(root, self.render_card(body=body))
        self.assertEqual(1, result.returncode)
        self.assertNotIn("body.embedded_image", result.stdout)
        self.assertIn("link.missing", result.stdout)

    def test_embedded_images_are_allowed(self) -> None:
        body = """![Missing diagram](missing-image.png)

<img src="also-missing.png" alt="missing">"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(root, self.render_card(body=body))
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertNotIn("body.embedded_image", result.stdout)

    def test_links_ignore_code_and_images_and_report_locations(self) -> None:
        body = """[Inline](missing-inline.md)
`[Inline code](missing-code.md)`
![Image](missing-image.md)
```markdown
[Fenced](missing-fenced.md)
```
[Reference][missing-reference]
[missing-reference]: missing-reference.md
[Outside](../../../../README.md)
[Directory](directory_target)"""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "README.md").write_text("# Outside\n", encoding="utf-8")
            (root / "knowledge/ops/ascendc/apis/directory_target").mkdir(
                parents=True
            )
            result = self.run_lint(root, self.render_card(body=body), "--json")
        self.assertEqual(1, result.returncode, result.stderr)
        findings = [
            finding
            for finding in json.loads(result.stdout)["findings"]
            if finding["check"] == "links"
        ]
        self.assertEqual(
            [
                ("link.missing", 17, "missing-inline.md"),
                ("link.missing", 23, "missing-reference.md"),
                ("link.outside_bundle", 25, "../../../../README.md"),
                ("link.not_file", 26, "directory_target"),
            ],
            [
                (finding["code"], finding["line"], finding["details"])
                for finding in findings
            ],
        )

    def test_index_empty_requires_a_valid_direct_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            common = root / "knowledge/common"
            glossaries = common / "glossaries"
            invalid_child = glossaries / "nested"
            invalid_child.mkdir(parents=True)
            (common / "index.md").write_text("# Common\n", encoding="utf-8")
            (glossaries / "index.md").write_text(
                "# Glossaries\n",
                encoding="utf-8",
            )
            (glossaries / "README.txt").write_text("junk\n", encoding="utf-8")
            (glossaries / "Bad-Name.md").write_text("# Invalid\n", encoding="utf-8")
            (invalid_child / "index.md").write_text(
                "# Invalid child\n",
                encoding="utf-8",
            )
            contract = Contract(root)

            empty_paths = {
                path.resolve().relative_to(root.resolve()).as_posix()
                for path, issue in contract.validate_index_tree()
                if issue.code == "index.empty"
            }
            self.assertIn("knowledge/common/glossaries", empty_paths)
            self.assertNotIn("knowledge/common", empty_paths)

            (glossaries / "valid_card.md").write_text(
                "# Valid path\n",
                encoding="utf-8",
            )
            populated_paths = {
                path.resolve().relative_to(root.resolve()).as_posix()
                for path, issue in contract.validate_index_tree()
                if issue.code == "index.empty"
            }
        self.assertNotIn("knowledge/common/glossaries", populated_paths)

    def test_local_link_cannot_leave_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "README.md").write_text("# Outside\n", encoding="utf-8")
            result = self.run_lint(
                root,
                self.render_card(body="[Outside](../../../../README.md)"),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("link.outside_bundle", result.stdout)

    def test_local_link_must_target_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            directory = root / "knowledge/ops/ascendc/apis/directory_target"
            directory.mkdir(parents=True)
            result = self.run_lint(
                root,
                self.render_card(body="[Directory](directory_target)"),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("link.not_file", result.stdout)

    def test_strict_navigation_requires_same_repository(self) -> None:
        commit = "54beb3b1f2f32067ac026202546011cd1b03977f"
        tree = f"https://gitcode.com/cann/repo-a/tree/{commit}/src/"
        unrelated = f"https://github.com/unrelated/repo-b/blob/{commit}/README.md"
        same_repo = f"https://gitcode.com/cann/repo-a/blob/{commit}/src/file.cpp"
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            rejected = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        f"  - resource: {tree}\n"
                        "    role: primary\n"
                        f"  - resource: {unrelated}\n"
                        "    role: supporting"
                    )
                ),
                "--strict-navigation",
            )
            accepted = self.run_lint(
                root,
                self.render_card(
                    sources=f"  - resource: {tree}\n    role: primary",
                    body=f"[Exact implementation]({same_repo})",
                ),
                "--strict-navigation",
            )
        self.assertEqual(1, rejected.returncode)
        self.assertIn("source.navigation", rejected.stdout)
        self.assertEqual(0, accepted.returncode, accepted.stdout)

    def test_existing_local_source_root_checks_marker_and_file(self) -> None:
        source_yaml = "  - resource: cann-docs-raw/source.md\n    role: primary"
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            absent = self.run_lint(root, self.render_card(sources=source_yaml))
        self.assertEqual(0, absent.returncode, absent.stdout)

        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            source_root = root / "cann-docs-raw"
            source_root.mkdir()
            archive_sha256 = Contract(root).local_sources["cann_docs_raw"]["archive_sha256"]
            (source_root / ".complete").write_text(
                f"archive_sha256={archive_sha256}\n",
                encoding="utf-8",
            )
            (source_root / "source.md").write_text("# Source\n", encoding="utf-8")
            valid = self.run_lint(root, self.render_card(sources=source_yaml))
        self.assertEqual(0, valid.returncode, valid.stdout)

        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            source_root = root / "cann-docs-raw"
            source_root.mkdir()
            (source_root / ".complete").write_text(
                "archive_sha256=wrong\n",
                encoding="utf-8",
            )
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: cann-docs-raw/missing.md\n"
                        "    role: primary"
                    )
                ),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("source.archive_marker", result.stdout)
        self.assertIn("source.local_missing", result.stdout)

    def test_full_lint_requires_an_executable_local_source_fetch_script(self) -> None:
        module = load_lint_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            missing = module.Linter(root, False)
            missing.validate_full_tree()
            missing_codes = {finding["code"] for finding in missing.findings}

            fetch_script = root / "fetch-cann-docs.sh"
            fetch_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            fetch_script.chmod(0o644)
            non_executable = module.Linter(root, False)
            non_executable.validate_full_tree()
            mode_codes = {
                finding["code"] for finding in non_executable.findings
            }
        self.assertIn("source.fetch_script_missing", missing_codes)
        self.assertIn("source.fetch_script_mode", mode_codes)

    def test_log_entries_require_summary_and_details(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / "logs").mkdir()
            (root / "logs/2026-08-22.md").write_text(
                "# 2026-08-22\n\n## [08:00] governance | Missing sections\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(LINT), "--knowledge-root", str(root)],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("log.sections", result.stdout)

    def test_target_contract_is_compared_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "knowledge").mkdir()
            (root / "governance/schemas").mkdir(parents=True)
            (root / "governance/contracts").mkdir(parents=True)
            (root / "governance/schemas/registries.yaml").write_text("{}\n", encoding="utf-8")
            marker = root / "import-executed"
            (root / "governance/contracts/knowledge.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(LINT), "--knowledge-root", str(root), "--sample", "1"],
                check=False,
                text=True,
                capture_output=True,
            )
            executed = marker.exists()
        self.assertEqual(2, result.returncode)
        self.assertIn("does not match", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(executed)

    def test_invalid_schema_returns_operational_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            schema_path = root / "governance/schemas/frontmatter.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["type"] = "invalid-json-schema-type"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LINT), "--knowledge-root", str(root), "--sample", "1"],
                check=False,
                text=True,
                capture_output=True,
            )
        self.assertEqual(2, result.returncode)
        self.assertNotIn("Traceback", result.stderr)

    def test_bitbucket_branch_source_is_not_considered_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            result = self.run_lint(
                root,
                self.render_card(
                    sources=(
                        "  - resource: https://bitbucket.org/example/project/src/main/README.md\n"
                        "    role: primary"
                    )
                ),
            )
        self.assertEqual(1, result.returncode)
        self.assertIn("source.pin", result.stdout)


class MigratedSkillContractTests(unittest.TestCase):
    def test_lint_rejects_truncated_description_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "governance", root / "governance")
            card = root / "knowledge/ops/ascendc/apis/synthetic.md"
            card.parent.mkdir(parents=True)
            metadata = dict(SYNTHETIC_API_METADATA)
            metadata["description"] = "表1 An incomplete summary..."
            card.write_text(
                "---\n"
                + "\n".join(
                    [
                        f"type: {metadata['type']}",
                        f"title: {metadata['title']}",
                        f"description: {metadata['description']}",
                        "tags: [task.lookup, topic.compilation]",
                        "status: stable",
                        "sources:",
                        "  - resource: https://example.com/cann/synthetic-api",
                        'created_at: "2026-08-18T00:00:00Z"',
                        'updated_at: "2026-08-18T00:00:00Z"',
                        "platforms: [a2]",
                    ]
                )
                + "\n---\n\n# Synthetic\n\nThis field was cut...；next field.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(LINT),
                    "--knowledge-root",
                    str(root),
                    "--card",
                    "knowledge/ops/ascendc/apis/synthetic.md",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("body.truncated", result.stdout)
            self.assertIn("frontmatter.truncated", result.stdout)
            self.assertIn("frontmatter.description_placeholder", result.stdout)

    def test_query_receipt_is_versioned_and_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            shutil.copytree(ROOT / "governance", root / "governance")
            (root / "knowledge").mkdir(parents=True)
            built = subprocess.run(
                [sys.executable, str(INDEX), "--knowledge-root", str(root), "build"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, built.returncode, built.stderr)
            receipt = work / "search.json"
            command = [
                sys.executable,
                str(QUERY),
                "--knowledge-root",
                str(root),
                "search",
                "--query",
                "definitely_absent_cannbot_probe_9f6a",
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
            self.assertEqual(payload["schema_version"], "cannbot-knowledge-search.v3")
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
