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
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "init.sh"
QUERY_RELATIVE = Path(".agents/skills/knowledge-query/scripts/knowledge_query.py")


class InstallerTests(unittest.TestCase):
    def test_default_resource_preparation_precedes_project_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            shutil.copy2(INSTALLER, root / "init.sh")
            (root / "knowledge").mkdir()
            registry = root / "governance/schemas/registries.yaml"
            registry.parent.mkdir(parents=True)
            registry.write_text("{}\n", encoding="utf-8")
            query = root / ".agents/skills/knowledge-query"
            (query / "scripts").mkdir(parents=True)
            (query / "SKILL.md").write_text("fixture\n", encoding="utf-8")
            (query / "scripts/knowledge_index.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
            api = root / ".agents/skills/ascendc-api-knowledge-query"
            api.mkdir()
            (api / "SKILL.md").write_text("fixture\n", encoding="utf-8")
            project = Path(temporary) / "project"
            project.mkdir()
            command = ["bash", str(root / "init.sh"), "agents", str(project)]
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
                ["bash", str(INSTALLER), "agents", str(project), "contributor", "--skip-resources"],
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
            self.assertIn("knowledge-ingest", prompt)
            self.assertIn("ops-knowledge-vv-ingest", prompt)
            self.assertIn("ops-knowledge-cv-ingest", prompt)
            self.assertIn("### 贡献者附加流程", prompt)

    def test_consumer_prompt_routes_to_installed_skill_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_installer(project, "agents", "consumer")
            self.assertEqual(result.returncode, 0, result.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            routes = re.findall(r"\]\((\.agents/skills/[^)]+/SKILL\.md)\)", prompt)
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

    def test_conflict_does_not_leave_partial_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            conflict = project / ".agents/skills/knowledge-query"
            conflict.mkdir(parents=True)
            result = subprocess.run(
                ["bash", str(INSTALLER), "agents", str(project), "contributor"],
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
            "agents": None,
            "codex": None,
            "claude": Path(".claude/skills"),
            "opencode": Path(".opencode/skills"),
            "trae": Path(".trae/skills"),
            "cursor": Path(".cursor/skills"),
            "copilot": Path(".github/skills"),
        }
        for agent, adapter in adapters.items():
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                result = self.run_installer(project, agent, "consumer")
                self.assertEqual(result.returncode, 0, result.stderr)
                for skill in ("knowledge-query", "ascendc-api-knowledge-query"):
                    canonical = project / ".agents/skills" / skill
                    self.assertTrue(canonical.is_symlink())
                    self.assertEqual(canonical.resolve(), ROOT / ".agents/skills" / skill)
                    if adapter is not None:
                        agent_link = project / adapter / skill
                        self.assertTrue(agent_link.is_symlink())
                        self.assertEqual(agent_link.resolve(), canonical.resolve())

    def test_api_skill_conflict_prevents_partial_consumer_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            conflict = project / ".agents/skills/ascendc-api-knowledge-query"
            conflict.mkdir(parents=True)
            marker = conflict / "user-content.md"
            marker.write_text("preserve user content\n", encoding="utf-8")
            result = self.run_installer(project, "agents", "consumer")
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
                result = self.run_installer(project, "agents", "consumer")
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
            result = self.run_installer(project, "agents", "consumer")
            self.assertEqual(result.returncode, 2)
            self.assertIn("malformed cannbot-knowledge prompt markers", result.stderr)
            self.assertFalse((project / ".agents/skills/knowledge-query").exists())
            self.assertFalse((project / ".cannbot/knowledge.env").exists())
            self.assertEqual(prompt.read_text(encoding="utf-8"), original)

    def test_installed_config_supports_a_copied_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_installer(project, "agents", "consumer")
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
                    "definitely_absent_cannbot_probe_9f6a",
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

    def test_install_is_idempotent_and_prompt_can_be_uninstalled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
            first = self.run_installer(project, "agents", "consumer")
            second = self.run_installer(project, "agents", "consumer")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(prompt.count("<!-- cannbot-knowledge:start -->"), 1)
            uninstall = self.run_installer(
                project,
                "agents",
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
            installed = self.run_installer(project, "agents", "contributor")
            self.assertEqual(installed.returncode, 0, installed.stderr)
            reinstalled = self.run_installer(
                project,
                "agents",
                "--prompt-action",
                "reinstall",
            )
            self.assertEqual(reinstalled.returncode, 0, reinstalled.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("### 贡献者附加流程", prompt)
            self.assertEqual(prompt.count("<!-- cannbot-knowledge:start -->"), 1)


if __name__ == "__main__":
    unittest.main()
