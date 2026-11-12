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

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills/knowledge-issue-handler"


class KnowledgeIssueHandlerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.routing = (SKILL_ROOT / "references/issue-routing.md").read_text(
            encoding="utf-8"
        )
        cls.evidence = (SKILL_ROOT / "references/knowledge-evidence.md").read_text(
            encoding="utf-8"
        )
        cls.config = yaml.safe_load(
            (SKILL_ROOT / "assets/classify_config.yaml.template").read_text(
                encoding="utf-8"
            )
        )
        cls.skills_root = ROOT / ".agents/skills"

    def test_default_configuration_is_scoped_and_read_only(self) -> None:
        self.assertEqual("cann/cannbot-knowledge", self.config["repo"])
        self.assertFalse(self.config["auto-response"])
        self.assertFalse(self.config["auto-assign"])
        self.assertEqual("", self.config["auto-assign-fallback-user"])
        self.assertEqual([], self.config["ignored_issue_ids"])
        for marker in ("Knowledge-Report", "Knowledge-Request", "Bug-Report"):
            self.assertIn(marker, "\n".join(self.config["responsibility"]["handle"]))
        self.assertIn("RFC", "\n".join(self.config["responsibility"]["list-only"]))
        self.assertIn("Roadmap", "\n".join(self.config["responsibility"]["ignore"]))

    def test_adapter_reuses_handler_and_does_not_add_an_event_bot(self) -> None:
        for dependency in ("gitcode-issue-handler", "gitcode-toolkit"):
            self.assertIn(dependency, self.skill)
        self.assertIn("issue_pipeline.py", self.skill)
        self.assertIn("resume --new-run", self.skill)
        self.assertIn("不提供 webhook、定时任务或无人值守运行器", self.skill)
        self.assertIn("vendored 副本", self.skill)
        self.assertIn("优先使用本仓内置的 vendored 副本", self.skill)
        self.assertNotIn(".gitcode/workflows", self.skill)

    def test_external_writes_and_knowledge_changes_require_separate_authorization(self) -> None:
        for required in (
            "auto-response: false",
            "auto-assign` 默认关闭",
            "后续追问始终按原 Handler 要求单独批准",
            "不自动运行 stale close",
            "不改知识卡、索引、治理文件、源码或 `.gitcode/`",
            "accept` 只表示材料审核完成，不等于发布授权",
        ):
            self.assertIn(required, self.skill)

    def test_vendored_docs_never_reference_removed_scripts(self) -> None:
        # Review finding: issue-routing.md instructed agents to run the
        # upstream knowledge_query.py preflight, but that script is not in the
        # trimmed copy, so following the document broke at the entry point.
        # Every reference in the vendored docs must now either name the
        # replacement (本仓 knowledge-query) or be a historical mention
        # guarded by the trim notice.
        handler_refs = self.skills_root / "gitcode-issue-handler" / "references"
        for doc in ("issue-routing.md", "runtime-knowledge.md", "code-root-cause.md"):
            text = (handler_refs / doc).read_text(encoding="utf-8")
            if "knowledge_query.py" in text:
                # The trim notice explains the replacement; every doc that
                # still names the removed script must carry it somewhere.
                self.assertIn(
                    "不在本仓 vendored 保留集",
                    text,
                    f"{doc} mentions knowledge_query.py without the trim notice",
                )
        # The two rewritten entry points must carry the replacement contract.
        routing = (handler_refs / "issue-routing.md").read_text(encoding="utf-8")
        self.assertIn("预检由本仓 `knowledge-query` Skill 直接承担", routing)
        runtime = (handler_refs / "runtime-knowledge.md").read_text(encoding="utf-8")
        self.assertIn("裁剪副本注意", runtime)
        manifest = (self.skills_root / "gitcode-issue-handler" / "VENDORED.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`knowledge_query.py`、`refresh_issue_knowledge.py`", manifest)

    def test_all_issue_templates_have_distinct_routes(self) -> None:
        for marker in (
            "Knowledge-Report",
            "Knowledge-Request",
            "Bug-Report",
            "Requirement",
            "[RFC]",
        ):
            self.assertIn(marker, self.routing)
        self.assertIn("默认 `list-only`", self.routing)
        self.assertIn("默认不修改代码", self.routing)
        self.assertIn("默认不创建知识卡、不更新索引或导航", self.routing)
        self.assertIn("不修改 pipeline、不增加旁路状态文件", self.routing)

    def test_knowledge_answers_require_full_cards_and_scope_checks(self) -> None:
        for required in (
            "knowledge-query",
            "ascendc-api-knowledge-query",
            "runtime-api-knowledge-query",
            "discover",
            "阅读全文",
            "不猜测平台",
            "索引缺失、损坏或 stale 属于查询错误",
            "有效零命中",
            "不承诺未来修复、收录、版本支持、排期或性能收益",
        ):
            self.assertIn(required, self.evidence)
        self.assertIn("不能冒充知识库卡片", self.evidence)
        self.assertIn("知识检索的唯一入口", self.evidence)

    def test_repository_internal_adapter_is_not_added_to_business_installer(self) -> None:
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        match = re.search(
            r"ALL_INSTALLABLE_SKILLS=\(\n(?P<body>.*?)\n\)", installer, re.DOTALL
        )
        self.assertIsNotNone(match)
        self.assertNotIn("knowledge-issue-handler", match.group("body"))
        self.assertIn("仓内专用 Skill", self.skill)

    def test_public_guide_preserves_draft_first_usage(self) -> None:
        guide = (ROOT / "docs/issue_handling.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/issue_handling.md", readme)
        self.assertIn("先拟稿，不发送，不改代码", guide)
        self.assertIn("GITCODE_TOKEN", guide)
        self.assertIn("自动首响", guide)
        self.assertIn("不修改 `.gitcode/`", guide)

    def test_runtime_tree_is_git_ignored(self) -> None:
        # Config, queues and raw API snapshots live in .cannbot/; committing them
        # would leak issue snapshots and dirty the tree on every scan.
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".cannbot/", [line.strip() for line in ignore])


class RoleNominationContractTests(unittest.TestCase):
    """Lock the Committer-nomination route: facts only, no appointment promises."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.reference = (SKILL_ROOT / "references/role-nomination.md").read_text(encoding="utf-8")
        cls.routing = (SKILL_ROOT / "references/issue-routing.md").read_text(encoding="utf-8")
        cls.guide = (ROOT / "docs/issue_handling.md").read_text(encoding="utf-8")
        cls.config = yaml.safe_load(
            (SKILL_ROOT / "assets/classify_config.yaml.template").read_text(encoding="utf-8")
        )
        cls.script_path = SKILL_ROOT / "scripts/collect_nomination_evidence.py"
        cls.script = cls.script_path.read_text(encoding="utf-8")

    def test_reference_covers_template_and_prohibitions(self) -> None:
        for required in (
            "已收到提名申请，本单作为提名记录保留。",
            "已核验的贡献（截至",
            "Committer 任命属治理事项",
            "只认 `merged_at` 非空",
            "不做承诺",
            "不评价申请人水平",
            "跨仓贡献",
            "申请人自述",
        ):
            self.assertIn(required, self.reference)
        # The knowledge/bug template must not leak into this route.
        self.assertIn("不能套知识/缺陷的根因-复现结构", self.reference)

    def test_route_is_separate_from_governance_list_only(self) -> None:
        self.assertIn("references/role-nomination.md", self.skill)
        self.assertIn("角色任命", self.skill)
        self.assertIn("collect_nomination_evidence.py", self.skill)
        self.assertIn("角色任命申请", self.routing)
        self.assertIn("role-nomination.md", self.routing)
        handle = "\n".join(self.config["responsibility"]["handle"])
        list_only = "\n".join(self.config["responsibility"]["list-only"])
        self.assertIn("角色任命", handle)
        self.assertIn("角色任命申请不在此列", list_only)
        self.assertIn("角色任命申请", self.guide)
        self.assertIn("collect_nomination_evidence.py", self.guide)

    def test_collector_stays_read_only(self) -> None:
        for verb in ('method="POST"', 'method="PATCH"', 'method="PUT"', 'method="DELETE"'):
            self.assertNotIn(verb, self.script)
        self.assertIn("Read-only", self.script)
        self.assertIn("api_get", self.script)

    def test_collector_output_is_isolated_per_issue_or_login(self) -> None:
        # Two applicants must never overwrite each other's evidence: the
        # default output directory embeds the issue number (or login when
        # --issue is omitted) instead of a shared "data/nomination" stem.
        self.assertNotIn('default=".cannbot/gitcode-issue-handler/data/nomination"', self.script)
        self.assertIn("nomination-{args.issue}", self.script)
        self.assertIn("nomination-{login}", self.script)

    def test_evidence_parsing_ignores_web_paths_and_counts_indexes_apart(self) -> None:
        module = _load_collector(self.script_path)
        body = (
            "参考 https://gitcode.com/cann/cannbot-knowledge/pull/218 与 "
            "knowledge/runtime/concepts/overview.md ，责任田为 knowledge/runtime/concepts 。"
        )
        # "knowledge/pull" inside a PR URL must never win.
        self.assertEqual("knowledge/runtime", module.detect_domain_path(body))
        self.assertEqual("", module.detect_domain_path("没有路径，只有 PR 链接 https://gitcode.com/cann/x/pull/1"))

    def test_draft_keeps_facts_separate_from_open_questions(self) -> None:
        module = _load_collector(self.script_path)
        payload = {
            "issue": 999,
            "login": "someone",
            "domain": "knowledge/tools",
            "domain_stats": {"path": "knowledge/tools", "exists": True, "cards": 5, "indexes": 2},
            "other_repos": ["asc-tools"],
            "pulls": [
                {
                    "number": 216,
                    "title": "feat(knowledge): 迁入工具知识卡",
                    "state": "merged",
                    "merged_at": "2026-11-09",
                    "in_domain": True,
                    "governance": False,
                    "files": 7,
                    "cards": 5,
                    "indexes": 2,
                    "additions": 356,
                    "deletions": 2,
                },
                {
                    "number": 217,
                    "title": "feat(knowledge): 第二批",
                    "state": "open",
                    "merged_at": "",
                    "in_domain": True,
                    "governance": False,
                    "files": 0,
                    "cards": 0,
                    "indexes": 0,
                    "additions": 0,
                    "deletions": 0,
                },
            ],
            "issues": [
                {
                    "number": 101,
                    "title": "[Knowledge-Request|知识需求]: 工具知识",
                    "state": "open",
                    "created_at": "2026-11-01",
                }
            ],
        }
        draft = module.build_draft(payload)
        self.assertIn("!216", draft)
        self.assertIn("5 张卡 + 2 个索引共 7 个文件", draft)
        self.assertIn("!217 在途", draft)
        self.assertIn("#101 在途", draft)
        self.assertIn("跨仓贡献为申请人自述", draft)
        self.assertIn("<!-- 待确认：责任田边界", draft)
        self.assertTrue(draft.rstrip().endswith("同步安排进入 SIG 例会陈述。"))
        # No promise wording, no root-cause structure.
        for banned in ("尽快", "本周", "排期", "**根因**", "**复现**"):
            self.assertNotIn(banned, draft)


def _load_collector(path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("collect_nomination_evidence", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReplyStructureContractTests(unittest.TestCase):
    """Lock the six-section reply flow to routes that have a failure path."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = (SKILL_ROOT / "references/reply-structure.md").read_text(encoding="utf-8")
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.routing = (SKILL_ROOT / "references/issue-routing.md").read_text(encoding="utf-8")
        cls.nomination = (SKILL_ROOT / "references/role-nomination.md").read_text(encoding="utf-8")
        cls.guide = (ROOT / "docs/issue_handling.md").read_text(encoding="utf-8")

    def test_six_sections_are_all_defined(self) -> None:
        for section in ("根因", "复现", "影响", "修复方向", "验证建议", "当前进展与下一步"):
            self.assertIn(section, self.reference)

    def test_routes_without_failure_path_are_excluded(self) -> None:
        # Nomination is an appointment record, RFCs are reviewed by maintainers:
        # neither has a root cause to reproduce, so both must stay out.
        self.assertIn("角色任命申请", self.reference)
        self.assertIn("role-nomination.md", self.reference)
        self.assertIn("**不用**", self.reference)
        self.assertIn("`list-only`", self.reference)
        self.assertIn("reply-structure.md", self.nomination)
        self.assertIn("不加「根因 / 复现 / 影响 / 修复方向 / 验证建议」小节", self.nomination)

    def test_variants_rename_sections_for_knowledge_routes(self) -> None:
        for variant in ("问题定位", "触发条件", "修正方向", "缺口定位", "入库方向", "验收口径"):
            self.assertIn(variant, self.reference)

    def test_evidence_levels_are_named_explicitly(self) -> None:
        # The batch that motivated this file padded 复现/影响 from issue prose;
        # the wording rule has to stay explicit.
        self.assertIn("未实机复现", self.reference)
        self.assertIn("本机已复现", self.reference)
        self.assertIn("源码推断", self.reference)

    def test_structure_is_wired_into_routing_and_guide(self) -> None:
        self.assertIn("references/reply-structure.md", self.skill)
        self.assertIn("reply-structure.md", self.routing)
        self.assertIn("reply-structure.md", self.guide)


class VendoredDependencyContractTests(unittest.TestCase):
    """Lock the in-repo vendored copies of the two GitCode collaboration skills."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skills_root = ROOT / ".agents/skills"

    def test_vendored_skill_directories_exist_with_provenance(self) -> None:
        for name in ("gitcode-issue-handler", "gitcode-toolkit"):
            root = self.skills_root / name
            self.assertTrue((root / "SKILL.md").is_file(), name)
            self.assertTrue((root / "scripts").is_dir(), name)
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Vendored 副本", text, name)
            self.assertIn("cann/cannbot-skills", text, name)
            # The copies are trimmed, not verbatim upstream checkouts.
            self.assertIn("裁剪版", text, name)
            self.assertNotIn("保持上游原样", text, name)
            manifest = (root / "VENDORED.md").read_text(encoding="utf-8")
            self.assertIn("2374941", manifest, name)

    def test_vendored_copies_are_trimmed_to_used_surface(self) -> None:
        handler = self.skills_root / "gitcode-issue-handler"
        for removed_dir in ("tests", "evals", "knowledge", "docs"):
            self.assertFalse((handler / removed_dir).exists(), removed_dir)
        self.assertFalse((handler / "README.md").exists())
        for removed_script in (
            "assign_issue.py",
            "associate_issue_pr.py",
            "auto_close_stale_issues.py",
            "build_issue_knowledge.py",
            "check_repro_env.py",
            "manage_worktrees.py",
            "operator_owner_config.py",
            "post_issue_comment.py",
            "post_triage_comment.py",
            "refresh_issue_knowledge.py",
        ):
            self.assertFalse(
                (handler / "scripts" / removed_script).exists(), removed_script
            )
        toolkit = self.skills_root / "gitcode-toolkit"
        for removed_dir in ("tests", "evals"):
            self.assertFalse((toolkit / removed_dir).exists(), removed_dir)
        for removed_script in (
            "fetch_pr_context.py",
            "trigger_pr_pipeline.sh",
        ):
            self.assertFalse(
                (toolkit / "scripts" / removed_script).exists(), removed_script
            )
        # The publish entry point documented in references/ must survive trimming.
        for kept_toolkit in ("post_issue_comment.py", "parse_gitcode_url.py", "_logging.py"):
            self.assertTrue(
                (toolkit / "scripts" / kept_toolkit).is_file(), kept_toolkit
            )
        # The entry points the adapter relies on must survive trimming.
        for kept in ("issue_pipeline.py", "classify_issues.py", "fetch_issues.py"):
            self.assertTrue((handler / "scripts" / kept).is_file(), kept)
        self.assertTrue((toolkit / "scripts" / "gitcode_client.py").is_file())

    def test_vendored_skills_are_not_installable(self) -> None:
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        match = re.search(
            r"ALL_INSTALLABLE_SKILLS=\(\n(?P<body>.*?)\n\)", installer, re.DOTALL
        )
        self.assertIsNotNone(match)
        for name in ("gitcode-issue-handler", "gitcode-toolkit"):
            self.assertNotIn(name, match.group("body"))

    def test_windows_fcntl_shim_present_in_both_script_dirs(self) -> None:
        # Vendored scripts use fcntl.flock (Unix-only). The shim keeps them
        # importable on Windows; do not remove it when re-vendoring.
        for name in ("gitcode-issue-handler", "gitcode-toolkit"):
            shim = self.skills_root / name / "scripts" / "fcntl.py"
            self.assertTrue(shim.is_file(), str(shim))
            text = shim.read_text(encoding="utf-8")
            self.assertIn("msvcrt.locking", text)
            self.assertIn("LK_LOCK", text)
            self.assertIn("LK_UNLCK", text)
            # The shim must disclose its blocking divergence: msvcrt gives up
            # after ~10s where flock waits forever, so callers can distinguish
            # contention from corruption only if the docstring says so.
            self.assertIn("10 seconds", text)

    def test_repository_style_gates_exclude_vendored_copies(self) -> None:
        # check.sh builds an explicit ruff path list that skips the vendored
        # directories; their internal style is owned by cann/cannbot-skills.
        check = (ROOT / "check.sh").read_text(encoding="utf-8")
        self.assertIn("gitcode-issue-handler/|.agents/skills/gitcode-toolkit/", check)
        self.assertIn("ruff_paths", check)
        # The direct invocation that would lint vendored trees is gone.
        self.assertNotIn("ruff check .agents/skills governance evals", check)

    def test_repository_docs_call_vendored_copies_trimmed(self) -> None:
        # "保持上游原样" contradicts the VENDORED.md manifests (裁剪版) and
        # must not reappear in the governance-facing documents.
        for relative in ("README.md", "AGENTS.md", "governance/specs/skills.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("保持上游原样", text, relative)
            self.assertIn("裁剪版", text, relative)


if __name__ == "__main__":
    unittest.main()
