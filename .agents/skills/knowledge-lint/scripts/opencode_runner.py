"""OpenCode CLI boundary for one-page content checks."""

from __future__ import annotations

import json
import math
import os
import signal
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path


_PASSTHROUGH_ENV = (
    "PATH",
    "SHELL",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "no_proxy",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)


class OpenCodeError(RuntimeError):
    kind = "runner"
    retryable = False

    def __init__(
        self, message: str, *, usage: dict[str, int | float] | None = None
    ) -> None:
        super().__init__(message)
        self.usage = usage


class OpenCodeRuntimeError(OpenCodeError):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        usage: dict[str, int | float] | None = None,
    ) -> None:
        super().__init__(message, usage=usage)
        self.retryable = retryable


class OpenCodeTimeout(OpenCodeError):
    kind = "timeout"
    retryable = True


class OpenCodeProtocolError(OpenCodeError):
    kind = "protocol"


class OpenCodeIncompleteError(OpenCodeError):
    kind = "protocol"
    retryable = True


@dataclass(frozen=True)
class OpenCodeResult:
    text: str
    usage: dict[str, int | float]
    usage_complete: bool = True


class ProcessRegistry:
    """Track active OpenCode process groups so an interrupted batch can stop them."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._processes: set[subprocess.Popen[str]] = set()
        self._stopped = False

    def add(self, process: subprocess.Popen[str]) -> None:
        with self._lock:
            if not self._stopped:
                self._processes.add(process)
                return
        _stop_process(process)

    def discard(self, process: subprocess.Popen[str]) -> None:
        with self._lock:
            self._processes.discard(process)

    def stop_all(self) -> None:
        with self._lock:
            self._stopped = True
            processes = tuple(self._processes)
        for process in processes:
            _stop_process(process)


def _number(value: object) -> int | float:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise OpenCodeProtocolError("OpenCode token 计数无效")
    if isinstance(value, float) and not math.isfinite(value):
        raise OpenCodeProtocolError("OpenCode token 计数无效")
    return value


def _error_details(value: object) -> tuple[str, int | None]:
    if not isinstance(value, dict):
        return "OpenCode 请求失败", None
    data = value.get("data")
    if not isinstance(data, dict):
        return "OpenCode 请求失败", None
    raw_status = data.get("statusCode") or data.get("status")
    try:
        status = int(raw_status) if raw_status is not None else None
    except (TypeError, ValueError):
        status = None
    detail = f" (HTTP {status})" if status is not None else ""
    return f"OpenCode 请求失败{detail}", status


def _is_retryable_status(status: int | None) -> bool:
    return status == 429 or (status is not None and status >= 500)


def redact_text(text: str, values: tuple[str, ...]) -> str:
    for value in values:
        if value:
            text = text.replace(value, "[redacted]")
    return text


def parse_events(stdout: str, *, redact: tuple[str, ...] = ()) -> OpenCodeResult:
    """Read OpenCode JSONL and return the final assistant text and usage."""
    final_text = ""
    last_error: tuple[str, int | None] | None = None
    usage = {
        "input": 0,
        "output": 0,
        "reasoning": 0,
        "cache_read": 0,
        "cache_write": 0,
    }
    usage_seen = False
    usage_complete = True
    for raw_line in stdout.splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise OpenCodeProtocolError(
                "OpenCode 输出了非 JSONL 内容", usage=usage if usage_seen else None
            ) from exc
        if not isinstance(event, dict):
            raise OpenCodeProtocolError(
                "OpenCode JSONL 事件不是 object", usage=usage if usage_seen else None
            )

        event_type = event.get("type")
        part = event.get("part")
        if event_type == "text" and isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                final_text = text.strip()
        elif event_type == "step_finish" and isinstance(part, dict):
            tokens = part.get("tokens")
            if not isinstance(tokens, dict):
                usage_complete = False
                continue
            if tokens.get("input") is None or tokens.get("output") is None:
                usage_complete = False
            cache = tokens.get("cache")
            cache = cache if isinstance(cache, dict) else {}
            try:
                counts = {
                    "input": _number(tokens.get("input")),
                    "output": _number(tokens.get("output")),
                    "reasoning": _number(tokens.get("reasoning")),
                    "cache_read": _number(cache.get("read")),
                    "cache_write": _number(cache.get("write")),
                }
            except OpenCodeProtocolError as exc:
                exc.usage = usage if usage_seen else None
                raise
            usage_seen = True
            for key, value in counts.items():
                usage[key] += value
        elif event_type == "error":
            last_error = _error_details(event.get("error"))

    if last_error:
        message, status = last_error
        raise OpenCodeRuntimeError(
            message,
            retryable=_is_retryable_status(status),
            usage=usage if usage_seen else None,
        )
    if not final_text:
        raise OpenCodeIncompleteError(
            "OpenCode 未返回最终文本", usage=usage if usage_seen else None
        )
    return OpenCodeResult(
        text=redact_text(final_text, redact),
        usage=usage,
        usage_complete=usage_seen and usage_complete,
    )


def build_env(
    *,
    opencode_config: str,
    model_id: str,
    model_env: tuple[str, ...],
    state_root: Path,
) -> dict[str, str]:
    """Build the small environment inherited by OpenCode and its tools."""
    env = {name: os.environ[name] for name in _PASSTHROUGH_ENV if name in os.environ}
    for name in model_env:
        value = os.environ.get(name)
        if not value:
            raise OpenCodeError(f"缺少模型凭据环境变量: {name}")
        env[name] = value

    env.update(
        {
            "HOME": os.fspath(state_root / "home"),
            "NO_COLOR": "1",
            "CONTENT_CHECK_MODEL_ID": model_id,
            "OPENCODE_CONFIG_CONTENT": opencode_config,
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
            "XDG_CACHE_HOME": os.fspath(state_root / "cache"),
            "XDG_CONFIG_HOME": os.fspath(state_root / "config"),
            "XDG_DATA_HOME": os.fspath(state_root / "data"),
            "XDG_STATE_HOME": os.fspath(state_root / "state"),
        }
    )
    return env


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        try:
            process.kill()
        except OSError:
            pass


def run_opencode(
    *,
    command: str,
    repo_root: Path,
    page: str,
    prompt: str,
    model: str,
    model_id: str,
    variant: str,
    timeout_s: float,
    model_env: tuple[str, ...],
    opencode_config: str,
    processes: ProcessRegistry | None = None,
) -> OpenCodeResult:
    """Run one isolated OpenCode session for one knowledge page."""
    argv = [
        command,
        "--pure",
        "run",
        "--dir",
        os.fspath(repo_root),
        "--model",
        model,
        "--format",
        "json",
        "--title",
        f"ContentCheck: {page}",
        "--variant",
        variant,
    ]

    with tempfile.TemporaryDirectory(prefix="content-check-opencode-") as temporary:
        env = build_env(
            opencode_config=opencode_config,
            model_id=model_id,
            model_env=model_env,
            state_root=Path(temporary),
        )
        timed_out = False
        try:
            process = subprocess.Popen(
                argv,
                cwd=repo_root,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except OSError:
            raise OpenCodeError("无法启动 OpenCode 进程") from None

        if processes is not None:
            processes.add(process)
        try:
            try:
                stdout, _ = process.communicate(prompt, timeout=timeout_s)
            except subprocess.TimeoutExpired:
                _stop_process(process)
                stdout, _ = process.communicate()
                timed_out = True
            except BaseException:
                _stop_process(process)
                process.communicate()
                raise
        finally:
            if processes is not None:
                processes.discard(process)

    try:
        response = parse_events(
            stdout, redact=tuple(env.get(name, "") for name in model_env)
        )
    except OpenCodeError as exc:
        if not timed_out and (
            not process.returncode or isinstance(exc, OpenCodeRuntimeError)
        ):
            raise
        usage = exc.usage
    else:
        if not timed_out and not process.returncode:
            return response
        usage = response.usage
    if timed_out:
        raise OpenCodeTimeout(f"OpenCode 页面检查超时({timeout_s:g}s)", usage=usage)
    raise OpenCodeRuntimeError(f"OpenCode 退出码 {process.returncode}", usage=usage)
