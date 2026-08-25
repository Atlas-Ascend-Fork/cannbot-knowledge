from __future__ import annotations

import json
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
    def run_installer(self, project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(INSTALLER), *arguments[:1], str(project), *arguments[1:]],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_contributor_install_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = subprocess.run(
                ["bash", str(INSTALLER), "agents", str(project), "contributor"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = {path.name for path in (project / ".agents/skills").iterdir() if path.is_symlink()}
            self.assertEqual(installed, {"knowledge-ingest", "knowledge-query", "knowledge-lint"})
            env = (project / ".cannbot/knowledge.env").read_text(encoding="utf-8")
            self.assertIn(f"export CANNBOT_KNOWLEDGE_ROOT={ROOT}", env)
            self.assertIn("export CANNBOT_KNOWLEDGE_PROFILE=contributor", env)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("<!-- cannbot-knowledge:start -->", prompt)
            self.assertIn("knowledge-ingest", prompt)
            self.assertIn("### 贡献者附加流程", prompt)

    def test_consumer_prompt_preserves_query_execution_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_installer(project, "agents", "consumer")
            self.assertEqual(result.returncode, 0, result.stderr)
            prompt = (project / "AGENTS.md").read_text(encoding="utf-8")
            required_contract = (
                "### 入口硬门禁",
                "### 知识库中有什么",
                "`discover`",
                "`common`",
                "`ascendc`、`triton`、`tilelang`、`pypto`、`shared`",
                "`graph`、`runtime`",
                "### 什么时候调用或重新调用",
                "### 每次执行的基本流程",
                "`local_path`",
                "search receipt",
                "outcome manifest",
                "### 需要立即纠正的行为",
                "索引缺失或 stale 后改为遍历知识树",
            )
            for expected in required_contract:
                with self.subTest(expected=expected):
                    self.assertIn(expected, prompt)
            self.assertNotIn("### 贡献者附加流程", prompt)

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
                canonical = project / ".agents/skills/knowledge-query"
                self.assertTrue(canonical.is_symlink())
                self.assertEqual(canonical.resolve(), ROOT / ".agents/skills/knowledge-query")
                if adapter is not None:
                    agent_link = project / adapter / "knowledge-query"
                    self.assertTrue(agent_link.is_symlink())
                    self.assertEqual(agent_link.resolve(), canonical.resolve())

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
