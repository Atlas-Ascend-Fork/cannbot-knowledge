#!/usr/bin/env python3
"""Run FormatCheck and render its GitCode Actions summary."""

import argparse
import html
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote


RUNTIME_MESSAGE = "FormatCheck 未生成有效结果。"
OUTCOMES = {
    0: "✅ 通过",
    1: "❌ 未通过",
    2: "⚠️ 运行失败",
}
CHECKER = ".agents/skills/knowledge-lint/scripts/knowledge_lint.py"
FINDING_KEYS = {
    "check",
    "tier",
    "path",
    "line",
    "code",
    "message",
    "details",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-repo", default="")
    parser.add_argument("--source-sha", default="")
    return parser.parse_args()


def run_linter(repo_root, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        completed = subprocess.run(
            [
                sys.executable,
                CHECKER,
                "--knowledge-root",
                str(repo_root),
                "--strict-navigation",
                "--json",
            ],
            cwd=repo_root,
            stdout=stream,
            check=False,
        )
    return completed.returncode


def runtime_result(repo_root):
    return {
        "root": str(repo_root),
        "checked": 0,
        "findings": [
            {
                "check": "format",
                "tier": None,
                "path": ".",
                "line": None,
                "code": "format.runtime",
                "message": RUNTIME_MESSAGE,
                "details": None,
            }
        ],
    }


def load_result(path, repo_root, checker_exit):
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(result, dict)
            or set(result) != {"root", "checked", "findings"}
            or not isinstance(result["root"], str)
            or not result["root"]
            or Path(result["root"]).resolve() != repo_root.resolve()
            or isinstance(result["checked"], bool)
            or not isinstance(result["checked"], int)
            or result["checked"] < 0
            or not isinstance(result["findings"], list)
        ):
            raise ValueError
        for finding in result["findings"]:
            if (
                not isinstance(finding, dict)
                or set(finding) != FINDING_KEYS
                or not isinstance(finding["tier"], str)
                or finding["tier"] not in {"P0", "P1", "P2"}
                or not all(
                    isinstance(finding[key], str) and finding[key]
                    for key in ("check", "path", "code", "message")
                )
                or (
                    finding["line"] is not None
                    and (
                        isinstance(finding["line"], bool)
                        or not isinstance(finding["line"], int)
                        or finding["line"] < 1
                    )
                )
                or (
                    finding["details"] is not None
                    and not isinstance(finding["details"], str)
                )
            ):
                raise ValueError
        result["findings"].sort(
            key=lambda finding: (
                {"P0": 0, "P1": 1, "P2": 2}[finding["tier"]],
                finding["path"],
                finding["line"] or 0,
                finding["check"],
                finding["code"],
                finding["message"],
                finding["details"] or "",
            )
        )
        expected_exit = 1 if any(
            finding["tier"] == "P0" for finding in result["findings"]
        ) else 0
        if checker_exit != expected_exit:
            raise ValueError
    except (OSError, UnicodeDecodeError, ValueError):
        result = runtime_result(repo_root)
        return result, 2
    return result, checker_exit


def write_result(path, result):
    result = {**result, "root": "."}
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def escape_cell(value):
    return html.escape(str(value)).replace("|", "\\|").replace("\n", "<br>")


def render_summary(result, exit_code, source_repo, source_sha):
    findings = result["findings"]
    counts = {
        tier: sum(finding.get("tier") == tier for finding in findings)
        for tier in ("P0", "P1", "P2")
    }
    lines = [
        f"## FormatCheck · {OUTCOMES[exit_code]}",
        "",
        f"- 已检查：`{result.get('checked', 0)}` 个 Markdown",
        f"- Findings：`{len(findings)}`（P0 `{counts['P0']}` · P1 `{counts['P1']}` · P2 `{counts['P2']}`）",
    ]
    if findings:
        lines.extend(["", "| 等级 | 检查 | 文件 | 说明 |", "|---|---|---|---|"])
        for finding in findings:
            path = str(finding.get("path", ""))
            line = finding.get("line")
            location = f"{path}:{line}" if isinstance(line, int) else path
            label = escape_cell(location).replace("[", "\\[").replace("]", "\\]")
            if source_repo and source_sha and path not in ("", "."):
                url = f"https://gitcode.com/{source_repo}/blob/{source_sha}/{quote(path, safe='/')}"
                if isinstance(line, int):
                    url = f"{url}#L{line}"
                label = f"[{label}]({url})"
            rule = f"{finding.get('check', '')}/{finding.get('code', '')}"
            explanation = escape_cell(finding.get("message", ""))
            if finding.get("details") is not None:
                explanation += f"<br>详情：{escape_cell(finding['details'])}"
            lines.append(
                f"| {escape_cell(finding.get('tier') or '—')} | `{escape_cell(rule)}` | "
                f"{label} | {explanation} |"
            )
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output.resolve()
    checker_exit = run_linter(repo_root, output)
    result, exit_code = load_result(output, repo_root, checker_exit)
    write_result(output, result)
    print(
        render_summary(
            result,
            exit_code,
            args.source_repo,
            args.source_sha,
        ),
        end="",
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
