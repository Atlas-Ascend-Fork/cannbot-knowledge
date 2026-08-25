"""OpenCode CLI boundary for one-page content checks."""

from __future__ import annotations

import json
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


class OpenCodeRuntimeError(OpenCodeError):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
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
    usage: dict[str, float]


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


def _number(value: object) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def _error_details(value: object) -> tuple[str, int | None]:
    if not isinstance(value, dict):
        return "OpenCode 请求失败", None
    name = str(value.get("name") or "OpenCodeError")
    data = value.get("data")
    if not isinstance(data, dict):
        return name, None
    message = str(data.get("message") or "").strip()
    raw_status = data.get("statusCode") or data.get("status")
    try:
        status = int(raw_status) if raw_status is not None else None
    except (TypeError, ValueError):
        status = None
    detail = f"HTTP {status}" if status is not None else ""
    if message:
        detail = f"{detail}: {message}" if detail else message
    return (f"{name}: {detail}" if detail else name), status


def _is_retryable_status(status: int | None) -> bool:
    return status == 429 or (status is not None and status >= 500)


def _redact(text: str, values: tuple[str, ...]) -> str:
    for value in values:
        if value:
            text = text.replace(value, "[redacted]")
    return text


def parse_events(stdout: str, *, redact: tuple[str, ...] = ()) -> OpenCodeResult:
    """Read OpenCode JSONL and return the final assistant text and usage."""
    final_text = ""
    last_error: tuple[str, int | None] | None = None
    usage = {
        "input": 0.0,
        "output": 0.0,
        "reasoning": 0.0,
        "cache_read": 0.0,
        "cache_write": 0.0,
    }
    for raw_line in stdout.splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise OpenCodeProtocolError("OpenCode 输出了非 JSONL 内容") from exc
        if not isinstance(event, dict):
            raise OpenCodeProtocolError("OpenCode JSONL 事件不是 object")

        event_type = event.get("type")
        part = event.get("part")
        if event_type == "text" and isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                final_text = text.strip()
        elif event_type == "step_finish" and isinstance(part, dict):
            tokens = part.get("tokens")
            if not isinstance(tokens, dict):
                continue
            cache = tokens.get("cache")
            cache = cache if isinstance(cache, dict) else {}
            usage["input"] += _number(tokens.get("input"))
            usage["output"] += _number(tokens.get("output"))
            usage["reasoning"] += _number(tokens.get("reasoning"))
            usage["cache_read"] += _number(cache.get("read"))
            usage["cache_write"] += _number(cache.get("write"))
        elif event_type == "error":
            last_error = _error_details(event.get("error"))

    if last_error:
        message, status = last_error
        raise OpenCodeRuntimeError(
            _redact(message, redact), retryable=_is_retryable_status(status)
        )
    if not final_text:
        raise OpenCodeIncompleteError("OpenCode 未返回最终文本")
    return OpenCodeResult(text=_redact(final_text, redact), usage=usage)


def build_env(
    *,
    opencode_config: str,
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


def _stderr_detail(stderr: str, env: dict[str, str], model_env: tuple[str, ...]) -> str:
    detail = _redact(stderr.strip(), tuple(env.get(name, "") for name in model_env))
    return detail.splitlines()[-1][:1000] if detail else ""


def run_opencode(
    *,
    command: str,
    repo_root: Path,
    page: str,
    prompt: str,
    model: str,
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
            model_env=model_env,
            state_root=Path(temporary),
        )
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
        except FileNotFoundError as exc:
            raise OpenCodeError(f"找不到 OpenCode 可执行文件: {command}") from exc

        if processes is not None:
            processes.add(process)
        try:
            try:
                stdout, stderr = process.communicate(prompt, timeout=timeout_s)
            except subprocess.TimeoutExpired as exc:
                _stop_process(process)
                process.communicate()
                raise OpenCodeTimeout(f"OpenCode 页面检查超时({timeout_s:g}s)") from exc
            except BaseException:
                _stop_process(process)
                process.communicate()
                raise
        finally:
            if processes is not None:
                processes.discard(process)

    if process.returncode != 0:
        if stdout.strip():
            try:
                parse_events(
                    stdout,
                    redact=tuple(env.get(name, "") for name in model_env),
                )
            except (OpenCodeIncompleteError, OpenCodeProtocolError):
                pass
        detail = _stderr_detail(stderr, env, model_env)
        message = f"OpenCode 退出码 {process.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise OpenCodeRuntimeError(message)
    return parse_events(
        stdout,
        redact=tuple(env.get(name, "") for name in model_env),
    )
