#!/usr/bin/env python3
"""Run changed-page ContentCheck and render an Actions summary."""

import argparse
import html
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote


CHECKER = ".agents/skills/knowledge-lint/scripts/content_check.py"
PROTOCOL_DIR = (
    Path(__file__).resolve().parents[2] / ".agents/skills/knowledge-lint/scripts"
)
sys.path.insert(0, str(PROTOCOL_DIR))

from content_protocol import (  # noqa: E402
    validate_ci_result,
    validate_plan,
)


PUBLIC_PAGE_ERRORS = {
    "timeout": "检查超时",
    "protocol": "检查结果无效",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--source-repo", default="")
    parser.add_argument("--source-sha", default="")
    return parser.parse_args()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def public_message(value, repo_root=None):
    message = str(value)
    if repo_root is None:
        return message
    root = str(repo_root.resolve())
    return message.replace(f"{root}/", "").replace(root, ".")


def public_error_message(error):
    if error["kind"] in PUBLIC_PAGE_ERRORS:
        return PUBLIC_PAGE_ERRORS[error["kind"]]
    message = str(error["message"])
    if "缺少模型凭据环境变量" in message:
        return "模型配置不可用"
    if "HTTP " in message or any(
        token in message.casefold()
        for token in ("network", "connect", "enotfound", "requesterror")
    ):
        return "模型请求失败"
    return "检查进程失败"


def public_runtime_message(error):
    message = str(error["message"])
    if "选页失败" in message:
        return "变更页面选择失败"
    if any(
        token in message.casefold()
        for token in ("protocol", "result", "invalid", "field")
    ):
        return "检查结果验证失败"
    return "检查运行失败"


def public_result(result, repo_root):
    skip = result["skip"]
    runtime_error = result["runtime_error"]
    return {
        "checks": result["checks"],
        "pages": [
            {
                "path": page["path"],
                "results": {
                    check_id: [
                        {
                            "msg": public_message(violation["msg"], repo_root),
                            "line": violation["line"],
                        }
                        for violation in violations
                    ]
                    for check_id, violations in page["results"].items()
                },
            }
            for page in result["pages"]
        ],
        "errors": [
            {
                "path": error["path"],
                "message": public_error_message(error),
            }
            for error in result["errors"]
        ],
        "skip": (
            None if skip is None else {"limit": skip["limit"], "paths": skip["paths"]}
        ),
        "runtime_error": (
            None
            if runtime_error is None
            else {"message": public_runtime_message(runtime_error)}
        ),
    }


def runtime_result(message, plan=None):
    return {
        "model": plan["model"] if plan is not None else None,
        "variant": plan["variant"] if plan is not None else None,
        "checks": plan["checks"] if plan is not None else [],
        "pages": [],
        "errors": [],
        "skip": None,
        "runtime_error": {"kind": "runtime", "message": message},
        "check_exit_code": 2,
    }


def relay(completed):
    for stream in (completed.stdout, completed.stderr):
        if stream:
            print(stream, end="" if stream.endswith("\n") else "\n", file=sys.stderr)


def changed_files(repo_root):
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            "HEAD^1",
            "HEAD",
            "--",
            "knowledge/",
        ],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = next(
            (line.strip() for line in completed.stderr.splitlines() if line.strip()),
            "无法读取 PR 变更页面",
        )
        raise RuntimeError(detail)
    return completed.stdout


def load_plan(path):
    return validate_plan(json.loads(path.read_text(encoding="utf-8")))


def create_plan(repo_root, output):
    completed = subprocess.run(
        [
            sys.executable,
            CHECKER,
            "--repo-root",
            str(repo_root),
            "--changed-files",
            "-",
            "--plan-only",
            str(output),
        ],
        cwd=repo_root,
        input=changed_files(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    relay(completed)
    if completed.returncode != 0:
        detail = next(
            (
                line.strip()
                for line in reversed(completed.stderr.splitlines())
                if line.strip()
            ),
            "未知错误",
        )
        raise RuntimeError(f"ContentCheck 选页失败：{detail}")
    return load_plan(output)


def run_checker(repo_root, plan, command, output):
    process = subprocess.Popen(
        [
            sys.executable,
            CHECKER,
            "--repo-root",
            str(repo_root),
            "--pages",
            *plan["selected"],
            "--command",
            command,
            "--output",
            str(output),
        ],
        cwd=repo_root,
        stdout=sys.stderr,
        start_new_session=True,
    )
    try:
        return process.wait()
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except OSError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass
            process.wait()
        raise


def result_from_plan(plan):
    return {
        "model": plan["model"],
        "variant": plan["variant"],
        "checks": plan["checks"],
        "pages": [],
        "errors": [],
        "skip": plan["skip"],
        "runtime_error": None,
        "check_exit_code": 0,
    }


def load_result(path, checker_exit):
    return {
        **json.loads(path.read_text(encoding="utf-8")),
        "check_exit_code": checker_exit,
    }


def escape_cell(value):
    return html.escape(str(value)).replace("|", "\\|").replace("\n", "<br>")


def source_link(path, line, source_repo, source_sha):
    label = escape_cell(f"{path}:{line}" if isinstance(line, int) else path)
    label = label.replace("[", "\\[").replace("]", "\\]")
    if not source_repo or not source_sha or path in ("", "."):
        return label
    url = f"https://gitcode.com/{source_repo}/blob/{source_sha}/{quote(path, safe='/')}"
    if isinstance(line, int):
        url = f"{url}#L{line}"
    return f"[{label}]({url})"


def collect_findings(result):
    rules = {rule["id"]: rule for rule in result["checks"]}
    findings = []
    for page in result["pages"]:
        for check_id, violations in page["results"].items():
            rule = rules[check_id]
            for violation in violations:
                findings.append(
                    {
                        "id": check_id,
                        "title": rule["title"],
                        "tier": rule["tier"],
                        "path": page["path"],
                        "line": violation["line"],
                        "message": violation["msg"],
                    }
                )
    tier_order = {"P0": 0, "P1": 1, "P2": 2}
    return sorted(
        findings,
        key=lambda finding: (
            tier_order[finding["tier"]],
            finding["path"],
            finding["line"] is None,
            finding["line"] or 0,
            finding["id"],
            finding["message"],
        ),
    )


def render_summary(result, source_repo, source_sha, repo_root=None):
    exit_code = result["check_exit_code"]
    skip = result["skip"]
    if skip is not None:
        selected = len(skip["paths"])
        lines = [
            "## ContentCheck · ⏭️ 已跳过",
            "",
            f"- 原因：待检查 `{selected}` 页，超过自动检查上限 `{skip['limit']}` 页",
            f"- 已检查：`0` 页；已跳过：`{selected}` 页；未完成：`0` 页",
            "- Findings：`0`（P0 `0` · P1 `0` · P2 `0`）",
        ]
    else:
        findings = collect_findings(result)
        counts = {
            tier: sum(finding["tier"] == tier for finding in findings)
            for tier in ("P0", "P1", "P2")
        }
        if result["runtime_error"] is not None:
            outcome = "⚠️ 运行失败"
        elif exit_code == 2:
            outcome = "⚠️ 检查未完成"
        elif exit_code == 1:
            outcome = "⚠️ 发现 P0"
        elif not result["pages"]:
            outcome = "⏭️ 无可检查的变更知识卡"
        else:
            outcome = "✅ 已完成"
        lines = [
            f"## ContentCheck · {outcome}",
            "",
            f"- 已检查：`{len(result['pages'])}` 页；未完成：`{len(result['errors'])}` 页",
            f"- Findings：`{len(findings)}`（P0 `{counts['P0']}` · P1 `{counts['P1']}` · P2 `{counts['P2']}`）",
        ]
        if findings:
            lines.extend(["", "| 等级 | 检查 | 文件 | 说明 |", "|---|---|---|---|"])
            for finding in findings:
                location = source_link(
                    finding["path"], finding["line"], source_repo, source_sha
                )
                lines.append(
                    f"| {escape_cell(finding['tier'])} | "
                    f"`{escape_cell(finding['id'])}` {escape_cell(finding['title'])} | "
                    f"{location} | "
                    f"{escape_cell(public_message(finding['message'], repo_root))} |"
                )
        if result["errors"]:
            lines.extend(["", "### 未完成页面", "", "| 页面 | 原因 |", "|---|---|"])
            for error in result["errors"]:
                location = source_link(error["path"], None, source_repo, source_sha)
                lines.append(f"| {location} | {public_error_message(error)} |")
        if result["runtime_error"] is not None:
            lines.extend(
                [
                    "",
                    "### 运行错误",
                    "",
                    f"- 原因：{public_runtime_message(result['runtime_error'])}",
                ]
            )
    return "\n".join(lines) + "\n"


def run(args):
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    plan_value = None
    repo_root = args.repo_root.resolve()
    try:
        with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
            plan_value = create_plan(repo_root, Path(temporary) / "plan.json")
        if not plan_value["needs_model"]:
            result = result_from_plan(plan_value)
        else:
            checker_exit = run_checker(
                repo_root,
                plan_value,
                args.command,
                output,
            )
            result = load_result(output, checker_exit)
        result = validate_ci_result(result, plan=plan_value, repo_root=repo_root)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        message = str(exc) or type(exc).__name__
        print(f"ContentCheck: {message}", file=sys.stderr)
        result = validate_ci_result(
            runtime_result(message, plan_value),
            plan=plan_value,
            repo_root=repo_root,
        )
    write_json(output, public_result(result, repo_root))
    print(
        render_summary(
            result,
            args.source_repo,
            args.source_sha,
            repo_root,
        ),
        end="",
    )
    return 0


def main():
    args = parse_args()
    return run(args)


def _interrupt_on_terminate(_signum, _frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _interrupt_on_terminate)
    raise SystemExit(main())
