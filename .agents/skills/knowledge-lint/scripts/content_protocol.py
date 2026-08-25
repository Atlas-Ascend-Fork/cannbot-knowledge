"""Machine protocol shared by ContentCheck and its CI adapter."""

from __future__ import annotations

import math
from pathlib import Path, PurePosixPath


TIERS = ("P0", "P1", "P2")
USAGE_KEYS = ("input", "output", "reasoning", "cache_read", "cache_write")
RESULT_FIELDS = {
    "model",
    "variant",
    "checks",
    "pages",
    "errors",
    "skip",
    "runtime_error",
}


class ContentProtocolError(ValueError):
    """Raised when a ContentCheck plan or result violates its protocol."""


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ContentProtocolError(f"{label} must be an object")
    return value


def _exact_keys(value: dict[str, object], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ContentProtocolError(f"{label} has invalid fields")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentProtocolError(f"{label} must be a non-empty string")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContentProtocolError(f"{label} must be a positive integer")
    return value


def _number(value: object, label: str) -> int | float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value < 0
        or (isinstance(value, float) and not math.isfinite(value))
    ):
        raise ContentProtocolError(f"{label} must be a finite non-negative number")
    return value


def _page_path(value: object, label: str) -> str:
    path = _text(value, label)
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or parsed.as_posix() != path
        or not parsed.parts
        or parsed.parts[0] != "knowledge"
        or ".." in parsed.parts
        or parsed.suffix != ".md"
        or parsed.name == "index.md"
    ):
        raise ContentProtocolError(f"{label} is not a knowledge page")
    return path


def validate_manifest(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ContentProtocolError("checks must be a non-empty array")
    checks: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        check = _object(raw, f"checks[{index}]")
        _exact_keys(check, {"id", "title", "tier"}, f"checks[{index}]")
        tier = _text(check["tier"], f"checks[{index}].tier")
        if tier not in TIERS:
            raise ContentProtocolError(f"checks[{index}].tier is invalid")
        checks.append(
            {
                "id": _text(check["id"], f"checks[{index}].id"),
                "title": _text(check["title"], f"checks[{index}].title"),
                "tier": tier,
            }
        )
    ids = [check["id"] for check in checks]
    if len(ids) != len(set(ids)):
        raise ContentProtocolError("check ids must be unique")
    return checks


def _paths(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ContentProtocolError(f"{label} must be an array")
    paths = [_page_path(path, f"{label}[{index}]") for index, path in enumerate(value)]
    if paths != sorted(set(paths)):
        raise ContentProtocolError(f"{label} must be sorted and unique")
    return paths


def validate_skip(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    skip = _object(value, "skip")
    _exact_keys(skip, {"reason", "limit", "paths"}, "skip")
    if skip["reason"] != "changed_page_limit_exceeded":
        raise ContentProtocolError("skip.reason is invalid")
    limit = _positive_int(skip["limit"], "skip.limit")
    paths = _paths(skip["paths"], "skip.paths")
    if len(paths) <= limit:
        raise ContentProtocolError("skip.paths does not exceed skip.limit")
    return {"reason": "changed_page_limit_exceeded", "limit": limit, "paths": paths}


def validate_plan(value: object) -> dict[str, object]:
    plan = _object(value, "plan")
    _exact_keys(
        plan,
        {"model", "variant", "checks", "selected", "skip", "needs_model"},
        "plan",
    )
    checks = validate_manifest(plan["checks"])
    selected = _paths(plan["selected"], "selected")
    skip = validate_skip(plan["skip"])
    needs_model = plan["needs_model"]
    if not isinstance(needs_model, bool):
        raise ContentProtocolError("needs_model must be a boolean")
    if skip is not None and skip["paths"] != selected:
        raise ContentProtocolError("skip.paths must equal selected")
    if needs_model != bool(selected and skip is None):
        raise ContentProtocolError("needs_model is inconsistent with selected and skip")
    return {
        "model": _text(plan["model"], "model"),
        "variant": _text(plan["variant"], "variant"),
        "checks": checks,
        "selected": selected,
        "skip": skip,
        "needs_model": needs_model,
    }


def validate_page_results(
    value: object,
    check_ids: list[str],
    *,
    line_count: int | None = None,
) -> dict[str, list[dict[str, object]]]:
    results = _object(value, "page results")
    if set(results) != set(check_ids):
        raise ContentProtocolError("page results must cover every configured check")
    normalized: dict[str, list[dict[str, object]]] = {}
    for check_id in check_ids:
        raw_violations = results[check_id]
        if not isinstance(raw_violations, list):
            raise ContentProtocolError(f"result {check_id} must be an array")
        violations: list[dict[str, object]] = []
        for index, raw in enumerate(raw_violations):
            violation = _object(raw, f"result {check_id}[{index}]")
            _exact_keys(violation, {"msg", "line"}, f"result {check_id}[{index}]")
            line = violation["line"]
            if line is not None:
                line = _positive_int(line, f"result {check_id}[{index}].line")
                if line_count is not None and line > line_count:
                    raise ContentProtocolError(
                        f"result {check_id}[{index}].line exceeds page length"
                    )
            violations.append(
                {
                    "msg": _text(
                        violation["msg"], f"result {check_id}[{index}].msg"
                    ).strip(),
                    "line": line,
                }
            )
        normalized[check_id] = violations
    return normalized


def _line_count(repo_root: Path | None, path: str) -> int | None:
    if repo_root is None:
        return None
    page = repo_root / path
    try:
        return len(page.read_text(encoding="utf-8").splitlines())
    except OSError as exc:
        raise ContentProtocolError(f"cannot read result page: {path}") from exc


def _page(
    value: object,
    index: int,
    check_ids: list[str],
    repo_root: Path | None,
) -> dict[str, object]:
    page = _object(value, f"pages[{index}]")
    _exact_keys(page, {"path", "results", "usage", "elapsed_s"}, f"pages[{index}]")
    path = _page_path(page["path"], f"pages[{index}].path")
    usage = _object(page["usage"], f"pages[{index}].usage")
    _exact_keys(usage, set(USAGE_KEYS), f"pages[{index}].usage")
    return {
        "path": path,
        "results": validate_page_results(
            page["results"], check_ids, line_count=_line_count(repo_root, path)
        ),
        "usage": {
            key: _number(usage[key], f"pages[{index}].usage.{key}")
            for key in USAGE_KEYS
        },
        "elapsed_s": _number(page["elapsed_s"], f"pages[{index}].elapsed_s"),
    }


def _page_error(value: object, index: int) -> dict[str, str]:
    error = _object(value, f"errors[{index}]")
    _exact_keys(error, {"path", "kind", "message"}, f"errors[{index}]")
    return {
        "path": _page_path(error["path"], f"errors[{index}].path"),
        "kind": _text(error["kind"], f"errors[{index}].kind"),
        "message": _text(error["message"], f"errors[{index}].message"),
    }


def _runtime_error(value: object) -> dict[str, str] | None:
    if value is None:
        return None
    error = _object(value, "runtime_error")
    _exact_keys(error, {"kind", "message"}, "runtime_error")
    return {
        "kind": _text(error["kind"], "runtime_error.kind"),
        "message": _text(error["message"], "runtime_error.message"),
    }


def validate_result(
    value: object,
    *,
    plan: dict[str, object] | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    result = _object(value, "result")
    _exact_keys(result, RESULT_FIELDS, "result")
    runtime_error = _runtime_error(result["runtime_error"])
    if runtime_error is None:
        model: str | None = _text(result["model"], "model")
        variant: str | None = _text(result["variant"], "variant")
        checks = validate_manifest(result["checks"])
    else:
        model = result["model"]
        variant = result["variant"]
        if model is not None:
            model = _text(model, "model")
        if variant is not None:
            variant = _text(variant, "variant")
        checks = [] if result["checks"] == [] else validate_manifest(result["checks"])

    if not isinstance(result["pages"], list) or not isinstance(result["errors"], list):
        raise ContentProtocolError("pages and errors must be arrays")
    check_ids = [check["id"] for check in checks]
    pages = [
        _page(raw, index, check_ids, repo_root)
        for index, raw in enumerate(result["pages"])
    ]
    errors = [_page_error(raw, index) for index, raw in enumerate(result["errors"])]
    page_paths = [str(page["path"]) for page in pages]
    error_paths = [error["path"] for error in errors]
    if page_paths != sorted(set(page_paths)):
        raise ContentProtocolError("pages must be sorted and unique")
    if error_paths != sorted(set(error_paths)):
        raise ContentProtocolError("errors must be sorted and unique")
    if set(page_paths) & set(error_paths):
        raise ContentProtocolError("a page cannot be both completed and incomplete")

    skip = validate_skip(result["skip"])
    if skip is not None and (pages or errors or runtime_error is not None):
        raise ContentProtocolError("a skipped result cannot contain work results")
    if runtime_error is not None and (pages or errors or skip is not None):
        raise ContentProtocolError("a runtime failure cannot contain page results")

    normalized: dict[str, object] = {
        "model": model,
        "variant": variant,
        "checks": checks,
        "pages": pages,
        "errors": errors,
        "skip": skip,
        "runtime_error": runtime_error,
    }
    if plan is not None:
        expected = validate_plan(plan)
        for key in ("model", "variant", "checks"):
            if normalized[key] != expected[key]:
                raise ContentProtocolError(f"result {key} does not match the plan")
        if runtime_error is None:
            if skip != expected["skip"]:
                raise ContentProtocolError("result skip does not match the plan")
            if skip is None:
                completed = sorted(page_paths + error_paths)
                if completed != expected["selected"]:
                    raise ContentProtocolError(
                        "result does not cover every selected page"
                    )
    return normalized


def expected_exit_code(result: dict[str, object]) -> int:
    if result["runtime_error"] is not None or result["errors"]:
        return 2
    if result["skip"] is not None:
        return 0
    tiers = {check["id"]: check["tier"] for check in result["checks"]}
    for page in result["pages"]:
        for check_id, violations in page["results"].items():
            if tiers[check_id] == "P0" and violations:
                return 1
    return 0


def validate_ci_result(
    value: object,
    *,
    plan: dict[str, object] | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    envelope = _object(value, "CI result")
    _exact_keys(envelope, RESULT_FIELDS | {"check_exit_code"}, "CI result")
    check_exit_code = envelope["check_exit_code"]
    if (
        isinstance(check_exit_code, bool)
        or not isinstance(check_exit_code, int)
        or check_exit_code not in {0, 1, 2}
    ):
        raise ContentProtocolError("check_exit_code must be 0, 1, or 2")
    core = validate_result(
        {key: envelope[key] for key in RESULT_FIELDS},
        plan=plan,
        repo_root=repo_root,
    )
    if check_exit_code != expected_exit_code(core):
        raise ContentProtocolError("check_exit_code does not match the result")
    return {**core, "check_exit_code": check_exit_code}


def attach_exit_code(
    result: dict[str, object],
    check_exit_code: int,
    *,
    plan: dict[str, object] | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    return validate_ci_result(
        {**result, "check_exit_code": check_exit_code},
        plan=plan,
        repo_root=repo_root,
    )
