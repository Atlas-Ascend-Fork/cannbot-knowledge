from __future__ import annotations

import json
import importlib.util
import re
import sys
import unittest
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from urllib.parse import unquote

import yaml


LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
TAG_RE = re.compile(r"\b(?:task|topic|paradigm)\.[a-z][a-z0-9_]*\b")


class DocumentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.registries = yaml.safe_load(
            (cls.root / "governance/schemas/registries.yaml").read_text(encoding="utf-8")
        )

    def documentation_files(self) -> list[Path]:
        roots = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            self.root / "AGENTS.md",
            self.root / "CLAUDE.md",
            self.root / "governance/specs",
            self.root / ".agents/skills",
            self.root / "knowledge",
            self.root / "logs",
        ]
        result: list[Path] = []
        for path in roots:
            if path.is_file():
                result.append(path)
            else:
                result.extend(path.rglob("*.md"))
        return sorted(result)

    def external_documentation_files(self) -> list[Path]:
        roots = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            self.root / "AGENTS.md",
            self.root / "CLAUDE.md",
            self.root / "governance/specs",
            self.root / "logs",
        ]
        result: list[Path] = []
        for path in roots:
            if path.is_file():
                result.append(path)
            else:
                result.extend(path.rglob("*.md"))
        return sorted(result)

    def test_local_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for document in self.documentation_files():
            text = document.read_text(encoding="utf-8")
            for match in LINK_RE.finditer(text):
                raw = match.group(1).strip()
                target = raw[1 : raw.index(">")] if raw.startswith("<") and ">" in raw else raw.split()[0]
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                relative = unquote(target.split("#", 1)[0])
                resolved = (document.parent / relative).resolve()
                if not resolved.exists():
                    line = text.count("\n", 0, match.start()) + 1
                    failures.append(f"{document.relative_to(self.root)}:{line}: {target}")
        self.assertEqual([], failures)

    def test_readme_links_every_governance_spec(self) -> None:
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        missing = [
            spec.name
            for spec in sorted((self.root / "governance/specs").glob("*.md"))
            if f"governance/specs/{spec.name}" not in readme
        ]
        self.assertEqual([], missing)

    def test_governance_specs_keep_five_focused_entries(self) -> None:
        expected = {"okf.md", "paths.md", "frontmatter.md", "schemas.md", "skills.md"}
        actual = {path.name for path in (self.root / "governance/specs").glob("*.md")}
        self.assertEqual(expected, actual)

    def test_okf_reference_is_pinned_and_scoped(self) -> None:
        commit = "fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f"
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        spec = (self.root / "governance/specs/okf.md").read_text(encoding="utf-8")
        reference = (
            "https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/"
            f"{commit}/okf/SPEC.md"
        )
        self.assertIn(reference, readme)
        self.assertIn(reference, spec)
        self.assertIn("符合 OKF v0.2", readme)
        self.assertIn("Open Knowledge Format", spec)
        self.assertIn("`knowledge/` 是本仓唯一的 OKF Knowledge Bundle", spec)

    def test_okf_terms_distinguish_concept_type_and_profiles(self) -> None:
        spec = (self.root / "governance/specs/okf.md").read_text(encoding="utf-8")
        for term in ("OKF Concept", "OKF `type`", "路径 Profile", "CANNBot Profile", "安装模式"):
            with self.subTest(term=term):
                self.assertIn(term, spec)
        self.assertIn("`type: API` 的卡片仍然是一个 OKF Concept", spec)

    def test_verified_is_not_a_stable_requirement(self) -> None:
        profiles = yaml.safe_load(
            (self.root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
        )
        self.assertTrue(
            all("verified" not in profile.get("required", []) for profile in profiles["profiles"].values())
        )
        frontmatter = (self.root / "governance/specs/frontmatter.md").read_text(encoding="utf-8")
        self.assertIn("`status` 和 trust tier 相互独立", frontmatter)

    def test_installation_mode_is_not_called_a_knowledge_profile(self) -> None:
        documents = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            *sorted((self.root / "governance/specs").glob("*.md")),
        ]
        failures = [path.relative_to(self.root).as_posix() for path in documents if "安装 Profile" in path.read_text(encoding="utf-8")]
        self.assertEqual([], failures)

    def test_knowledge_cards_use_okf_core_fields(self) -> None:
        root_index = (self.root / "knowledge/index.md").read_text(encoding="utf-8")
        root_metadata = yaml.safe_load(root_index.split("---", 2)[1])
        self.assertEqual({"okf_version": "0.2"}, root_metadata)

        failures: list[str] = []
        for card in sorted((self.root / "knowledge").rglob("*.md")):
            if card.name == "index.md":
                continue
            metadata = yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1])
            if not str(metadata.get("type", "")).strip():
                failures.append(f"{card.relative_to(self.root)}: missing type")
            if metadata.get("status") not in {"draft", "stable", "deprecated"}:
                failures.append(f"{card.relative_to(self.root)}: invalid status")
            for source in metadata.get("sources", []):
                if "resource" not in source or "url" in source:
                    failures.append(f"{card.relative_to(self.root)}: invalid source shape")
        self.assertEqual([], failures)

    def test_knowledge_index_entries_have_descriptions(self) -> None:
        failures: list[str] = []
        for index in sorted((self.root / "knowledge").rglob("index.md")):
            for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), start=1):
                if line.startswith("- [") and ")：" not in line:
                    failures.append(f"{index.relative_to(self.root)}:{number}")
        self.assertEqual([], failures)

    def test_each_skill_links_its_references(self) -> None:
        failures: list[str] = []
        for skill in sorted((self.root / ".agents/skills").iterdir()):
            if not skill.is_dir():
                continue
            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
            references = skill / "references"
            if not references.exists():
                continue
            for reference in sorted(references.glob("*.md")):
                target = f"references/{reference.name}"
                if target not in skill_text:
                    failures.append(f"{skill.name}: {target}")
        self.assertEqual([], failures)

    def test_skill_sources_do_not_contain_agent_vendor_metadata(self) -> None:
        vendor_metadata = sorted(
            path.relative_to(self.root).as_posix()
            for path in (self.root / ".agents/skills").glob("*/agents/*")
            if path.is_file()
        )
        self.assertEqual([], vendor_metadata)

    def test_markdown_structure(self) -> None:
        failures: list[str] = []
        for document in self.documentation_files():
            lines = document.read_text(encoding="utf-8").splitlines()
            content_start = 0
            if lines and lines[0] == "---":
                try:
                    content_start = lines.index("---", 1) + 1
                except ValueError:
                    failures.append(f"{document.relative_to(self.root)}: unterminated frontmatter")
                    continue
            first = next((line for line in lines[content_start:] if line.strip()), "")
            if not first.startswith("# "):
                failures.append(f"{document.relative_to(self.root)}: first content heading is not H1")
            if sum(line.startswith("```") for line in lines) % 2:
                failures.append(f"{document.relative_to(self.root)}: unbalanced fenced code blocks")
            if any(line != line.rstrip() for line in lines):
                failures.append(f"{document.relative_to(self.root)}: trailing whitespace")
        self.assertEqual([], failures)

    def test_external_docs_do_not_expose_skill_script_cli(self) -> None:
        forbidden = (
            "knowledge_query.py",
            "knowledge_ingest.py",
            "knowledge_lint.py",
            "build_graph.py",
            "quick_validate.py",
        )
        failures: list[str] = []
        for document in self.external_documentation_files():
            text = document.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    failures.append(f"{document.relative_to(self.root)}: {token}")
        self.assertEqual([], failures)

    def test_repository_docs_do_not_describe_an_import_origin(self) -> None:
        forbidden = ("NPU-Kernel-Wiki", "NPU Kernel Wiki", "迁移 pilot", "首批迁移", "旧仓")
        failures: list[str] = []
        for document in self.external_documentation_files():
            text = document.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    failures.append(f"{document.relative_to(self.root)}: {token}")
        self.assertEqual([], failures)

    def test_documented_tags_are_registered(self) -> None:
        registered = set(self.registries["tags"])
        locations = [
            self.root / "CONTRIBUTING.md",
            self.root / "governance/specs/frontmatter.md",
            self.root / ".agents/skills/knowledge-ingest/SKILL.md",
            self.root / ".agents/skills/knowledge-query/SKILL.md",
            self.root / ".agents/skills/knowledge-lint/SKILL.md",
        ]
        documented = set()
        for path in locations:
            documented.update(TAG_RE.findall(path.read_text(encoding="utf-8")))
        self.assertEqual(set(), documented - registered)

    def test_frontmatter_spec_lists_every_source_role(self) -> None:
        schema = json.loads(
            (self.root / "governance/schemas/frontmatter.schema.json").read_text(encoding="utf-8")
        )
        roles = schema["properties"]["sources"]["items"]["properties"]["role"]["enum"]
        spec = (self.root / "governance/specs/frontmatter.md").read_text(encoding="utf-8")
        self.assertEqual([], [role for role in roles if f"`{role}`" not in spec])

    def test_authoritative_frontmatter_docs_cover_profiles(self) -> None:
        profiles = yaml.safe_load(
            (self.root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
        )
        documents = [
            self.root / "governance/specs/frontmatter.md",
            self.root / ".agents/skills/knowledge-ingest/references/frontmatter-profiles.md",
        ]
        for document in documents:
            text = document.read_text(encoding="utf-8")
            with self.subTest(document=document.name):
                for field in profiles["common_required"]:
                    self.assertIn(f"`{field}`", text)
                for profile in profiles["profiles"]:
                    self.assertTrue(
                        f"`{profile}`" in text or f"`{profile}/`" in text,
                        f"{document} does not document profile {profile}",
                    )

    def test_frontmatter_spec_covers_schema_fields_and_enums(self) -> None:
        schema = json.loads(
            (self.root / "governance/schemas/frontmatter.schema.json").read_text(encoding="utf-8")
        )
        spec = (self.root / "governance/specs/frontmatter.md").read_text(encoding="utf-8")
        missing_fields = [field for field in schema["properties"] if f"`{field}`" not in spec]
        self.assertEqual([], missing_fields)
        for field in ("status",):
            with self.subTest(field=field):
                self.assertEqual(
                    [],
                    [value for value in schema["properties"][field]["enum"] if f"`{value}`" not in spec],
                )

    def test_schema_spec_covers_path_contract_identifiers(self) -> None:
        path_spec = (self.root / "governance/specs/paths.md").read_text(encoding="utf-8")
        schema_spec = (self.root / "governance/specs/schemas.md").read_text(encoding="utf-8")
        profiles = yaml.safe_load(
            (self.root / "governance/schemas/profiles.yaml").read_text(encoding="utf-8")
        )
        for section in ("domains", "technologies", "scopes"):
            with self.subTest(section=section):
                self.assertIn(f"`{section}`", schema_spec)
                self.assertEqual(
                    [],
                    [item for item in self.registries[section] if f"`{item}`" not in path_spec],
                )
        self.assertEqual(
            [],
            [profile for profile in profiles["profiles"] if f"`{profile}" not in path_spec],
        )
        for values in self.registries["paths"].values():
            self.assertEqual([], [value for value in values if f"`{value}`" not in path_spec])

    @staticmethod
    def load_module(path: Path, name: str):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def parser_options(parser: ArgumentParser) -> set[str]:
        result: set[str] = set()
        for action in parser._actions:
            result.update(option for option in action.option_strings if option.startswith("--"))
            if isinstance(action, _SubParsersAction):
                for child in action.choices.values():
                    result.update(DocumentationContractTests.parser_options(child))
        return result

    def test_skill_docs_only_use_supported_cli_flags(self) -> None:
        cases = (
            (
                "ingest",
                (
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/knowledge_ingest.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-ingest/scripts/reference_inventory.py",
                        "parser",
                    ),
                ),
                self.root / ".agents/skills/knowledge-ingest",
            ),
            (
                "query",
                (
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
                        "build_parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/knowledge_index.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/retrieval_state.py",
                        "parser",
                    ),
                    (
                        self.root / ".agents/skills/knowledge-query/scripts/retrieval_outcome.py",
                        "parser",
                    ),
                ),
                self.root / ".agents/skills/knowledge-query",
            ),
            (
                "lint",
                (
                    (
                        self.root / ".agents/skills/knowledge-lint/scripts/knowledge_lint.py",
                        "build_parser",
                    ),
                ),
                self.root / ".agents/skills/knowledge-lint",
            ),
        )
        for name, parsers, docs_root in cases:
            supported: set[str] = set()
            for index, (script, parser_factory) in enumerate(parsers):
                module = self.load_module(script, f"documentation_{name}_{index}")
                supported.update(self.parser_options(getattr(module, parser_factory)()))
            documented: set[str] = set()
            for document in docs_root.rglob("*.md"):
                documented.update(re.findall(r"--[a-z][a-z0-9-]*", document.read_text(encoding="utf-8")))
            with self.subTest(skill=name):
                self.assertEqual(set(), documented - supported)

    def test_query_derives_trust_tier_from_okf_verified_events(self) -> None:
        module = self.load_module(
            self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
            "documentation_query_trust",
        )
        self.assertEqual("unverified", module.trust_tier({}))
        self.assertEqual(
            "machine-confirmed",
            module.trust_tier({"verified": {"by": "process:ci", "at": "2026-08-15T08:00:00Z"}}),
        )
        self.assertEqual(
            "human-reviewed",
            module.trust_tier(
                {
                    "verified": [
                        {"by": "process:ci", "at": "2026-08-15T08:00:00Z"},
                        {"by": "human:reviewer", "at": "2026-08-15T09:00:00Z"},
                    ]
                }
            ),
        )

    def test_agent_instruction_files_match(self) -> None:
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(agents, claude)


if __name__ == "__main__":
    unittest.main()
