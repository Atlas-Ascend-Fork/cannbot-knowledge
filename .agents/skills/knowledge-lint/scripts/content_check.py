#!/usr/bin/env python3
"""Changed-page semantic checks powered by one OpenCode session per page."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import re
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib

from content_protocol import (
    ContentProtocolError,
    USAGE_KEYS,
    expected_exit_code,
    validate_page_results,
    validate_plan,
    validate_result,
)
from opencode_runner import OpenCodeError, ProcessRegistry, redact_text, run_opencode


HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_CONFIG = SKILL_ROOT / "references/content_check.toml"
DEFAULT_REPO_ROOT = HERE.parents[3]


@dataclass(frozen=True)
class CheckRule:
    id: str
    title: str
    details: str
    tier: str


@dataclass(frozen=True)
class Settings:
    command: str
    model: str
    model_id: str
    variant: str
    max_concurrency: int
    timeout_s: float
    max_attempts: int
    max_changed_pages: int
    progress_interval_s: float
    model_env: tuple[str, ...]
    prompt: str
    opencode_config: str


@dataclass(frozen=True)
class SelectionPlan:
    selected: list[str]
    skip: dict[str, object] | None
    needs_model: bool


class PageProtocolError(RuntimeError):
    kind = "protocol"
    retryable = True


class UsageTotals:
    """Accumulate reported usage from every attempt, including failed pages."""

    def __init__(self) -> None:
        self.tokens: dict[str, int | float] = dict.fromkeys(USAGE_KEYS, 0)
        self.incomplete_attempts = 0
        self._lock = threading.Lock()

    def record(self, usage: dict[str, int | float] | None, complete: bool) -> None:
        with self._lock:
            if usage is not None:
                for key in USAGE_KEYS:
                    self.tokens[key] += usage[key]
            if not complete:
                self.incomplete_attempts += 1


_CHECK_ID_RE = re.compile(r"[a-z][a-z0-9_]*\Z")
_ENV_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} 必须是 object")
    return value


def _exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} 字段不完整或包含未知字段")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 必须是非空字符串")
    return value.strip()


def _positive_number(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value <= 0
        or (isinstance(value, float) and not math.isfinite(value))
    ):
        raise ValueError(f"{label} 必须是有限正数")
    return float(value)


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} 必须是正整数")
    return value


def load_config(
    path: Path, command_override: str | None = None
) -> tuple[Settings, list[CheckRule]]:
    data = _mapping(tomllib.loads(path.read_text(encoding="utf-8")), "配置")
    _exact_keys(data, {"runner", "checks"}, "配置")
    runner = _mapping(data["runner"], "runner")
    _exact_keys(
        runner,
        {
            "command",
            "model",
            "model_id",
            "variant",
            "model_env",
            "max_concurrency",
            "timeout_s",
            "max_attempts",
            "max_changed_pages",
            "progress_interval_s",
            "prompt",
            "opencode_config",
        },
        "runner",
    )
    raw_checks = data["checks"]
    if not isinstance(raw_checks, list):
        raise ValueError("checks 必须是数组")
    checks: list[CheckRule] = []
    configured_ids: list[str] = []
    for index, raw in enumerate(raw_checks):
        item = _mapping(raw, f"checks[{index}]")
        _exact_keys(
            item,
            {"id", "title", "details", "tier", "enabled"},
            f"checks[{index}]",
        )
        if not isinstance(item["enabled"], bool):
            raise ValueError(f"checks[{index}].enabled 必须是 boolean")
        check_id = _text(item["id"], f"checks[{index}].id")
        if not _CHECK_ID_RE.fullmatch(check_id):
            raise ValueError(f"checks[{index}].id 必须使用小写 snake_case")
        configured_ids.append(check_id)
        check = CheckRule(
            id=check_id,
            title=_text(item["title"], f"checks[{index}].title"),
            details=_text(item["details"], f"checks[{index}].details"),
            tier=_text(item["tier"], f"checks[{index}].tier"),
        )
        if check.tier not in {"P0", "P1", "P2"}:
            raise ValueError("ContentCheck tier 只能是 P0、P1 或 P2")
        if item["enabled"]:
            checks.append(check)
    if not checks:
        raise ValueError("ContentCheck 至少需要一个启用检查项")
    if len(configured_ids) != len(set(configured_ids)):
        raise ValueError("ContentCheck 检查 id 重复")
    max_concurrency = _positive_int(runner["max_concurrency"], "max_concurrency")
    timeout_s = _positive_number(runner["timeout_s"], "timeout_s")
    max_attempts = _positive_int(runner["max_attempts"], "max_attempts")
    max_changed_pages = _positive_int(runner["max_changed_pages"], "max_changed_pages")
    progress_interval_s = _positive_number(
        runner["progress_interval_s"], "progress_interval_s"
    )
    if progress_interval_s > timeout_s:
        raise ValueError("progress_interval_s 不能大于 timeout_s")
    model_env = runner["model_env"]
    if not isinstance(model_env, list) or not all(
        isinstance(name, str) and _ENV_NAME_RE.fullmatch(name) for name in model_env
    ):
        raise ValueError("model_env 必须是合法环境变量名数组")
    if len(model_env) != len(set(model_env)):
        raise ValueError("model_env 不能包含重复项")

    base = path.parent
    prompt_path = base / _text(runner["prompt"], "prompt")
    opencode_config_path = base / _text(runner["opencode_config"], "opencode_config")
    prompt = prompt_path.read_text(encoding="utf-8")
    opencode_config = opencode_config_path.read_text(encoding="utf-8")
    if not prompt.strip():
        raise ValueError("ContentCheck prompt 不能为空")
    if not isinstance(json.loads(opencode_config), dict):
        raise ValueError("OpenCode 配置必须是 JSON object")
    command = command_override if command_override is not None else runner["command"]
    settings = Settings(
        command=_text(command, "command"),
        model=_text(runner["model"], "model"),
        model_id=_text(runner["model_id"], "model_id"),
        variant=_text(runner["variant"], "variant"),
        max_concurrency=max_concurrency,
        timeout_s=timeout_s,
        max_attempts=max_attempts,
        max_changed_pages=max_changed_pages,
        progress_interval_s=progress_interval_s,
        model_env=tuple(model_env),
        prompt=prompt,
        opencode_config=opencode_config,
    )
    return settings, checks


def _normalize_page(repo_root: Path, raw: str) -> str | None:
    path = Path(raw.strip())
    if path.is_absolute():
        try:
            path = path.relative_to(repo_root)
        except ValueError:
            return None
    if (
        not path.parts
        or path.parts[0] != "knowledge"
        or ".." in path.parts
        or path.suffix != ".md"
        or path.name == "index.md"
    ):
        return None

    candidate = repo_root / path
    return path.as_posix() if candidate.is_file() else None


def select_pages(repo_root: Path, changed_files: list[str]) -> list[str]:
    repo_root = repo_root.resolve()
    return sorted(
        {
            page
            for raw in changed_files
            if (page := _normalize_page(repo_root, raw)) is not None
        }
    )


def build_selection_plan(
    selected: list[str], settings: Settings, auto_selected: bool
) -> SelectionPlan:
    skip = None
    if auto_selected and len(selected) > settings.max_changed_pages:
        skip = {
            "reason": "changed_page_limit_exceeded",
            "limit": settings.max_changed_pages,
            "paths": selected,
        }
    return SelectionPlan(
        selected=selected,
        skip=skip,
        needs_model=bool(selected) and skip is None,
    )


def _check_manifest(checks: list[CheckRule]) -> list[dict[str, str]]:
    return [
        {"id": check.id, "title": check.title, "tier": check.tier} for check in checks
    ]


def _plan_value(
    plan: SelectionPlan,
    settings: Settings,
    checks: list[CheckRule],
) -> dict[str, object]:
    return validate_plan(
        {
            "model": settings.model,
            "variant": settings.variant,
            "checks": _check_manifest(checks),
            "selected": plan.selected,
            "skip": plan.skip,
            "needs_model": plan.needs_model,
        }
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_selection_plan(
    path: Path,
    plan: SelectionPlan,
    settings: Settings,
    checks: list[CheckRule],
) -> None:
    _write_json(path, _plan_value(plan, settings, checks))


def build_prompt(instructions: str, page: str, checks: list[CheckRule]) -> str:
    rules = {
        check.id: {"title": check.title, "details": check.details} for check in checks
    }
    return (
        f"{instructions.rstrip()}\n\n"
        f"## 本次焦点卡\n\n`{page}`\n\n"
        "## 本次检查项\n\n"
        f"{json.dumps(rules, ensure_ascii=False, indent=2)}\n"
    )


def decode_page_output(text: str) -> object:
    """Decode a bare JSON response or the final JSON paragraph from OpenCode."""
    candidates = [text]
    fenced = text.rsplit("```", 2)
    if len(fenced) == 3:
        candidate = fenced[1].lstrip()
        candidates.append(
            candidate[4:].lstrip() if candidate.startswith("json") else candidate
        )
    start = text.rfind("\n{")
    if start >= 0:
        candidates.append(text[start + 1 :])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise PageProtocolError("页面最终输出不是合法 JSON") from None


def _check_page(
    repo_root: Path,
    page: str,
    settings: Settings,
    checks: list[CheckRule],
    processes: ProcessRegistry,
    metrics: UsageTotals,
) -> dict[str, object]:
    prompt = build_prompt(settings.prompt, page, checks)
    started = time.monotonic()
    page_usage: dict[str, int | float] = dict.fromkeys(USAGE_KEYS, 0)
    for attempt in range(settings.max_attempts):
        attempt_started = time.monotonic()
        response = None
        failure = None
        print(
            f"ContentCheck: started {page} "
            f"attempt={attempt + 1}/{settings.max_attempts}",
            flush=True,
        )
        try:
            response = run_opencode(
                command=settings.command,
                repo_root=repo_root,
                page=page,
                prompt=prompt,
                model=settings.model,
                model_id=settings.model_id,
                variant=settings.variant,
                timeout_s=settings.timeout_s,
                model_env=settings.model_env,
                opencode_config=settings.opencode_config,
                processes=processes,
            )
            value = decode_page_output(response.text)
            try:
                results = validate_page_results(
                    value,
                    [check.id for check in checks],
                    line_count=len(
                        (repo_root / page).read_text(encoding="utf-8").splitlines()
                    ),
                )
            except ContentProtocolError as exc:
                raise PageProtocolError(str(exc)) from exc
            for violations in results.values():
                for violation in violations:
                    violation["msg"] = redact_text(
                        str(violation["msg"]),
                        tuple(os.environ.get(name, "") for name in settings.model_env),
                    )
        except (OpenCodeError, PageProtocolError) as exc:
            failure = exc
        usage = (
            response.usage if response is not None else getattr(failure, "usage", None)
        )
        complete = response.usage_complete if response is not None else False
        metrics.record(usage, complete)
        if usage is not None:
            for key in USAGE_KEYS:
                page_usage[key] += usage[key]
        print(
            f"ContentCheck: attempt {attempt + 1} {page} "
            f"elapsed_s={time.monotonic() - attempt_started:.3f} "
            f"usage_complete={str(complete).lower()} "
            f"{_usage_log(usage) if usage is not None else 'tokens=unavailable'}",
            flush=True,
        )
        if failure is None:
            return {
                "path": page,
                "results": results,
                "usage": page_usage,
                "elapsed_s": round(time.monotonic() - started, 3),
            }
        if not failure.retryable or attempt + 1 == settings.max_attempts:
            raise failure
        print(f"ContentCheck: retrying {page} reason={failure.kind}", flush=True)
    raise AssertionError("unreachable")


def _print_results(
    pages: list[dict[str, object]],
    errors: list[dict[str, str]],
    checks: list[CheckRule],
) -> int:
    counts = {"P0": 0, "P1": 0, "P2": 0}
    by_path = {str(page["path"]): page for page in pages}
    for check in checks:
        for path in sorted(by_path):
            page = by_path[path]
            results = cast(dict[str, list[dict[str, object]]], page["results"])
            for violation in results.get(check.id, []):
                counts[check.tier] += 1
                line = violation["line"]
                location = f"{path}:{line}" if line is not None else path
                print(f"[{check.tier}] {check.title}\n{location}\n{violation['msg']}\n")

    total = sum(counts.values())
    print(
        "ContentCheck: "
        f"pages={len(pages) + len(errors)}, violations={total}, "
        f"P0={counts['P0']}, P1={counts['P1']}, P2={counts['P2']}, "
        f"errors={len(errors)}"
    )
    if errors:
        return 2
    return 1 if counts["P0"] else 0


def _usage_log(usage: dict[str, int | float]) -> str:
    return " ".join(
        f"tokens_{key}={int(value) if isinstance(value, float) and value.is_integer() else value}"
        for key, value in usage.items()
    )


def run_content_check(
    *,
    repo_root: Path,
    plan: SelectionPlan,
    settings: Settings,
    checks: list[CheckRule],
    output: Path,
) -> int:
    pages: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    if plan.needs_model:
        metrics = UsageTotals()
        workers = min(settings.max_concurrency, len(plan.selected))
        processes = ProcessRegistry()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        started = time.monotonic()
        pending: dict[concurrent.futures.Future[dict[str, object]], str] = {}
        print(
            f"ContentCheck: start selected={len(plan.selected)} workers={workers}",
            flush=True,
        )
        try:
            pending = {
                executor.submit(
                    _check_page, repo_root, page, settings, checks, processes, metrics
                ): page
                for page in plan.selected
            }
            while pending:
                done, _ = concurrent.futures.wait(
                    pending,
                    timeout=settings.progress_interval_s,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                if not done:
                    completed = len(pages) + len(errors)
                    print(
                        "ContentCheck: progress "
                        f"completed={completed}/{len(plan.selected)} "
                        f"running={min(workers, len(pending))} "
                        f"elapsed_s={time.monotonic() - started:.1f}",
                        flush=True,
                    )
                    continue
                for future in sorted(done, key=lambda item: pending[item]):
                    page = pending.pop(future)
                    try:
                        result = future.result()
                    except Exception as exc:
                        errors.append(
                            {
                                "path": page,
                                "kind": str(getattr(exc, "kind", "runner")),
                                "message": str(exc) or type(exc).__name__,
                            }
                        )
                        print(
                            f"ContentCheck: failed {page}: {errors[-1]['message']}",
                            flush=True,
                        )
                    else:
                        pages.append(result)
                        print(
                            f"ContentCheck: completed {page} "
                            f"elapsed_s={result['elapsed_s']}",
                            flush=True,
                        )
        except BaseException:
            processes.stop_all()
            for future in pending:
                future.cancel()
            executor.shutdown(wait=True, cancel_futures=True)
            print("ContentCheck: interrupted", file=sys.stderr, flush=True)
            raise
        else:
            executor.shutdown(wait=True)
        finally:
            print(
                f"ContentCheck: finished completed={len(pages)} "
                f"errors={len(errors)} elapsed_s={time.monotonic() - started:.3f} "
                f"usage_complete={str(metrics.incomplete_attempts == 0).lower()} "
                f"incomplete_attempts={metrics.incomplete_attempts} "
                f"{_usage_log(metrics.tokens)}",
                flush=True,
            )

    pages.sort(key=lambda page: str(page["path"]))
    errors.sort(key=lambda error: error["path"])
    artifact = validate_result(
        {
            "model": settings.model,
            "variant": settings.variant,
            "checks": _check_manifest(checks),
            "pages": pages,
            "errors": errors,
            "skip": plan.skip,
            "runtime_error": None,
        },
        plan=_plan_value(plan, settings, checks),
        repo_root=repo_root,
    )
    _write_json(output, artifact)
    if plan.skip is not None:
        skipped = cast(list[str], plan.skip["paths"])
        print(
            "ContentCheck: skipped "
            f"selected={len(skipped)}, limit={plan.skip['limit']}",
            flush=True,
        )
        exit_code = 0
    else:
        exit_code = _print_results(pages, errors, checks)
    if exit_code != expected_exit_code(artifact):
        raise AssertionError("ContentCheck exit code does not match its result")
    return exit_code


def _changed_files(path: str, stdin: TextIO) -> list[str]:
    if path == "-":
        return stdin.read().splitlines()
    return Path(path).read_text(encoding="utf-8").splitlines()


def _cli_pages(repo_root: Path, pages: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in pages:
        page = _normalize_page(repo_root, raw)
        if page is None:
            raise ValueError(f"不是可检查的知识卡: {raw}")
        normalized.append(page)
    return sorted(set(normalized))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="使用 OpenCode 检查一张或多张知识卡的内容质量",
        epilog=(
            "示例:\n"
            "  python3 .agents/skills/knowledge-lint/scripts/content_check.py "
            "--pages knowledge/ops/ascendc/apis/example.md\n"
            "  git diff --name-only BASE...HEAD -- knowledge/ | "
            "python3 .agents/skills/knowledge-lint/scripts/content_check.py "
            "--changed-files -"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--pages",
        nargs="+",
        metavar="PAGE",
        help="直接检查一张或多张仓库内知识卡",
    )
    inputs.add_argument("--changed-files", help="流水线变更文件清单；- 表示标准输入")
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--command", help="覆盖配置中的 OpenCode 可执行命令")
    outputs = parser.add_mutually_exclusive_group()
    outputs.add_argument("--output", type=Path)
    outputs.add_argument(
        "--plan-only",
        type=Path,
        metavar="PATH",
        help="仅写入选页计划，不启动 OpenCode",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    output = args.output or repo_root / "artifacts/ci/content-check.json"
    try:
        settings, checks = load_config(args.config.resolve(), args.command)
        auto_selected = args.changed_files is not None
        selected = (
            select_pages(repo_root, _changed_files(args.changed_files, sys.stdin))
            if auto_selected
            else _cli_pages(repo_root, args.pages)
        )
        plan = build_selection_plan(selected, settings, auto_selected)
        if args.plan_only is not None:
            write_selection_plan(args.plan_only, plan, settings, checks)
            return 0
        exit_code = run_content_check(
            repo_root=repo_root,
            plan=plan,
            settings=settings,
            checks=checks,
            output=output,
        )
    except (KeyError, OSError, ValueError) as exc:
        print(f"ContentCheck: {exc}", file=sys.stderr)
        return 2
    return exit_code


def _interrupt_on_terminate(_signum: int, _frame: object) -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _interrupt_on_terminate)
    raise SystemExit(main())
