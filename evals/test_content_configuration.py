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
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
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

    def test_model_uses_a_public_alias_and_cannbot_gateway(self) -> None:
        self.assertEqual("content-review/content-check", self.settings.model)
        self.assertEqual(
            ("BASE_URL", "AUTH_TOKEN", "CANNBOT_VKEY"),
            self.settings.model_env,
        )

        config = json.loads(OPENCODE_CONFIG.read_text(encoding="utf-8"))
        provider = config["provider"]["content-review"]
        self.assertEqual("@ai-sdk/openai-compatible", provider["npm"])
        self.assertEqual("{env:BASE_URL}", provider["options"]["baseURL"])
        self.assertEqual("{env:AUTH_TOKEN}", provider["options"]["apiKey"])
        self.assertEqual(
            "{env:CANNBOT_VKEY}", provider["options"]["headers"]["x-api-vkey"]
        )
        model = provider["models"]["content-check"]
        self.assertEqual("{env:CONTENT_CHECK_MODEL_ID}", model["id"])
        self.assertEqual(
            self.settings.variant,
            model["variants"][self.settings.variant]["reasoningEffort"],
        )
        self.assertNotIn("limit", model)
        self.assertEqual("deny", config["permission"]["webfetch"])
        prompt = (
            ROOT / ".agents/skills/knowledge-lint/references/content_check_prompt.md"
        ).read_text(encoding="utf-8")
        self.assertIn("不得发起网络请求", prompt)

        workflow = (
            ROOT / ".gitcode/workflows/cannbot-knowledge_actions.yml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("MODEL: ${{ secrets.MODEL }}", workflow)
        self.assertIn("CANNBOT_VKEY: ${{ secrets.CANNBOT_VKEY }}", workflow)
        with tempfile.TemporaryDirectory() as temporary:
            credentials = {
                "BASE_URL": "https://provider.invalid/v1",
                "AUTH_TOKEN": "token-sentinel",
                "CANNBOT_VKEY": "vkey-sentinel",
            }
            with mock.patch.dict(os.environ, credentials, clear=True):
                env = opencode_runner.build_env(
                    opencode_config=self.settings.opencode_config,
                    model_id="alternate-model-id",
                    model_env=self.settings.model_env,
                    state_root=Path(temporary),
                )
            self.assertEqual("alternate-model-id", env["CONTENT_CHECK_MODEL_ID"])
            self.assertNotIn("MODEL", env)

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
                    f"knowledge/domain/concepts/{index:03}.md"
                    for index in range(self.settings.max_changed_pages + 1)
                ]
                skipped = core.build_selection_plan(selected, self.settings, True)
                at_limit = core.build_selection_plan(selected[:-1], self.settings, True)
                self.assertTrue(at_limit.needs_model)
                self.assertIsNone(at_limit.skip)
                self.assertTrue(
                    core.build_selection_plan(
                        selected, self.settings, False
                    ).needs_model
                )
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

    def test_missing_gateway_vkey_is_a_non_retryable_page_error(self) -> None:
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
            self.assertIn("CANNBOT_VKEY", result["errors"][0]["message"])
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn(environment["AUTH_TOKEN"], serialized)
            self.assertNotIn(environment["BASE_URL"], serialized)

    def test_usage_includes_retries_failed_pages_and_marks_missing_counters(
        self,
    ) -> None:
        good = json.dumps({check.id: [] for check in self.checks})

        def response(text, count, complete=True):
            usage = dict.fromkeys(protocol.USAGE_KEYS, 0)
            usage["input"] = count
            return opencode_runner.OpenCodeResult(text, usage, complete)

        cases = (
            ([response("bad JSON", 100), response(good, 7)], 0, 107, 0),
            ([response("bad JSON", 100), response("bad JSON", 7)], 2, 107, 0),
            ([response(good, 0, False)], 0, 0, 1),
            ([opencode_runner.OpenCodeRuntimeError("HTTP 403")], 2, 0, 1),
            (
                [
                    opencode_runner.OpenCodeRuntimeError(
                        "HTTP 403", usage=response(good, 9).usage
                    )
                ],
                2,
                9,
                1,
            ),
        )
        for responses, expected_exit, tokens, incomplete in cases:
            with self.subTest(tokens=tokens, incomplete=incomplete, exit=expected_exit):
                with tempfile.TemporaryDirectory() as temporary:
                    repo = Path(temporary)
                    page = "knowledge/ops/ascendc/apis/example.md"
                    target = repo / page
                    target.parent.mkdir(parents=True)
                    target.write_text("# Example\n", encoding="utf-8")
                    output = repo / "result.json"
                    log = io.StringIO()
                    with (
                        mock.patch.object(core, "run_opencode", side_effect=responses),
                        redirect_stdout(log),
                    ):
                        exit_code = core.run_content_check(
                            repo_root=repo,
                            plan=core.build_selection_plan([page], self.settings, True),
                            settings=replace(self.settings, max_attempts=2),
                            checks=self.checks,
                            output=output,
                        )
                    self.assertEqual(expected_exit, exit_code)
                    total = next(
                        line
                        for line in log.getvalue().splitlines()
                        if line.startswith("ContentCheck: finished")
                    )
                    self.assertIn(f"tokens_input={tokens} ", total)
                    self.assertIn("elapsed_s=", total)
                    self.assertIn(f"incomplete_attempts={incomplete} ", total)
                    self.assertIn(
                        f"usage_complete={str(incomplete == 0).lower()} ", total
                    )
                    pages = json.loads(output.read_text())["pages"]
                    if pages:
                        self.assertEqual(tokens, pages[0]["usage"]["input"])

    def test_token_counters_keep_integer_precision(self) -> None:
        for count in (1_234_567, 2**53 + 1):
            with self.subTest(count=count):
                events = [
                    {"type": "step_finish", "part": {"tokens": {"input": count}}},
                    {"type": "text", "part": {"text": "{}"}},
                ]
                result = opencode_runner.parse_events(
                    "\n".join(map(json.dumps, events))
                )
                self.assertEqual(count, result.usage["input"])
                self.assertIn(f"tokens_input={count} ", core._usage_log(result.usage))

    def test_provider_errors_hide_raw_details_and_keep_partial_usage(self) -> None:
        events = [
            {"type": "step_finish", "part": {"tokens": {"input": 23}}},
            {
                "type": "error",
                "error": {
                    "name": "private-provider-name",
                    "data": {"statusCode": 429, "message": "private-provider-detail"},
                },
            },
        ]
        with self.assertRaises(opencode_runner.OpenCodeRuntimeError) as raised:
            opencode_runner.parse_events("\n".join(map(json.dumps, events)))
        self.assertEqual("OpenCode 请求失败 (HTTP 429)", str(raised.exception))
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(23, raised.exception.usage["input"])

    def test_cli_failure_keeps_partial_usage_without_stderr(self) -> None:
        event = json.dumps({"type": "step_finish", "part": {"tokens": {"input": 19}}})
        for tail, expected_error, timeout in (
            ("sys.exit(7)", opencode_runner.OpenCodeRuntimeError, 10),
            ("time.sleep(30)", opencode_runner.OpenCodeTimeout, 3),
        ):
            with self.subTest(error=expected_error.__name__):
                with tempfile.TemporaryDirectory() as temporary:
                    repo = Path(temporary)
                    executable = repo / "fake-opencode"
                    executable.write_text(
                        f"#!{sys.executable}\nimport sys, time\n"
                        f"print({event!r}, flush=True)\n"
                        "print('private-stderr-detail', file=sys.stderr, flush=True)\n"
                        f"{tail}\n",
                        encoding="utf-8",
                    )
                    executable.chmod(0o755)
                    with self.assertRaises(expected_error) as raised:
                        opencode_runner.run_opencode(
                            command=str(executable),
                            repo_root=repo,
                            page="knowledge/example.md",
                            prompt="check",
                            model=self.settings.model,
                            model_id=self.settings.model_id,
                            variant=self.settings.variant,
                            timeout_s=timeout,
                            model_env=(),
                            opencode_config=self.settings.opencode_config,
                        )
                    self.assertNotIn("private-stderr-detail", str(raised.exception))
                    self.assertEqual(19, raised.exception.usage["input"])

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

        results = {check.id: [] for check in self.checks}
        results[self.checks[0].id] = [{"msg": secret, "line": 1}]
        response = opencode_runner.OpenCodeResult(
            json.dumps(results).replace(secret, r"\u006dodel-secret-sentinel"),
            dict.fromkeys(protocol.USAGE_KEYS, 0),
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            page = "knowledge/ops/ascendc/apis/example.md"
            target = repo / page
            target.parent.mkdir(parents=True)
            target.write_text("# Example\n", encoding="utf-8")
            output = repo / "result.json"
            log = io.StringIO()
            with (
                mock.patch.dict(os.environ, {"AUTH_TOKEN": secret}),
                mock.patch.object(core, "run_opencode", return_value=response),
                redirect_stdout(log),
            ):
                core.run_content_check(
                    repo_root=repo,
                    plan=core.build_selection_plan([page], self.settings, True),
                    settings=self.settings,
                    checks=self.checks,
                    output=output,
                )
            self.assertNotIn(secret, log.getvalue() + output.read_text())
            self.assertIn("[redacted]", log.getvalue())

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
