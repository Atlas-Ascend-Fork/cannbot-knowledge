from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/knowledge-lint/scripts"
sys.path.insert(0, str(SCRIPTS))

import content_check as core  # noqa: E402
import content_protocol as protocol  # noqa: E402
import opencode_runner  # noqa: E402


def load_ci_adapter():
    path = ROOT / ".gitcode/scripts/content_check.py"
    spec = importlib.util.spec_from_file_location("ci_content_check_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CI = load_ci_adapter()
CONFIG = ROOT / ".agents/skills/knowledge-lint/references/content_check.toml"
OPENCODE_CONFIG = ROOT / ".agents/skills/knowledge-lint/scripts/opencode.json"


class ContentModelConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings, cls.checks = core.load_config(CONFIG)

    def test_model_uses_a_public_alias_and_secret_backed_id(self) -> None:
        self.assertEqual("content-review/content-check", self.settings.model)
        self.assertEqual(("BASE_URL", "AUTH_TOKEN", "MODEL"), self.settings.model_env)

        config = json.loads(OPENCODE_CONFIG.read_text(encoding="utf-8"))
        model = config["provider"]["content-review"]["models"]["content-check"]
        self.assertEqual("{env:MODEL}", model["id"])
        self.assertNotIn("limit", model)
        self.assertEqual("deny", config["permission"]["webfetch"])
        prompt = (
            ROOT / ".agents/skills/knowledge-lint/references/content_check_prompt.md"
        ).read_text(encoding="utf-8")
        self.assertIn("不得发起网络请求", prompt)

        workflow = (
            ROOT / ".gitcode/workflows/cannbot-knowledge_actions.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("MODEL: ${{ secrets.MODEL }}", workflow)

    def test_workflow_keeps_cann_contract_and_registered_runner_specs(self) -> None:
        workflow = (
            ROOT / ".gitcode/workflows/cannbot-knowledge_actions.yml"
        ).read_text(encoding="utf-8")
        self.assertTrue(workflow.startswith("name: PR-pipeline_cannbot-knowledge\n"))
        self.assertIn("SOURCE_BRANCH: ${{ atomgit.head_ref }}", workflow)
        self.assertIn(
            'obs_path: "${{ env.org_name }}/${{ env.repo_name }}/ci/package/'
            '${{ env.MERGE_ID }}"',
            workflow,
        )
        self.assertNotIn("vars.OBS_PATH", workflow)
        self.assertEqual(3, workflow.count("'arch=arm64', 'spec=large'"))
        self.assertNotIn("'arch=arm64', 'spec=small'", workflow)
        self.assertNotIn("'arch=arm64', 'spec=medium'", workflow)
        self.assertNotIn("'arch=arm64', 'spec=xlarge'", workflow)

    def test_zero_pages_and_automatic_limit_do_not_read_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            with mock.patch.dict(os.environ, {}, clear=True):
                empty = core.build_selection_plan([], self.settings, True)
                selected = [
                    f"knowledge/domain/concepts/{index:02}.md"
                    for index in range(self.settings.max_changed_pages + 1)
                ]
                skipped = core.build_selection_plan(selected, self.settings, True)
                with mock.patch.object(core, "_check_page") as check_page:
                    empty_output = repo / "empty.json"
                    skip_output = repo / "skip.json"
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            0,
                            core.run_content_check(
                                repo_root=repo,
                                plan=empty,
                                settings=self.settings,
                                checks=self.checks,
                                output=empty_output,
                            ),
                        )
                        self.assertEqual(
                            0,
                            core.run_content_check(
                                repo_root=repo,
                                plan=skipped,
                                settings=self.settings,
                                checks=self.checks,
                                output=skip_output,
                            ),
                        )
            check_page.assert_not_called()
            self.assertIsNotNone(json.loads(skip_output.read_text())["skip"])

    def test_missing_model_secret_is_a_non_retryable_page_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            page = "knowledge/domain/concepts/example.md"
            target = repo / page
            target.parent.mkdir(parents=True)
            target.write_text("# Example\n", encoding="utf-8")
            plan = core.build_selection_plan([page], self.settings, False)
            output = repo / "result.json"
            environment = {
                "BASE_URL": "https://provider.invalid",
                "AUTH_TOKEN": "token-sentinel",
            }
            with mock.patch.dict(os.environ, environment, clear=True):
                with redirect_stdout(io.StringIO()):
                    exit_code = core.run_content_check(
                        repo_root=repo,
                        plan=plan,
                        settings=self.settings,
                        checks=self.checks,
                        output=output,
                    )

            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(2, exit_code)
            self.assertEqual([], result["pages"])
            self.assertEqual([page], [error["path"] for error in result["errors"]])
            self.assertIn("MODEL", result["errors"][0]["message"])
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn(environment["AUTH_TOKEN"], serialized)
            self.assertNotIn(environment["BASE_URL"], serialized)

    def test_final_model_text_is_redacted(self) -> None:
        secret = "model-secret-sentinel"
        event = json.dumps(
            {
                "type": "text",
                "part": {"text": f'{{"result":"{secret}"}}'},
            }
        )
        result = opencode_runner.parse_events(event, redact=(secret,))
        self.assertNotIn(secret, result.text)
        self.assertIn("[redacted]", result.text)

    def test_summary_and_public_artifact_hide_model_metadata(self) -> None:
        plan = {
            "model": self.settings.model,
            "variant": self.settings.variant,
            "checks": [
                {"id": check.id, "title": check.title, "tier": check.tier}
                for check in self.checks
            ],
            "selected": [],
            "skip": None,
            "needs_model": False,
        }
        result = CI.result_from_plan(protocol.validate_plan(plan))
        summary = CI.render_summary(result, "", "")
        artifact = CI.public_result(result, ROOT)
        self.assertEqual(self.settings.model, result["model"])
        self.assertNotIn("模型：", summary)
        self.assertNotIn("variant：", summary)
        self.assertNotIn("MODEL", summary)
        self.assertEqual(
            {"checks", "pages", "errors", "skip", "runtime_error"}, set(artifact)
        )
        self.assertNotIn("model", artifact)
        self.assertNotIn("variant", artifact)
        self.assertNotIn("check_exit_code", artifact)

    def test_summary_omits_ci_meta_context(self) -> None:
        plan = protocol.validate_plan(
            {
                "model": self.settings.model,
                "variant": self.settings.variant,
                "checks": [
                    {"id": check.id, "title": check.title, "tier": check.tier}
                    for check in self.checks
                ],
                "selected": [],
                "skip": None,
                "needs_model": False,
            }
        )
        base = CI.result_from_plan(plan)
        skipped = {
            **base,
            "skip": {
                "reason": "changed_page_limit_exceeded",
                "limit": 1,
                "paths": [
                    "knowledge/ops/ascendc/apis/example_a.md",
                    "knowledge/ops/ascendc/apis/example_b.md",
                ],
            },
        }
        summaries = [
            CI.render_summary(base, "", "", ROOT),
            CI.render_summary(skipped, "", "", ROOT),
            CI.render_summary(
                CI.runtime_result(f"{ROOT}/network unavailable", plan), "", "", ROOT
            ),
        ]
        page = "knowledge/ops/ascendc/apis/example.md"
        results = {check["id"]: [] for check in plan["checks"]}
        results[plan["checks"][0]["id"]] = [
            {"msg": f"Finding {index}", "line": index + 1} for index in range(21)
        ]
        reviewed_result = {
            **base,
            "pages": [{"path": page, "results": results}],
        }
        summaries.append(CI.render_summary(reviewed_result, "", "", ROOT))
        errors = [
            {
                "path": f"knowledge/ops/ascendc/apis/error_{index}.md",
                "kind": "runner",
                "message": f"Error {index}",
            }
            for index in range(21)
        ]
        summaries.append(
            CI.render_summary(
                {**base, "check_exit_code": 2, "errors": errors}, "", "", ROOT
            )
        )
        for summary in summaries:
            self.assertNotIn("非阻断", summary)
            self.assertNotIn("门禁：", summary)
            self.assertNotIn("检查范围：", summary)
            self.assertNotIn("结果文件：", summary)
            self.assertNotIn("OBS 下载链接：", summary)
            self.assertNotIn("index.md", summary)
            self.assertNotIn("Summary", summary)
            self.assertNotIn("下载", summary)
            self.assertNotIn("仅显示前 20 条", summary)
            self.assertNotIn("模型：", summary)
            self.assertNotIn("variant：", summary)
            self.assertNotIn(str(ROOT), summary)
        self.assertEqual(21, summaries[-2].count("| P1 |"))
        self.assertIn("knowledge/ops/ascendc/apis/error_20.md", summaries[-1])

        public_page = CI.public_result(reviewed_result, ROOT)["pages"][0]
        self.assertEqual({"path", "results"}, set(public_page))
        public_error = CI.public_result(
            {**base, "check_exit_code": 2, "errors": errors}, ROOT
        )["errors"][0]
        self.assertEqual({"path", "message"}, set(public_error))
        self.assertEqual("检查进程失败", public_error["message"])
        self.assertEqual(
            {"limit", "paths"}, set(CI.public_result(skipped, ROOT)["skip"])
        )
        public_runtime = CI.public_result(
            CI.runtime_result(f"{ROOT}/network unavailable", plan), ROOT
        )["runtime_error"]
        self.assertEqual({"message"}, set(public_runtime))
        self.assertEqual("检查运行失败", public_runtime["message"])
        self.assertNotIn(str(ROOT), public_runtime["message"])

        page_error_cases = (
            ({"kind": "timeout", "message": "private"}, "检查超时"),
            ({"kind": "protocol", "message": "private"}, "检查结果无效"),
            (
                {"kind": "runner", "message": "缺少模型凭据环境变量: MODEL"},
                "模型配置不可用",
            ),
            ({"kind": "runner", "message": "HTTP 503: private"}, "模型请求失败"),
        )
        for error, expected in page_error_cases:
            with self.subTest(error=error):
                self.assertEqual(expected, CI.public_error_message(error))
        self.assertEqual(
            "变更页面选择失败",
            CI.public_runtime_message({"message": "ContentCheck 选页失败: private"}),
        )
        self.assertEqual(
            "检查结果验证失败",
            CI.public_runtime_message({"message": "result has invalid field"}),
        )

    def test_ci_adapter_validates_a_normal_result_once(self) -> None:
        plan = protocol.validate_plan(
            {
                "model": self.settings.model,
                "variant": self.settings.variant,
                "checks": [
                    {"id": check.id, "title": check.title, "tier": check.tier}
                    for check in self.checks
                ],
                "selected": [],
                "skip": None,
                "needs_model": False,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "content-check.json"
            args = SimpleNamespace(
                output=output,
                repo_root=Path(temporary),
                command="unused",
                source_repo="",
                source_sha="",
            )
            with mock.patch.object(CI, "create_plan", return_value=plan):
                with (
                    mock.patch.object(
                        CI,
                        "validate_ci_result",
                        wraps=protocol.validate_ci_result,
                    ) as validate,
                    redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(0, CI.run(args))
            artifact = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(1, validate.call_count)
        self.assertEqual(
            {"checks", "pages", "errors", "skip", "runtime_error"}, set(artifact)
        )

    def test_load_result_only_attaches_the_checker_exit_code(self) -> None:
        plan = protocol.validate_plan(
            {
                "model": self.settings.model,
                "variant": self.settings.variant,
                "checks": [
                    {"id": check.id, "title": check.title, "tier": check.tier}
                    for check in self.checks
                ],
                "selected": [],
                "skip": None,
                "needs_model": False,
            }
        )
        core_result = CI.result_from_plan(plan)
        core_result.pop("check_exit_code")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "core-result.json"
            path.write_text(json.dumps(core_result), encoding="utf-8")
            with mock.patch.object(CI, "validate_ci_result") as validate:
                envelope = CI.load_result(path, 0)
        validate.assert_not_called()
        self.assertEqual(0, envelope["check_exit_code"])

    def test_ci_adapter_validates_only_runtime_after_protocol_failure(self) -> None:
        plan = protocol.validate_plan(
            {
                "model": self.settings.model,
                "variant": self.settings.variant,
                "checks": [
                    {"id": check.id, "title": check.title, "tier": check.tier}
                    for check in self.checks
                ],
                "selected": [],
                "skip": None,
                "needs_model": False,
            }
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "content-check.json"
            args = SimpleNamespace(
                output=output,
                repo_root=Path(temporary),
                command="unused",
                source_repo="",
                source_sha="",
            )
            with mock.patch.object(CI, "create_plan", return_value=plan):
                with (
                    mock.patch.object(
                        CI,
                        "result_from_plan",
                        return_value={"invalid": True},
                    ),
                    mock.patch.object(
                        CI,
                        "validate_ci_result",
                        wraps=protocol.validate_ci_result,
                    ) as validate,
                    redirect_stdout(io.StringIO()),
                    redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(0, CI.run(args))
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(2, validate.call_count)
        self.assertEqual({"message"}, set(result["runtime_error"]))
        self.assertEqual([], result["errors"])

    def test_skill_workflow_is_nested_under_run(self) -> None:
        skill = (ROOT / ".agents/skills/knowledge-lint/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("\n### 工作流\n", skill)
        self.assertNotIn("\n## 工作流\n", skill)


if __name__ == "__main__":
    unittest.main()
