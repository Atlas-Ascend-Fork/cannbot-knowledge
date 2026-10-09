# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"
QUERY_RELATIVE = Path(".agents/skills/knowledge-query/scripts/knowledge_query.py")


class InstallerTests(unittest.TestCase):
    def create_repository_fixture(self, root: Path) -> None:
        root.mkdir()
        shutil.copy2(INSTALLER, root / "install.sh")
        (root / "knowledge").mkdir()
        (root / "knowledge/index.md").write_text("# Fixture\n", encoding="utf-8")
        (root / "requirements.txt").write_text("\n", encoding="utf-8")
        registry = root / "governance/schemas/registries.yaml"
        registry.parent.mkdir(parents=True)
        registry.write_text("{}\n", encoding="utf-8")
        query = root / ".agents/skills/knowledge-query"
        (query / "scripts").mkdir(parents=True)
        (query / "SKILL.md").write_text("fixture\n", encoding="utf-8")
        (query / "scripts/knowledge_index.py").write_text(
            "raise SystemExit(0)\n", encoding="utf-8"
        )
        api = root / ".agents/skills/ascendc-api-knowledge-query"
        api.mkdir()
        (api / "SKILL.md").write_text("fixture\n", encoding="utf-8")
        (root / "get_resources.sh").write_text(
            "#!/usr/bin/env bash\necho 'resource fixture restored'\n", encoding="utf-8"
        )

    def test_destination_parent_symlinks_cannot_leave_project(self) -> None:
        for directory in (".cannbot", ".agents", ".claude"):
            with self.subTest(directory=directory), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary) / "project"
                outside = Path(temporary) / "outside"
                project.mkdir()
                outside.mkdir()
                (project / directory).symlink_to(outside, target_is_directory=True)
                result = self.run_installer(project, "claude")
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("destination parent leaves project", result.stderr)
                self.assertEqual([], list(outside.iterdir()))
                self.assertEqual([directory], [path.name for path in project.iterdir()])

    def test_destination_parent_file_fails_before_any_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".cannbot").write_text("user content\n", encoding="utf-8")
            result = self.run_installer(project, "claude")
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("not a directory", result.stderr)
            self.assertEqual([".cannbot"], [path.name for path in project.iterdir()])
            self.assertEqual("user content\n", (project / ".cannbot").read_text())

    def test_prompt_replacement_preserves_existing_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            prompt = project / "AGENTS.md"
            prompt.write_text("user rules\n", encoding="utf-8")
            prompt.chmod(0o640)
            result = self.run_installer(project, "codex")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(0o640, prompt.stat().st_mode & 0o777)
            self.assertTrue(prompt.read_text().startswith("user rules\n"))

    def test_default_resource_preparation_precedes_project_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            self.create_repository_fixture(root)
            project = Path(temporary) / "project"
            project.mkdir()
            command = ["bash", str(root / "install.sh"), "codex", str(project)]
            resource_script = root / "get_resources.sh"
            resource_script.write_text("#!/usr/bin/env bash\necho 'resource fixture failed' >&2\nexit 9\n", encoding="utf-8")
            failed = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertEqual(9, failed.returncode)
            self.assertIn("resource fixture failed", failed.stderr)
            self.assertEqual([], list(project.iterdir()))
            resource_script.write_text("#!/usr/bin/env bash\necho 'resource fixture restored'\n", encoding="utf-8")
            succeeded = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertEqual(0, succeeded.returncode, succeeded.stderr)
            self.assertIn("resource fixture restored", succeeded.stdout)
            self.assertTrue((project / ".agents/skills/knowledge-query").is_symlink())

    def test_standalone_installer_clones_and_fast_forwards_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            self.create_repository_fixture(source)
            subprocess.run(
                ["git", "init"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "checkout", "-b", "main"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "fixture@example.com"],
                cwd=source,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Fixture"], cwd=source, check=True
            )
            subprocess.run(["git", "add", "--force", "."], cwd=source, check=True)
            subprocess.run(
                ["git", "commit", "-m", "fixture"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )

            managed = base / "managed"
            project = base / "project"
            project.mkdir()
            command = [
                "bash",
                "-s",
                "--",
                "codex",
                str(project),
                "consumer",
                "--knowledge-root",
                str(managed),
                "--repository-url",
                str(source),
                "--repository-ref",
                "main",
                "--skip-resources",
            ]
            installer_source = INSTALLER.read_text(encoding="utf-8")
            installed = subprocess.run(
                command,
                input=installer_source,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertIn("Cloning cannbot-knowledge", installed.stdout)
            self.assertEqual(
                managed / ".agents/skills/knowledge-query",
                (project / ".agents/skills/knowledge-query").resolve(),
            )
            env = (project / ".cannbot/knowledge.env").read_text(encoding="utf-8")
            self.assertIn(f"export CANNBOT_KNOWLEDGE_ROOT={managed}", env)

            marker = source / "updated.txt"
            marker.write_text("updated\n", encoding="utf-8")
            subprocess.run(["git", "add", "updated.txt"], cwd=source, check=True)
            subprocess.run(
                ["git", "commit", "-m", "update fixture"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )
            updated = subprocess.run(
                command,
                input=installer_source,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, updated.returncode, updated.stderr)
            self.assertIn("Updating cannbot-knowledge", updated.stdout)
            self.assertEqual("updated\n", (managed / "updated.txt").read_text(encoding="utf-8"))

    def run_installer(self, project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(INSTALLER), *arguments[:1], str(project), *arguments[1:], "--skip-resources"],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_contributor_install_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = subprocess.run(
                ["bash", str(INSTALLER), "codex", str(project), "contributor", "--skip-resources"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = {path.name for path in (project / ".agents/skills").iterdir() if path.is_symlink()}
            self.assertEqual(
                installed,
                {
                    "knowledge-ingest",
                    "knowledge-query",
                    "ascendc-api-knowledge-query",
                    "knowledge-lint",
                    "ops-knowledge-vv-ingest",
                    "ops-knowledge-cv-ingest",
                },
            )
            help_result = subprocess.run(
                ["bash", str(INSTALLER), "--help"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, help_result.returncode, help_result.stderr)
            self.assertIn("repository-internal trace ingest skill is not installed", help_result.stdout)
            env = (project / ".cannbot/knowledge.env").read_text(encoding="utf-8")
            self.assertIn(f"export CANNBOT_KNOWLEDGE_ROOT={ROOT}", env)
            self.assertIn("export CANNBOT_KNOWLEDGE_PROFILE=contributor", env)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- cannbot-knowledge:start -->", prompt)
            self.assertIn("ascend_910_95.md", prompt)
            self.assertIn(str(ROOT / "knowledge/common/platforms/concepts/ascend_910_95.md"), prompt)
            self.assertNotIn("$CANNBOT_KNOWLEDGE_ROOT/knowledge", prompt)
            self.assertIn("knowledge-ingest", prompt)
            self.assertIn("ops-knowledge-vv-ingest", prompt)
            self.assertIn("ops-knowledge-cv-ingest", prompt)
            self.assertIn("### 贡献者附加流程", prompt)

    def test_platform_option_is_persisted_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = self.run_installer(
                project, "codex", "consumer", "--platform", "a2"
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            knowledge_env = project / ".cannbot/knowledge.env"
            self.assertIn(
                "export CANNBOT_KNOWLEDGE_PLATFORM=a2",
                knowledge_env.read_text(encoding="utf-8"),
            )
            reinstalled = self.run_installer(project, "codex", "consumer")
            self.assertEqual(0, reinstalled.returncode, reinstalled.stderr)
            self.assertIn(
                "export CANNBOT_KNOWLEDGE_PLATFORM=a2",
                knowledge_env.read_text(encoding="utf-8"),
            )

    def test_invalid_platform_does_not_modify_existing_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = self.run_installer(
                project, "codex", "consumer", "--platform", "a2"
            )
            self.assertEqual(0, installed.returncode, installed.stderr)

            def snapshot() -> dict[str, tuple[str, bytes | str]]:
                entries: dict[str, tuple[str, bytes | str]] = {}
                for path in sorted(project.rglob("*")):
                    relative = str(path.relative_to(project))
                    if path.is_symlink():
                        entries[relative] = ("symlink", os.readlink(path))
                    elif path.is_file():
                        entries[relative] = ("file", path.read_bytes())
                return entries

            before = snapshot()
            rejected = self.run_installer(
                project, "codex", "consumer", "--platform", "a2_typo"
            )
            self.assertEqual(2, rejected.returncode)
            self.assertIn("unknown platform: a2_typo", rejected.stderr)
            self.assertEqual(before, snapshot())

            empty = self.run_installer(project, "codex", "consumer", "--platform=")
            self.assertEqual(2, empty.returncode)
            self.assertIn("--platform requires a non-empty value", empty.stderr)
            self.assertEqual(before, snapshot())

    def test_consumer_prompt_routes_to_installed_skill_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_installer(project, "codex", "consumer")
            self.assertEqual(result.returncode, 0, result.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            routes = re.findall(r"`(\.agents/skills/[^`]+/SKILL\.md)`", prompt)
            self.assertEqual(2, len(routes))
            self.assertEqual(
                {"knowledge-query", "ascendc-api-knowledge-query"},
                {Path(route).parent.name for route in routes},
            )
            for route in routes:
                with self.subTest(route=route):
                    installed_source = project / route
                    self.assertTrue(installed_source.is_file())
                    self.assertEqual((ROOT / route).resolve(), installed_source.resolve())
            self.assertEqual(
                {"knowledge-query", "ascendc-api-knowledge-query"},
                {path.name for path in (project / ".agents/skills").iterdir()},
            )

    def test_switching_to_consumer_removes_managed_contributor_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            for agent in ("claude", "opencode"):
                installed = self.run_installer(project, agent, "contributor")
                self.assertEqual(0, installed.returncode, installed.stderr)

            downgraded = self.run_installer(project, "codex", "consumer")
            self.assertEqual(0, downgraded.returncode, downgraded.stderr)
            expected = {"knowledge-query", "ascendc-api-knowledge-query"}
            self.assertEqual(expected, {path.name for path in (project / ".agents/skills").iterdir()})
            self.assertEqual(expected, {path.name for path in (project / ".claude/skills").iterdir()})
            self.assertEqual(expected, {path.name for path in (project / ".opencode/skills").iterdir()})
            env = (project / ".cannbot/knowledge.env").read_text(encoding="utf-8")
            self.assertIn("CANNBOT_KNOWLEDGE_PROFILE=consumer", env)
            for prompt_path in (project / "AGENTS.md", project / "CLAUDE.md"):
                prompt = prompt_path.read_text(encoding="utf-8")
                self.assertNotIn("### 贡献者附加流程", prompt)
                self.assertIn(str(ROOT / "knowledge"), prompt)

    def test_first_consumer_install_preserves_unmanaged_contributor_links(self) -> None:
        for canonical_kind in ("directory", "foreign-link"):
            with self.subTest(canonical_kind=canonical_kind), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                project = base / "project"
                project.mkdir()
                canonical = project / ".agents/skills/knowledge-ingest"
                canonical.parent.mkdir(parents=True)
                if canonical_kind == "directory":
                    canonical.mkdir()
                    user_content = canonical / "user-content.md"
                else:
                    foreign_skill = base / "foreign-knowledge-ingest"
                    foreign_skill.mkdir()
                    canonical.symlink_to(foreign_skill, target_is_directory=True)
                    user_content = foreign_skill / "user-content.md"
                user_content.write_text("preserve user Skill\n", encoding="utf-8")

                adapter = project / ".claude/skills/knowledge-ingest"
                adapter.parent.mkdir(parents=True)
                adapter.symlink_to(canonical, target_is_directory=True)
                adapter_target = os.readlink(adapter)
                canonical_target = os.readlink(canonical) if canonical.is_symlink() else None

                result = self.run_installer(project, "codex", "consumer")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("preserve user Skill\n", user_content.read_text(encoding="utf-8"))
                self.assertTrue(adapter.is_symlink())
                self.assertEqual(adapter_target, os.readlink(adapter))
                if canonical_kind == "directory":
                    self.assertTrue(canonical.is_dir())
                    self.assertFalse(canonical.is_symlink())
                else:
                    self.assertTrue(canonical.is_symlink())
                    self.assertEqual(canonical_target, os.readlink(canonical))

    def test_cleanup_preflight_failure_preserves_existing_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            project.mkdir()
            installed = self.run_installer(project, "codex", "contributor")
            self.assertEqual(0, installed.returncode, installed.stderr)

            canonical_root = project / ".agents/skills"
            original_links = {
                path.name: os.readlink(path)
                for path in canonical_root.iterdir()
                if path.is_symlink()
            }
            original_env = (project / ".cannbot/knowledge.env").read_bytes()
            original_prompt = (project / "AGENTS.md").read_bytes()

            outside = base / "outside"
            external_skills = outside / "skills"
            external_skills.mkdir(parents=True)
            external_adapter = external_skills / "knowledge-lint"
            external_adapter.symlink_to(
                canonical_root / "knowledge-lint", target_is_directory=True
            )
            opencode_root = project / ".opencode"
            opencode_root.symlink_to(outside, target_is_directory=True)
            adapter_target = os.readlink(external_adapter)

            failed = self.run_installer(project, "codex", "consumer")
            self.assertEqual(2, failed.returncode, failed.stderr)
            self.assertIn("destination parent leaves project", failed.stderr)
            self.assertEqual(
                original_links,
                {
                    path.name: os.readlink(path)
                    for path in canonical_root.iterdir()
                    if path.is_symlink()
                },
            )
            self.assertEqual(original_env, (project / ".cannbot/knowledge.env").read_bytes())
            self.assertEqual(original_prompt, (project / "AGENTS.md").read_bytes())
            self.assertTrue(opencode_root.is_symlink())
            self.assertTrue(external_adapter.is_symlink())
            self.assertEqual(adapter_target, os.readlink(external_adapter))

    def test_cross_client_downgrade_updates_crlf_managed_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = self.run_installer(project, "claude", "contributor")
            self.assertEqual(0, installed.returncode, installed.stderr)
            prompt = project / "CLAUDE.md"
            prompt.write_bytes(prompt.read_bytes().replace(b"\n", b"\r\n"))

            downgraded = self.run_installer(project, "codex", "consumer")
            self.assertEqual(0, downgraded.returncode, downgraded.stderr)
            prompt_text = prompt.read_text(encoding="utf-8")
            self.assertNotIn("贡献者附加流程", prompt_text)
            for skill in (
                "knowledge-ingest",
                "knowledge-lint",
                "ops-knowledge-vv-ingest",
                "ops-knowledge-cv-ingest",
            ):
                self.assertNotIn(skill, prompt_text)
                self.assertFalse((project / ".agents/skills" / skill).is_symlink())
                self.assertFalse((project / ".claude/skills" / skill).is_symlink())
            env = (project / ".cannbot/knowledge.env").read_text(encoding="utf-8")
            self.assertIn("CANNBOT_KNOWLEDGE_PROFILE=consumer", env)

    def test_conflict_does_not_leave_partial_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            conflict = project / ".agents/skills/knowledge-query"
            conflict.mkdir(parents=True)
            result = subprocess.run(
                ["bash", str(INSTALLER), "codex", str(project), "contributor"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse((project / ".agents/skills/knowledge-ingest").exists())
            self.assertFalse((project / ".agents/skills/knowledge-lint").exists())
            self.assertFalse((project / ".cannbot/knowledge.env").exists())
            self.assertFalse((project / "AGENTS.md").exists())

    def test_agent_adapters_point_to_canonical_skills(self) -> None:
        adapters = {
            "codex": (None, Path("AGENTS.md")),
            "claude": (Path(".claude/skills"), Path("CLAUDE.md")),
            "opencode": (Path(".opencode/skills"), Path("AGENTS.md")),
            "trae": (
                Path(".trae/skills"),
                Path(".trae/rules/cannbot-knowledge.md"),
            ),
            "cursor": (Path(".cursor/skills"), Path("AGENTS.md")),
            "copilot": (
                Path(".github/skills"),
                Path(".github/copilot-instructions.md"),
            ),
        }
        for agent, (adapter, prompt) in adapters.items():
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                result = self.run_installer(project, agent, "consumer")
                self.assertEqual(result.returncode, 0, result.stderr)
                prompt_path = project / prompt
                self.assertTrue(prompt_path.is_file())
                self.assertEqual(0o644, prompt_path.stat().st_mode & 0o777)
                if agent == "trae":
                    prompt_text = prompt_path.read_text(encoding="utf-8")
                    self.assertTrue(prompt_text.startswith("---\nalwaysApply: true\n---\n"))
                for skill in ("knowledge-query", "ascendc-api-knowledge-query"):
                    canonical = project / ".agents/skills" / skill
                    self.assertTrue(canonical.is_symlink())
                    self.assertEqual(canonical.resolve(), ROOT / ".agents/skills" / skill)
                    if adapter is not None:
                        agent_link = project / adapter / skill
                        self.assertTrue(agent_link.is_symlink())
                        self.assertEqual(agent_link.resolve(), canonical.resolve())
                uninstalled = self.run_installer(
                    project,
                    agent,
                    "consumer",
                    "--prompt-action",
                    "uninstall",
                )
                self.assertEqual(0, uninstalled.returncode, uninstalled.stderr)
                self.assertNotIn(
                    "<!-- cannbot-knowledge:start -->",
                    prompt_path.read_text(encoding="utf-8"),
                )
                reinstalled = self.run_installer(
                    project,
                    agent,
                    "consumer",
                    "--prompt-action",
                    "reinstall",
                )
                self.assertEqual(0, reinstalled.returncode, reinstalled.stderr)
                self.assertIn(
                    "<!-- cannbot-knowledge:start -->",
                    prompt_path.read_text(encoding="utf-8"),
                )

    def test_prompt_updates_preserve_existing_file_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            prompt = project / "AGENTS.md"
            prompt.write_text("# Existing\n", encoding="utf-8")
            prompt.chmod(0o640)
            installed = self.run_installer(project, "codex", "consumer")
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertEqual(0o640, prompt.stat().st_mode & 0o777)
            uninstalled = self.run_installer(
                project, "codex", "consumer", "--prompt-action", "uninstall"
            )
            self.assertEqual(0, uninstalled.returncode, uninstalled.stderr)
            self.assertEqual(0o640, prompt.stat().st_mode & 0o777)

    def test_project_env_updates_preserve_existing_file_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = self.run_installer(project, "codex", "contributor")
            self.assertEqual(0, installed.returncode, installed.stderr)
            knowledge_env = project / ".cannbot/knowledge.env"
            knowledge_env.chmod(0o640)
            updated = self.run_installer(project, "codex", "consumer")
            self.assertEqual(0, updated.returncode, updated.stderr)
            self.assertEqual(0o640, knowledge_env.stat().st_mode & 0o777)

    def test_existing_managed_repository_must_be_on_requested_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            self.create_repository_fixture(source)
            subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
            subprocess.run(["git", "checkout", "-b", "main"], cwd=source, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.com"], cwd=source, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=source, check=True)
            subprocess.run(["git", "add", "."], cwd=source, check=True)
            subprocess.run(["git", "commit", "-m", "fixture"], cwd=source, check=True, capture_output=True)
            managed = base / "managed"
            subprocess.run(["git", "clone", "--branch", "main", str(source), str(managed)], check=True, capture_output=True)
            subprocess.run(["git", "checkout", "-b", "other"], cwd=managed, check=True, capture_output=True)
            project = base / "project"
            project.mkdir()
            result = subprocess.run(
                [
                    "bash",
                    str(INSTALLER),
                    "codex",
                    str(project),
                    "consumer",
                    "--knowledge-root",
                    str(managed),
                    "--repository-url",
                    str(source),
                    "--repository-ref",
                    "main",
                    "--skip-resources",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("branch mismatch", result.stderr)
            self.assertEqual("other", subprocess.check_output(["git", "branch", "--show-current"], cwd=managed, text=True).strip())
            self.assertEqual([], list(project.iterdir()))

    def test_offline_explicit_checkout_does_not_require_an_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "repo"
            self.create_repository_fixture(root)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            project = base / "project"
            project.mkdir()
            result = subprocess.run(
                [
                    "bash",
                    str(INSTALLER),
                    "codex",
                    str(project),
                    "consumer",
                    "--knowledge-root",
                    str(root),
                    "--skip-repository-update",
                    "--skip-resources",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((project / ".agents/skills/knowledge-query").is_symlink())

    def test_missing_runtime_dependencies_are_installed_automatically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            project.mkdir()
            marker = base / "dependency-installed"
            python_wrapper = base / "python3"
            python_wrapper.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"${1:-}\" == \"-m\" && \"${2:-}\" == \"pip\" && \"${3:-}\" == \"install\" ]]; then\n"
                f"  touch {marker!s}\n"
                "  exit 0\n"
                "fi\n"
                "if [[ \"${1:-}\" == \"-\" ]]; then\n"
                "  payload=$(cat)\n"
                f"  if [[ \"$payload\" == *\"import yaml\"* && ! -f {marker!s} ]]; then\n"
                "    exit 1\n"
                "  fi\n"
                f"  printf '%s\\n' \"$payload\" | {sys.executable!s} \"$@\"\n"
                "  exit $?\n"
                "fi\n"
                f"exec {sys.executable!s} \"$@\"\n",
                encoding="utf-8",
            )
            python_wrapper.chmod(0o755)
            environment = os.environ.copy()
            environment["CANNBOT_PYTHON"] = str(python_wrapper)
            result = subprocess.run(
                [
                    "bash",
                    str(INSTALLER),
                    "codex",
                    str(project),
                    "consumer",
                    "--skip-resources",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(marker.is_file())
            self.assertIn("Installing Python runtime dependencies", result.stdout)

    def test_agents_is_not_a_client_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_installer(project, "agents", "consumer")
            self.assertEqual(2, result.returncode)
            self.assertIn("unknown agent: agents", result.stderr)
            self.assertEqual([], list(project.iterdir()))
            help_result = subprocess.run(
                ["bash", str(INSTALLER), "--help"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertNotIn("<agents|", help_result.stdout)

    def test_api_skill_conflict_prevents_partial_consumer_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            conflict = project / ".agents/skills/ascendc-api-knowledge-query"
            conflict.mkdir(parents=True)
            marker = conflict / "user-content.md"
            marker.write_text("preserve user content\n", encoding="utf-8")
            result = self.run_installer(project, "codex", "consumer")
            self.assertEqual(2, result.returncode)
            self.assertFalse((project / ".agents/skills/knowledge-query").exists())
            self.assertFalse((project / ".cannbot/knowledge.env").exists())
            self.assertEqual("preserve user content\n", marker.read_text(encoding="utf-8"))

    def test_existing_query_only_install_can_add_api_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            query = project / ".agents/skills/knowledge-query"
            query.parent.mkdir(parents=True)
            query.symlink_to(ROOT / ".agents/skills/knowledge-query", target_is_directory=True)
            before = query.lstat().st_ino
            for _ in range(2):
                result = self.run_installer(project, "codex", "consumer")
                self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(before, query.lstat().st_ino)
            self.assertEqual(
                ROOT / ".agents/skills/ascendc-api-knowledge-query",
                (project / ".agents/skills/ascendc-api-knowledge-query").resolve(),
            )

    def test_config_conflict_does_not_leave_skill_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".cannbot/knowledge.env").mkdir(parents=True)
            result = self.run_installer(project, "claude", "consumer")
            self.assertEqual(result.returncode, 2)
            self.assertIn("non-regular config path", result.stderr)
            self.assertFalse((project / ".agents/skills/knowledge-query").exists())
            self.assertFalse((project / ".claude/skills/knowledge-query").exists())
            self.assertFalse((project / "CLAUDE.md").exists())

    def test_malformed_prompt_markers_do_not_leave_partial_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            prompt = project / "AGENTS.md"
            original = "# Existing\n\n<!-- cannbot-knowledge:start -->\n"
            prompt.write_text(original, encoding="utf-8")
            result = self.run_installer(project, "codex", "consumer")
            self.assertEqual(result.returncode, 2)
            self.assertIn("malformed cannbot-knowledge prompt markers", result.stderr)
            self.assertFalse((project / ".agents/skills/knowledge-query").exists())
            self.assertFalse((project / ".cannbot/knowledge.env").exists())
            self.assertEqual(prompt.read_text(encoding="utf-8"), original)

    def test_malformed_marker_in_another_managed_prompt_fails_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            prompt = project / "AGENTS.md"
            original = "# Existing\n\n<!-- cannbot-knowledge:end -->\n"
            prompt.write_text(original, encoding="utf-8")
            result = self.run_installer(project, "claude", "consumer")
            self.assertEqual(2, result.returncode)
            self.assertIn("malformed cannbot-knowledge prompt markers", result.stderr)
            self.assertFalse((project / ".agents/skills/knowledge-query").exists())
            self.assertFalse((project / ".cannbot/knowledge.env").exists())
            self.assertFalse((project / "CLAUDE.md").exists())
            self.assertEqual(original, prompt.read_text(encoding="utf-8"))

    def test_copied_query_can_search_but_is_not_a_complete_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_installer(project, "codex", "consumer")
            self.assertEqual(result.returncode, 0, result.stderr)
            canonical = project / ".agents/skills/knowledge-query"
            canonical.unlink()
            shutil.copytree(ROOT / ".agents/skills/knowledge-query", canonical)
            query = subprocess.run(
                [
                    sys.executable,
                    str(project / QUERY_RELATIVE),
                    "search",
                    "--query",
                    "qzxk_vwbr_hjdm_plqn",
                    "--technology",
                    "ascendc",
                    "--platform",
                    "a2",
                    "--k",
                    "1",
                ],
                cwd=project,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(query.returncode, 0, query.stderr)
            self.assertEqual(json.loads(query.stdout)["count"], 0)
            verify = subprocess.run(
                [sys.executable, str(canonical / "scripts/knowledge_index.py"),
                 "verify", "--level", "full"],
                cwd=project, check=False, text=True, capture_output=True,
            )
            self.assertNotEqual(verify.returncode, 0)
            self.assertIn("governance/contracts", verify.stderr)

    def test_install_is_idempotent_and_prompt_can_be_uninstalled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
            first = self.run_installer(project, "codex", "consumer")
            second = self.run_installer(project, "codex", "consumer")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(prompt.count("<!-- cannbot-knowledge:start -->"), 1)
            uninstall = self.run_installer(
                project,
                "codex",
                "consumer",
                "--prompt-action",
                "uninstall",
            )
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(prompt.strip(), "# Existing")
            self.assertTrue((project / ".agents/skills/knowledge-query").is_symlink())

    def test_prompt_reinstall_reuses_the_installed_contributor_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            installed = self.run_installer(project, "codex", "contributor")
            self.assertEqual(installed.returncode, 0, installed.stderr)
            reinstalled = self.run_installer(
                project,
                "codex",
                "--prompt-action",
                "reinstall",
            )
            self.assertEqual(reinstalled.returncode, 0, reinstalled.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("### 贡献者附加流程", prompt)
            self.assertEqual(prompt.count("<!-- cannbot-knowledge:start -->"), 1)


if __name__ == "__main__":
    unittest.main()
