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

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/knowledge-issue-handler/scripts/scan_pr_issue_links.py"


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("scan_pr_issue_links", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def issue(number: int, title: str, state: str = "open", url: str | None = None) -> dict[str, Any]:
    return {"number": number, "state": state, "title": title, "body": "", "html_url": url or f"u{number}"}


def pull(number: int, title: str, merged: bool = True, state: str | None = None) -> dict[str, Any]:
    return {
        "number": number,
        "state": state or ("merged" if merged else "open"),
        "merged_at": "2026-01-01T00:00:00+08:00" if merged else None,
        "title": title,
        "body": "",
        "source_branch": "",
        "html_url": f"p{number}",
    }


def kinds(refs: list[tuple[Any, ...]], number: int) -> set[str]:
    return {ref[-1] for ref in refs if ref[0] == number}


class PrSideExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_template_placeholders_are_ignored(self) -> None:
        body = "关联 Issue：<!-- #123、完整链接或“无” -->\n主要改动：修复连接重试"
        self.assertEqual([], self.module.extract_pr_side_refs("fix: retry", body, "fix/retry"))

    def test_closing_keywords_and_issue_url_are_closing_evidence(self) -> None:
        refs = self.module.extract_pr_side_refs("fix: 修复日志顺序", "Fixes #42", "fix/log-order")
        self.assertIn((42, "high", "PR 文本中的关闭/关联关键词", "closing"), refs)
        refs = self.module.extract_pr_side_refs(
            "fix: 修复日志顺序", "见 https://gitcode.com/cann/cannbot-knowledge/issues/42", ""
        )
        self.assertIn((42, "high", "PR 文本中的 Issue 链接", "closing"), refs)

    def test_pr_title_prefix_counts_as_closing(self) -> None:
        refs = self.module.extract_pr_side_refs("#66: 新增芯片别名映射", "", "")
        self.assertIn((66, "high", "PR 标题以 #N 开头", "closing"), refs)

    def test_bare_reference_in_pr_body_is_not_a_link(self) -> None:
        self.assertEqual([], self.module.extract_pr_side_refs("feat: 新增知识", "Depends on #15 合入后同步", ""))


class IssueSideDeclarationTests(unittest.TestCase):
    """Phase 1 evidence: only a claim that this PR resolves the issue counts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_submitted_pr_comment_is_a_declaration(self) -> None:
        refs = self.module.extract_issue_side_refs("Bug", "", ["已提交 PR 处理本 Issue： #225"])
        self.assertIn("declare", kinds(refs, 225))
        self.assertIn(
            (225, "medium", "Issue 声明同句的 PR 处理本 Issue", "closing", "declare"),
            refs,
        )

    def test_self_reference_with_fix_verb_is_a_declaration(self) -> None:
        refs = self.module.extract_issue_side_refs("Bug", "", ["该问题已由 PR #183 合入修复"])
        self.assertIn("declare", kinds(refs, 183))

    def test_labeled_pr_field_is_a_declaration(self) -> None:
        body = "关联 PR: https://gitcode.com/cann/cannbot-knowledge/merge_requests/76"
        refs = self.module.extract_issue_side_refs("Bug", body, [], "cann/cannbot-knowledge")
        self.assertIn("declare", kinds(refs, 76))

    def test_negated_fix_verb_is_not_a_declaration(self) -> None:
        # Review counterexample 1: "尚未修复" must not read as "修复".
        refs = self.module.extract_issue_side_refs(
            "Bug", "", ["本 Issue 尚未修复，PR #251 只更新文档。"], "cann/cannbot-knowledge"
        )
        self.assertNotIn("declare", kinds(refs, 251))
        self.assertIn("mention", kinds(refs, 251))

    def test_cross_repo_pr_link_never_borrows_local_merge_state(self) -> None:
        # Review counterexample 2: a URL into another repository only carries
        # its number; matching it against this repo's same-numbered PR would
        # attribute a foreign PR's merge state to this issue.
        refs = self.module.extract_issue_side_refs(
            "Bug", "关联 PR: https://gitcode.com/another/repo/pull/251", [], "cann/cannbot-knowledge"
        )
        self.assertEqual(set(), kinds(refs, 251))

    def test_same_repo_pr_link_still_declares(self) -> None:
        # The ownership filter must not reject links into the scanned repo.
        refs = self.module.extract_issue_side_refs(
            "Bug",
            "关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/251",
            [],
            "cann/cannbot-knowledge",
        )
        self.assertIn("declare", kinds(refs, 251))

    def test_unambiguous_declaration_survives_the_guards(self) -> None:
        # Review positive case: a plain, un-negated, same-repo declaration.
        refs = self.module.extract_issue_side_refs(
            "Bug", "", ["本 Issue 已由本仓 PR #251 修复"], "cann/cannbot-knowledge"
        )
        self.assertIn("declare", kinds(refs, 251))

    def test_repo_ownership_defaults_to_suspicious_when_repo_unknown(self) -> None:
        # Without a repo to compare against, no URL is trusted as a declaration.
        refs = self.module.extract_issue_side_refs(
            "Bug", "关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/251", []
        )
        self.assertEqual(set(), kinds(refs, 251))

    def test_experimental_baseline_reference_is_only_a_mention(self) -> None:
        body = "[PR #68](https://gitcode.com/cann/cannbot-knowledge/pull/68) 的 WIP 批次还包含大量英文卡"
        refs = self.module.extract_issue_side_refs("检索缺口", body, [])
        self.assertEqual({"mention"}, kinds(refs, 68))

    def test_complementary_reference_is_only_a_mention(self) -> None:
        body = "- 两卡均挂在 Issue #23 动线下，与已合入导航层（PR #100）和检视中组合卡层（PR #101）互补"
        refs = self.module.extract_issue_side_refs("场景契约链卡", body, [])
        self.assertEqual({"mention"}, kinds(refs, 100))
        self.assertEqual({"mention"}, kinds(refs, 101))

    def test_pr_merged_into_another_pr_does_not_declare_the_issue(self) -> None:
        body = "1. **PR 合并**：原 PR #99（试点 4 链路，30 卡）已并入 PR #100（对抗验证批次），#99 关闭"
        refs = self.module.extract_issue_side_refs("动线", body, [])
        self.assertNotIn("declare", kinds(refs, 100))

    def test_issue_labeled_number_is_not_read_as_a_pr(self) -> None:
        body = "首期已提交知识缺口 Issue #88 与迁入总览占位 PR #199"
        refs = self.module.extract_issue_side_refs("知识需求", body, [])
        self.assertEqual(set(), kinds(refs, 88))
        self.assertIn("mention", kinds(refs, 199))

    def test_pr_counts_are_not_references(self) -> None:
        self.assertEqual([], self.module.extract_issue_side_refs("申请", "已有贡献：已合入 PR 9 个", []))


class TwoPhasePairingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_declared_merged_pr_is_closable(self) -> None:
        pairs, funnel = self.module.build_pairs(
            [issue(1, "日志乱序")],
            [pull(2, "fix(logs): 修复日志乱序")],
            {1: ["关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/2"]},
            "cann/cannbot-knowledge",
        )
        self.assertEqual(1, len(pairs))
        self.assertEqual("issue_declared", pairs[0]["phase"])
        self.assertEqual("可直接闭环（Issue 已声明）", pairs[0]["classification"])
        self.assertEqual(1, funnel["closable_issues"])

    def test_declared_open_pr_blocks_closing(self) -> None:
        pairs, funnel = self.module.build_pairs(
            [issue(1, "日志乱序")],
            [pull(2, "fix(logs): 修复日志乱序", merged=False)],
            {1: ["已提交 PR 处理本 Issue： #2"]},
            "cann/cannbot-knowledge",
        )
        self.assertEqual("PR 进行中（Issue 已声明）", pairs[0]["classification"])
        self.assertEqual(0, funnel["closable_issues"])

    def test_mention_never_recommends_closing(self) -> None:
        pairs, funnel = self.module.build_pairs(
            [issue(1, "检索缺口")],
            [pull(68, "feat: 泛化增量")],
            {1: ["在 PR #68 的固定提交上构建索引，结果仍漏召回"]},
            "cann/cannbot-knowledge",
        )
        self.assertEqual("issue_mention", pairs[0]["phase"])
        self.assertEqual("PR 已合并，待核对闭环（Issue 仅提及）", pairs[0]["classification"])
        self.assertEqual(0, funnel["closable_issues"])

    def test_declaration_outranks_mention_for_the_same_issue(self) -> None:
        pairs, _ = self.module.build_pairs(
            [issue(1, "动线")],
            [pull(100, "feat: 导航层", merged=True), pull(101, "feat: 组合卡")],
            {1: ["关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/100\n与 PR #101 互补"]},
            "cann/cannbot-knowledge",
        )
        self.assertEqual([(1, 100)], [(item["issue"], item["pr"]) for item in pairs])
        self.assertEqual("issue_declared", pairs[0]["phase"])

    def test_undeclared_issue_is_matched_from_the_pr_side(self) -> None:
        pairs, funnel = self.module.build_pairs(
            [issue(103, "迁入 Ascend C 算子调试知识")],
            [pull(232, "feat(knowledge): 迁入调试知识卡（Issue #103 第五批）")],
            {},
        )
        self.assertEqual("pr_reference", pairs[0]["phase"])
        self.assertEqual("PR 已合并，待核对闭环（PR 侧引用）", pairs[0]["classification"])
        self.assertEqual(1, funnel["issues_matched_by_pr_reference"])

    def test_stale_declaration_falls_through_to_other_evidence(self) -> None:
        stale_pr = pull(222, "fix(logs): 修复日志乱序", merged=False, state="closed")
        replacement = pull(240, "fix(logs): 修复日志乱序", merged=True)
        replacement["body"] = "Fixes #97"
        pairs, _ = self.module.build_pairs(
            [issue(97, "logs 乱序")],
            [stale_pr, replacement],
            {97: ["关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/222"]},
            "cann/cannbot-knowledge",
        )
        phases = {(item["pr"], item["phase"]) for item in pairs}
        self.assertIn((222, "issue_declared"), phases)
        self.assertIn((240, "pr_reference"), phases)

    def test_similarity_is_low_confidence_and_never_closable(self) -> None:
        module = self.module
        original = module.SIMILARITY_MIN_IDF
        module.SIMILARITY_MIN_IDF = 0.0
        try:
            pairs, funnel = module.build_pairs(
                [issue(48, "新增 Ascend310B 目标平台知识卡")],
                [pull(111, "knowledge: 新增 Ascend310B 目标平台知识卡")],
                {},
            )
        finally:
            module.SIMILARITY_MIN_IDF = original
        self.assertEqual("title_similarity", pairs[0]["phase"])
        self.assertEqual("low", pairs[0]["confidence"])
        self.assertEqual("疑似匹配，需人工判断", pairs[0]["classification"])
        self.assertEqual(0, funnel["closable_issues"])

    def test_funnel_accounts_for_every_issue(self) -> None:
        pairs, funnel = self.module.build_pairs(
            [issue(1, "日志乱序"), issue(2, "检索缺口"), issue(3, "无关需求")],
            [pull(10, "fix(logs): 修复日志乱序"), pull(11, "feat: 泛化增量")],
            {1: ["关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/10"], 2: ["在 PR #11 上验证"]},
            "cann/cannbot-knowledge",
        )
        accounted = (
            funnel["issues_declared"]
            + funnel["issues_mentioned"]
            + funnel["issues_matched_by_pr_reference"]
            + funnel["issues_matched_by_similarity"]
            + funnel["issues_unmatched"]
        )
        self.assertEqual(3, accounted)
        self.assertEqual(1, funnel["issues_unmatched"])
        self.assertEqual([3], [item["issue"] for item in funnel["unmatched_list"]])
        self.assertEqual(2, len(pairs))

    def test_closed_issue_is_not_actionable(self) -> None:
        pairs, _ = self.module.build_pairs(
            [issue(1, "日志乱序", state="closed")],
            [pull(2, "fix(logs): 修复日志乱序")],
            {1: ["关联 PR: https://gitcode.com/cann/cannbot-knowledge/pull/2"]},
            "cann/cannbot-knowledge",
        )
        self.assertEqual("无需处理（Issue 已关闭）", pairs[0]["classification"])


class ClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_classification_depends_on_phase_and_pr_state(self) -> None:
        open_issue = {"state": "open"}
        merged_pr = {"state": "merged", "merged_at": "2026-01-01T00:00:00+08:00"}
        open_pr = {"state": "open", "merged_at": ""}
        closed_pr = {"state": "closed", "merged_at": ""}
        module = self.module
        self.assertEqual(
            "可直接闭环（Issue 已声明）", module.classify(open_issue, merged_pr, module.PHASE_DECLARED)
        )
        self.assertEqual(
            "PR 进行中（Issue 已声明）", module.classify(open_issue, open_pr, module.PHASE_DECLARED)
        )
        self.assertEqual(
            "PR 已关闭未合入（Issue 已声明）",
            module.classify(open_issue, closed_pr, module.PHASE_DECLARED),
        )
        self.assertEqual(
            "PR 已合并，待核对闭环（PR 侧引用）",
            module.classify(open_issue, merged_pr, module.PHASE_INFERRED),
        )
        self.assertEqual("疑似匹配，需人工判断", module.classify(open_issue, merged_pr, module.PHASE_SIMILARITY))

    def test_only_declared_close_is_closable(self) -> None:
        self.assertEqual(("可直接闭环（Issue 已声明）",), self.module.CLOSABLE_CLASSES)


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def _report(self) -> dict[str, Any]:
        return {
            "repo": "cann/cannbot-knowledge",
            "fetched_at": "2026-11-07T11:00:00+08:00",
            "issue_state": "open",
            "pr_state": "all",
            "summary": {"issues": 2, "pulls": 2, "pairs": 2, "suggest_close": 1},
            "funnel": {
                "issues": 2,
                "issues_declared": 1,
                "issues_mentioned": 1,
                "issues_matched_by_pr_reference": 0,
                "issues_matched_by_similarity": 0,
                "issues_unmatched": 0,
                "closable_pairs": 1,
                "closable_issues": 1,
                "unmatched_list": [],
            },
            "pairs": [
                {
                    "issue": 1,
                    "pr": 2,
                    "phase": "issue_declared",
                    "confidence": "high",
                    "evidence": ["Issue 声明该 PR 与本 Issue 对应/修复"],
                    "classification": "可直接闭环（Issue 已声明）",
                    "issue_title": "[Bug|缺陷] x",
                    "pr_title": "fix: y",
                    "pr_url": "https://example/2",
                    "issue_url": "https://example/1",
                },
                {
                    "issue": 3,
                    "pr": 4,
                    "phase": "issue_mention",
                    "confidence": "medium",
                    "evidence": ["Issue 文本或评论提及该 PR"],
                    "classification": "PR 已合并，待核对闭环（Issue 仅提及）",
                    "issue_title": "z",
                    "pr_title": "feat: w",
                    "pr_url": "https://example/4",
                    "issue_url": "https://example/3",
                },
            ],
        }

    def test_report_escapes_table_pipes(self) -> None:
        markdown = self.module.render_markdown(self._report())
        self.assertIn("[Bug\\|缺陷] x", markdown)
        self.assertIn("## ① Issue 明确声明修复 PR", markdown)
        self.assertIn("## ② Issue 仅提及 PR", markdown)

    def test_report_shows_the_funnel(self) -> None:
        markdown = self.module.render_markdown(self._report())
        self.assertIn("## 漏斗", markdown)
        self.assertIn("可直接闭环：1 个 Issue", markdown)

    def test_comment_drafts_skip_negligible_links(self) -> None:
        report = self._report()
        for pair in report["pairs"]:
            pair["classification"] = "疑似匹配，需人工判断"
        markdown = self.module.render_markdown(report)
        self.assertNotIn("评论草稿", markdown)


class SingleIssueScopeTests(unittest.TestCase):
    """`--issue N` narrows the scan without touching the repository."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def _raw(self, directory: Path) -> Path:
        raw = directory / "raw"
        raw.mkdir()
        (raw / "issues.json").write_text(
            json.dumps(
                [
                    {
                        "number": 53,
                        "state": "open",
                        "title": "补充 AscendC 指南",
                        "body": "关联 PR: https://gitcode.com/cann/x/merge_requests/136",
                        "html_url": "u53",
                    },
                    {"number": 54, "state": "open", "title": "无关需求", "body": "", "html_url": "u54"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (raw / "pulls.json").write_text(
            json.dumps(
                [
                    {
                        "number": 136,
                        "state": "merged",
                        "merged_at": "2026-10-27T08:39:05+08:00",
                        "title": "knowledge(ascendc): 补充知识卡",
                        "body": "",
                        "source_branch": "",
                        "html_url": "p136",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return raw

    def test_single_issue_scan_keeps_only_that_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = self._raw(Path(tmp))
            out = Path(tmp) / "out"
            with redirect_stdout(io.StringIO()):
                code = self.module.main(
                    ["--repo", "cann/x", "--from-raw", str(raw), "--issue", "53", "--output-dir", str(out)]
                )
            self.assertEqual(0, code)
            report = json.loads((out / "pr-issue-links.json").read_text(encoding="utf-8"))
            markdown = (out / "pr-issue-links.md").read_text(encoding="utf-8")
        self.assertEqual(53, report["issue_filter"])
        self.assertEqual(1, report["summary"]["issues"])
        self.assertEqual({53}, {item["issue"] for item in report["pairs"]})
        self.assertIn("单 Issue 模式，仅 #53", markdown)

    def test_unknown_issue_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = self._raw(Path(tmp))
            out = Path(tmp) / "out"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = self.module.main(
                    ["--repo", "cann/x", "--from-raw", str(raw), "--issue", "999", "--output-dir", str(out)]
                )
        self.assertEqual(2, code)
        self.assertFalse((out / "pr-issue-links.json").exists())


class ReadOnlyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_scanner_is_read_only(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ('method="POST"', 'method="PUT"', 'method="PATCH"', 'method="DELETE"'):
            self.assertNotIn(forbidden, source)
        self.assertIn('method="GET"', source)
        self.assertIn("never comments", source)

    def test_token_rides_as_access_token_query_param(self) -> None:
        # The vendored gitcode_client.py authenticates via the access_token
        # query parameter; PRIVATE-TOKEN headers are rejected by some v5
        # endpoints. The scanner must stay consistent with that contract,
        # so no request header may carry the token.
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('headers["PRIVATE-TOKEN"]', source)
        self.assertIn("access_token", source)

    def test_pagination_ceiling_is_reported(self) -> None:
        module = self.module
        pages = [{"per_page": 1, "page": number, "items": [{"number": number}]} for number in range(1, 4)]
        requested = []

        def fake_api_get(path, params, token):
            requested.append(params["page"])
            return pages[params["page"] - 1]["items"]

        original = module.api_get
        original_sleep = module.time.sleep
        module.api_get = fake_api_get
        module.time.sleep = lambda _seconds: None
        try:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                collected = module.paginate("/repos/x/y/issues", None, max_pages=3, per_page=1)
        finally:
            module.api_get = original
            module.time.sleep = original_sleep
        self.assertEqual(3, len(collected))
        self.assertEqual([1, 2, 3], requested)
        self.assertIn("hit the --max-pages ceiling (3 pages)", stderr.getvalue())
        self.assertIn("results are truncated", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
