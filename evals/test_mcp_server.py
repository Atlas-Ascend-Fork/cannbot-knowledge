# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""End-to-end tests for mcp-server/server.py (external behavior only)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_DIR = ROOT / "mcp-server"
SERVER = MCP_SERVER_DIR / "server.py"
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
INDEX_TOOL = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
SKILL_SCRIPTS = ROOT / ".agents/skills/knowledge-query/scripts"
CASES = ROOT / "evals/retrieval_cases.yaml"

CARD_A = """---
type: API
title: DataCopyPad 对齐约束
description: DataCopyPad 在 GM 与 UB 间拷贝时的对齐与 padding 行为约束。
tags: [task.lookup, topic.memory]
status: stable
sources:
  - resource: https://example.com/cann/datacopypad
    role: primary
  - resource: https://example.com/cann/datacopypad-guide
    role: supporting
  - resource: https://example.com/cann/datacopypad-extras
    role: example
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: [a2, "950"]
---

# DataCopyPad

DataCopyPad copies padded blocks between GM and UB. See the
[aligned helper](aligned_api.md) for related alignment helpers.

## Details

The copy respects alignment constraints per platform.
"""

CARD_B = """---
type: API
title: Aligned API helper
description: Alignment helper APIs used together with DataCopyPad.
tags: [task.lookup, topic.memory]
status: stable
sources:
  - resource: https://example.com/cann/aligned
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: ["950"]
---

# Aligned API helper

Relative link: [DataCopyPad](data_copy_pad.md). Bundle-root link:
[root copy](/ops/ascendc/apis/data_copy_pad.md). Anchor link:
[details](#details). External link: [official docs](https://example.com/docs).
Navigation link: [API index](index.md). Image: ![pipeline](https://raw.gitcode.com/cann/asc-devkit/raw/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/figures/net_topology.png "LI Pipeline").

```text
[not a link](fake_target.md)
```

## Details

Helper body.

<a id="details"></a>
"""


def big_card(total_lines: int) -> str:
    frontmatter = [
        "---",
        "type: API",
        "title: Appendix table",
        "description: Large generated appendix table for pagination tests.",
        "tags: [task.lookup, topic.memory]",
        "status: stable",
        "sources:",
        "  - resource: https://example.com/cann/appendix",
        "    role: primary",
        'created_at: "2026-08-18T00:00:00Z"',
        'updated_at: "2026-08-18T00:00:00Z"',
        'platforms: ["950"]',
        "---",
        "",
    ]
    body_lines = max(0, total_lines - len(frontmatter))
    lines = frontmatter + [f"appendix row {index:04d} payload data" for index in range(body_lines)]
    return "\n".join(lines) + "\n"


def write_index(path: Path, entries: list[tuple[str, str]]) -> None:
    lines = ["# Index", ""]
    for name, summary in entries:
        lines.append(f"- [{name}]({name})：{summary}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_fixture() -> Path:
    temporary = tempfile.mkdtemp(prefix="cannbot-mcp-fixture-")
    root = Path(temporary) / "knowledge-root"
    root.mkdir()
    shutil.copytree(ROOT / "governance", root / "governance")
    shutil.copytree(
        SKILL_SCRIPTS,
        root / ".agents/skills/knowledge-query/scripts",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    apis = root / "knowledge/ops/ascendc/apis"
    apis.mkdir(parents=True)
    (root / "knowledge/index.md").write_text(
        '---\nokf_version: "0.2"\n---\n\n# Test knowledge\n', encoding="utf-8"
    )
    write_index(
        root / "knowledge/ops/index.md",
        [("ascendc", "Ascend C 算子知识")],
    )
    write_index(
        root / "knowledge/ops/ascendc/index.md",
        [("apis", "API 知识")],
    )
    write_index(
        apis / "index.md",
        [
            ("data_copy_pad.md", "DataCopyPad 对齐约束。"),
            ("aligned_api.md", "对齐辅助 API。"),
            ("appendix_table.md", "分页测试用附录表。"),
        ],
    )
    (apis / "data_copy_pad.md").write_text(CARD_A, encoding="utf-8")
    (apis / "aligned_api.md").write_text(CARD_B, encoding="utf-8")
    (apis / "appendix_table.md").write_text(big_card(1985), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(INDEX_TOOL),
            "--knowledge-root",
            str(root),
            "build",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"fixture index build failed: {completed.stderr}")
    return root


FIXTURE: Path | None = None
HOME_DIR: Path | None = None


def setUpModule() -> None:
    global FIXTURE, HOME_DIR
    FIXTURE = build_fixture()
    HOME_DIR = Path(tempfile.mkdtemp(prefix="cannbot-mcp-home-"))


def tearDownModule() -> None:
    if FIXTURE is not None:
        shutil.rmtree(FIXTURE.parent, ignore_errors=True)
    if HOME_DIR is not None:
        shutil.rmtree(HOME_DIR, ignore_errors=True)


def server_command() -> list[str]:
    for candidate in (
        MCP_SERVER_DIR / ".venv/bin/python",
        MCP_SERVER_DIR / ".venv/bin/python3",
    ):
        if candidate.is_file():
            return [str(candidate), str(SERVER)]
    executable = shutil.which("uv")
    if executable:
        return [executable, "--directory", str(MCP_SERVER_DIR), "run", str(SERVER)]
    probe = subprocess.run(
        [sys.executable, "-c", "import mcp"], check=False, capture_output=True
    )
    if probe.returncode == 0:
        return [sys.executable, str(SERVER)]
    raise unittest.SkipTest(
        "no MCP server runtime available (mcp-server/.venv or uv with network)"
    )


def server_environment(root: Path, home: Path, **overrides: str) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "CANNBOT_KNOWLEDGE_ROOT": str(root),
    }
    environment.update({key: str(value) for key, value in overrides.items()})
    return environment


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class StdioClient:
    """Minimal newline-delimited JSON-RPC client for the stdio transport."""

    def __init__(self, root: Path, home: Path, cwd: Path | None = None, **env: str) -> None:
        self.process = subprocess.Popen(
            server_command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=server_environment(root, home, **env),
            cwd=str(cwd) if cwd else None,
        )
        self.responses: dict[object, dict] = {}
        self.stderr_lines: list[str] = []
        self.stdout_noise: list[str] = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self.stdout_noise.append(line)
                continue
            if isinstance(message, dict) and "id" in message:
                with self._condition:
                    self.responses[message["id"]] = message
                    self._condition.notify_all()

    def _read_stderr(self) -> None:
        for line in self.process.stderr:
            self.stderr_lines.append(line)

    def request(self, identifier: object, method: str, params: dict | None = None, timeout: float = 180.0) -> dict:
        message: dict = {"jsonrpc": "2.0", "id": identifier, "method": method}
        if params is not None:
            message["params"] = params
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        deadline = time.time() + timeout
        with self._condition:
            while identifier not in self.responses:
                remaining = deadline - time.time()
                if remaining <= 0 or self.process.poll() is not None:
                    raise AssertionError(
                        f"no response for {method} (id={identifier}); "
                        f"stderr={self.stderr_text()[-800:]}"
                    )
                self._condition.wait(remaining / 4 + 0.05)
        return self.responses[identifier]

    def notify(self, method: str) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.process.stdin.flush()

    def initialize(self) -> dict:
        response = self.request(
            "init",
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "evals", "version": "1"},
            },
        )
        self.notify("notifications/initialized")
        return response["result"]

    def call_tool(self, name: str, arguments: dict, timeout: float = 180.0) -> tuple[bool, object]:
        response = self.request(
            f"call-{name}-{time.monotonic_ns()}",
            "tools/call",
            {"name": name, "arguments": arguments},
            timeout=timeout,
        )
        result = response["result"]
        text = result["content"][0]["text"]
        is_error = bool(result.get("isError"))
        if is_error:
            return True, text
        return False, json.loads(text)

    def stderr_text(self) -> str:
        return "".join(self.stderr_lines)

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)


class HttpServer:
    """Streamable HTTP server process with a tiny JSON/SSE client."""

    def __init__(
        self,
        root: Path,
        home: Path,
        *,
        tokens: str,
        rate_limit: int | None = None,
        log_dir: Path | None = None,
        log_mode: str | None = None,
        upload_remote: Path | None = None,
        upload_interval: int | None = None,
        first_token: str = "cbk_ready",
    ) -> None:
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}/mcp"
        environment: dict[str, str] = {
            "CANNBOT_MCP_TRANSPORT": "http",
            "CANNBOT_MCP_PORT": str(self.port),
            "CANNBOT_MCP_TOKENS": tokens,
        }
        if rate_limit is not None:
            environment["CANNBOT_MCP_RATE_LIMIT"] = str(rate_limit)
        if log_dir is not None:
            environment["CANNBOT_MCP_LOG_DIR"] = str(log_dir)
        if log_mode is not None:
            environment["CANNBOT_MCP_LOG"] = log_mode
        if upload_remote is not None:
            environment["CANNBOT_MCP_LOG_UPLOAD_REMOTE"] = str(upload_remote)
        if upload_interval is not None:
            environment["CANNBOT_MCP_LOG_UPLOAD_INTERVAL"] = str(upload_interval)
        self.process = subprocess.Popen(
            server_command(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=server_environment(root, home, **environment),
        )
        self._stderr: list[str] = []
        threading.Thread(target=self._drain, daemon=True).start()
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(
                    "HTTP server exited during startup: " + self.stderr_text()
                )
            try:
                status, _headers, messages = self.post(
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    token=first_token,
                    timeout=5,
                )
                if status == 200 and messages:
                    return
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(0.2)
        raise AssertionError("HTTP server did not become ready: " + self.stderr_text())

    def _drain(self) -> None:
        for line in self.process.stderr:
            self._stderr.append(line)

    def stderr_text(self) -> str:
        return "".join(self._stderr)

    def post(self, payload: dict, token: str | None = None, timeout: float = 60.0):
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(self.base, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, dict(response.headers), self._parse(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers or {}), self._parse(exc.read().decode("utf-8"))

    @staticmethod
    def _parse(raw: str) -> list[dict]:
        if raw.startswith("event:") or raw.startswith("data:"):
            messages = []
            for line in raw.splitlines():
                if line.startswith("data: "):
                    messages.append(json.loads(line[6:]))
            return messages
        try:
            return [json.loads(raw)]
        except json.JSONDecodeError:
            return []

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)


def run_direct_cli(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(QUERY), "--knowledge-root", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
        cwd=tempfile.gettempdir(),
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", str(Path.home())),
        },
    )


def retry_after_of(headers: dict) -> int:
    for key, value in headers.items():
        if key.lower() == "retry-after":
            return int(value)
    return 0


class StdioSmokeTests(unittest.TestCase):
    def test_initialize_tools_list_and_discover(self) -> None:
        client = StdioClient(FIXTURE, HOME_DIR)
        try:
            info = client.initialize()
            self.assertEqual("cannbot-knowledge", info["serverInfo"]["name"])
            response = client.request("tools", "tools/list")
            tools = {tool["name"]: tool for tool in response["result"]["tools"]}
            self.assertEqual({"discover", "search", "read_card"}, set(tools))
            for tool in tools.values():
                self.assertTrue(tool["annotations"]["readOnlyHint"])
                self.assertTrue(tool["description"])
            search_schema = tools["search"]["inputSchema"]
            self.assertIn("query", search_schema.get("required", []))
            self.assertNotIn("platform", search_schema.get("required", []))
            self.assertIn("a2 / a3 / 950", search_schema["properties"]["platform"]["description"])
            self.assertIn(
                "not multi-word AND", search_schema["properties"]["match"]["description"]
            )
            self.assertIn(
                "start small", search_schema["properties"]["limit"]["description"]
            )
            is_error, payload = client.call_tool("discover", {})
            self.assertFalse(is_error)
            self.assertEqual("knowledge-discovery.v1", payload["schema_version"])
            self.assertEqual(3, payload["cards"])
            self.assertIn("index", payload)
            self.assertIn("content_fingerprint", payload["index"])
            self.assertEqual([], client.stdout_noise)
        finally:
            client.close()

    def test_missing_index_fails_closed_with_clean_stdout(self) -> None:
        broken = FIXTURE.parent / "broken-root"
        shutil.copytree(
            FIXTURE, broken, ignore=shutil.ignore_patterns("knowledge.sqlite3*")
        )
        try:
            shutil.rmtree(broken / "artifacts", ignore_errors=True)
            client = StdioClient(broken, HOME_DIR)
            try:
                client.initialize()
                is_error, text = client.call_tool("discover", {})
                self.assertTrue(is_error)
                self.assertIn("knowledge CLI failed", text)
                self.assertIn("knowledge_index.py", text)
                self.assertEqual([], client.stdout_noise)
            finally:
                client.close()
        finally:
            shutil.rmtree(broken, ignore_errors=True)

    def test_stale_index_is_rejected(self) -> None:
        card = FIXTURE / "knowledge/ops/ascendc/apis/data_copy_pad.md"
        stat = card.stat()
        client = StdioClient(FIXTURE, HOME_DIR)
        try:
            client.initialize()
            try:
                os.utime(card, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
                is_error, text = client.call_tool("discover", {})
                self.assertTrue(is_error)
                self.assertIn("changed after index build", text)
                self.assertIn("knowledge_index.py", text)
            finally:
                os.utime(card, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            _is_error, payload = client.call_tool("discover", {})
            self.assertEqual(3, payload["cards"])
        finally:
            client.close()


class SearchParityTests(unittest.TestCase):
    CASE_ARGUMENT_KEYS = (
        "domain", "technology", "type", "task", "tag", "platform",
        "include_unlocated", "include_shared", "source_technology",
        "target_technology", "status", "match", "k",
    )

    @staticmethod
    def cli_arguments(query: str, filters: dict) -> list[str]:
        arguments = ["search", "--json", "--query", query]
        for key, value in filters.items():
            if key == "k":
                arguments += ["--limit", str(value)]
                continue
            flag = "--type" if key == "type" else f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    arguments.append(flag)
                continue
            values = value if isinstance(value, list) else [value]
            for item in values:
                arguments += [flag, str(item)]
        return arguments

    @staticmethod
    def mcp_arguments(query: str, filters: dict) -> dict:
        arguments: dict = {"query": query}
        for key, value in filters.items():
            if key == "k":
                arguments["limit"] = value
            elif key == "platform" and not isinstance(value, list):
                # retrieval_cases.yaml carries scalar platforms; the MCP
                # schema takes a list (the CLI takes repeats of --platform).
                arguments["platform"] = [value]
            else:
                arguments[key] = value
        return arguments

    def assert_parity(self, root: Path, query: str, filters: dict) -> None:
        direct = run_direct_cli(root, self.cli_arguments(query, filters))
        client = StdioClient(root, HOME_DIR)
        try:
            client.initialize()
            is_error, payload = client.call_tool(
                "search", self.mcp_arguments(query, filters)
            )
        finally:
            client.close()
        if direct.returncode != 0:
            self.assertTrue(is_error, "MCP search succeeded where the CLI failed")
            message = json.loads(direct.stdout)["error"]["message"]
            self.assertIn(message, payload)
            return
        self.assertFalse(is_error, payload)
        self.assertEqual(json.loads(direct.stdout), payload)

    def test_fixture_parity(self) -> None:
        for query, filters in (
            ("DataCopyPad", {"technology": "ascendc", "platform": ["a2"], "match": "literal", "k": 5}),
            ("appendix row", {"platform": ["950"], "match": "text", "k": 3}),
            ("aligned helper", {"platform": ["a2"]}),
        ):
            with self.subTest(query=query):
                self.assert_parity(FIXTURE, query, filters)

    def test_platform_fail_closed_and_unknown_platform(self) -> None:
        client = StdioClient(FIXTURE, HOME_DIR)
        try:
            client.initialize()
            is_error, text = client.call_tool(
                "search", {"query": "DataCopyPad", "technology": "ascendc"}
            )
            self.assertTrue(is_error)
            self.assertIn("platform is required", text)
            self.assertIn("determine a target platform", text)
            is_error, text = client.call_tool(
                "search",
                {"query": "DataCopyPad", "platform": ["ascend910b"], "match": "literal"},
            )
            self.assertTrue(is_error)
            self.assertIn("unknown platforms: ascend910b", text)
            is_error, payload = client.call_tool(
                "search",
                {"query": "DataCopyPad", "platform": ["950"], "match": "literal", "limit": 2},
            )
            self.assertFalse(is_error)
            self.assertLessEqual(payload["count"], 2)
            for result in payload["results"]:
                self.assertIn("950", result["platforms"] or [])
            self.assertIn("request_sha256", payload)
        finally:
            client.close()

    def test_repository_retrieval_cases_match_direct_cli(self) -> None:
        verify = subprocess.run(
            [sys.executable, str(INDEX_TOOL), "--knowledge-root", str(ROOT), "verify", "--level", "quick"],
            check=False, capture_output=True, text=True,
        )
        if verify.returncode != 0:
            build = subprocess.run(
                [sys.executable, str(INDEX_TOOL), "--knowledge-root", str(ROOT), "build"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(0, build.returncode, build.stderr)
        data = yaml.safe_load(CASES.read_text(encoding="utf-8"))
        cases = data["cases"]
        positive = [case for case in cases if not case.get("expected_error")][:6]
        negative = [case for case in cases if case.get("expected_error")][:2]
        for case in positive + negative:
            with self.subTest(case=case["id"]):
                self.assert_parity(ROOT, case["query"], case.get("filters", {}))


class ReadCardTests(unittest.TestCase):
    def read(self, arguments: dict) -> tuple[bool, object]:
        client = StdioClient(FIXTURE, HOME_DIR)
        try:
            client.initialize()
            return client.call_tool("read_card", arguments)
        finally:
            client.close()

    def test_card_payload_frontmatter_sources_links_images(self) -> None:
        is_error, card = self.read({"path": "ops/ascendc/apis/aligned_api.md"})
        self.assertFalse(is_error)
        self.assertEqual("ops/ascendc/apis/aligned_api", card["path"])
        self.assertTrue(card["content"].startswith("---\n"))
        self.assertEqual("API", card["frontmatter"]["type"])
        self.assertEqual(["950"], card["frontmatter"]["platforms"])
        self.assertEqual(1, len(card["sources"]))
        self.assertEqual([], card["source_headers"])
        self.assertEqual(str(FIXTURE), card["local_only"]["sources_root"])
        self.assertEqual(
            str(FIXTURE / "knowledge/ops/ascendc/apis/aligned_api.md"),
            card["local_only"]["local_path"],
        )
        self.assertNotIn("local_path", card)
        self.assertIn("index", card)
        links = {link["href"]: link for link in card["links"]}
        self.assertEqual(
            "ops/ascendc/apis/data_copy_pad.md",
            links["data_copy_pad.md"]["resolved_path"],
        )
        self.assertEqual(
            "ops/ascendc/apis/data_copy_pad.md",
            links["/ops/ascendc/apis/data_copy_pad.md"]["resolved_path"],
        )
        self.assertNotIn("resolved_path", links["#details"])
        self.assertEqual(
            "ops/ascendc/apis/index.md", links["index.md"]["resolved_path"]
        )
        self.assertNotIn("https://example.com/docs", links)
        self.assertNotIn("fake_target.md", links)
        self.assertEqual(
            [
                {
                    "url": "https://raw.gitcode.com/cann/asc-devkit/raw/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/figures/net_topology.png",
                    "alt": "pipeline",
                }
            ],
            card["images"],
        )

    def test_concept_and_markdown_paths_are_equivalent(self) -> None:
        _error_a, card_a = self.read({"path": "ops/ascendc/apis/data_copy_pad"})
        _error_b, card_b = self.read({"path": "ops/ascendc/apis/data_copy_pad.md"})
        self.assertEqual(card_a["path"], card_b["path"])
        self.assertEqual(card_a["card_sha256"], card_b["card_sha256"])
        self.assertEqual(3, len(card_b["sources"]))

    def test_path_safety(self) -> None:
        for bad in (
            "../../etc/passwd",
            "/etc/passwd",
            "ops/../../secret.md",
            "nonexistent/card.md",
            "ops/ascendc/apis/data_copy_pad.md/../../escape.md",
        ):
            with self.subTest(path=bad):
                is_error, text = self.read({"path": bad})
                self.assertTrue(is_error, bad)
                self.assertTrue(
                    "escape" in text
                    or "does not exist" in text
                    or "segments" in text
                    or "Bundle-relative" in text,
                    text,
                )

    def test_offset_beyond_end_reports_valid_range(self) -> None:
        is_error, text = self.read(
            {"path": "ops/ascendc/apis/data_copy_pad.md", "offset": 10000}
        )
        self.assertTrue(is_error)
        self.assertIn("beyond the end", text)
        self.assertIn("valid offsets are 0..", text)

    def test_big_card_pagination_in_five_pages(self) -> None:
        full_path = FIXTURE / "knowledge/ops/ascendc/apis/appendix_table.md"
        expected = full_path.read_text(encoding="utf-8")
        collected = []
        offset = 0
        pages = 0
        while True:
            is_error, card = self.read(
                {"path": "ops/ascendc/apis/appendix_table.md", "offset": offset, "limit": 400}
            )
            self.assertFalse(is_error)
            self.assertEqual(offset, card["offset"])
            collected.append(card["content"])
            pages += 1
            if not card["truncated"]:
                self.assertIsNone(card["next_offset"])
                break
            self.assertEqual(offset + card["returned_lines"], card["next_offset"])
            offset = card["next_offset"]
            self.assertLess(pages, 10)
        self.assertEqual(5, pages)
        self.assertEqual(1985, card["total_lines"])
        self.assertEqual(expected, "".join(collected))

    def test_limit_is_clamped_to_500(self) -> None:
        is_error, card = self.read(
            {"path": "ops/ascendc/apis/appendix_table.md", "limit": 5000}
        )
        self.assertFalse(is_error)
        self.assertEqual(500, card["returned_lines"])
        self.assertTrue(card["truncated"])
        self.assertEqual(500, card["next_offset"])

    def test_navigation_index_is_readable(self) -> None:
        is_error, index = self.read({"path": "ops/ascendc/apis/index.md"})
        self.assertFalse(is_error)
        self.assertEqual("ops/ascendc/apis/index", index["path"])
        hrefs = {link["href"] for link in index["links"]}
        self.assertIn("data_copy_pad.md", hrefs)


class EndToEndPipelineTests(unittest.TestCase):
    def test_discover_search_read_and_follow_links(self) -> None:
        client = StdioClient(FIXTURE, HOME_DIR)
        try:
            client.initialize()
            _error, discovery = client.call_tool("discover", {})
            self.assertEqual(3, discovery["cards"])
            _error, results = client.call_tool(
                "search",
                {
                    "query": "DataCopyPad",
                    "technology": "ascendc",
                    "platform": ["a2"],
                    "match": "literal",
                    "limit": 5,
                },
            )
            self.assertGreaterEqual(results["count"], 1)
            first = results["results"][0]
            _error, card = client.call_tool("read_card", {"path": first["path"]})
            self.assertFalse(_error)
            self.assertEqual(first["path"], card["path"])
            resolved = [
                link["resolved_path"]
                for link in card["links"]
                if "resolved_path" in link
                and link["resolved_path"].endswith("aligned_api.md")
            ]
            self.assertEqual(1, len(resolved))
            _error, second = client.call_tool(
                "read_card", {"path": resolved[0]}
            )
            self.assertFalse(_error)
            self.assertEqual("ops/ascendc/apis/aligned_api", second["path"])
            self.assertEqual("Aligned API helper", second["title"])
        finally:
            client.close()


class StdioLoggingTests(unittest.TestCase):
    def test_call_log_rows_match_direct_cli_evidence(self) -> None:
        """v2 log rows must be reproducible against the direct CLI truth."""
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-v2-"))
        try:
            client = StdioClient(
                FIXTURE, HOME_DIR, CANNBOT_MCP_LOG="on", CANNBOT_MCP_LOG_DIR=str(log_dir)
            )
            try:
                client.initialize()
                _error, _discovery = client.call_tool("discover", {})
                search_arguments = {
                    "query": "DataCopyPad",
                    "platform": ["a2"],
                    "match": "literal",
                    "limit": 5,
                }
                _error, search_payload = client.call_tool("search", search_arguments)
                self.assertFalse(_error)
                _error, card_payload = client.call_tool(
                    "read_card",
                    {"path": "ops/ascendc/apis/data_copy_pad.md", "offset": 0, "limit": 10},
                )
                self.assertFalse(_error)
                _error, failure_text = client.call_tool(
                    "search", {"query": "DataCopyPad"}
                )
                self.assertTrue(_error, failure_text)
            finally:
                client.close()
            direct = run_direct_cli(
                FIXTURE,
                [
                    "search", "--json", "--query", "DataCopyPad",
                    "--platform", "a2", "--match", "literal", "--limit", "5",
                ],
            )
            self.assertEqual(0, direct.returncode, direct.stderr)
            direct_payload = json.loads(direct.stdout)

            files = list(log_dir.glob("*.jsonl"))
            self.assertEqual(1, len(files))
            rows = [
                json.loads(line)
                for line in files[0].read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                ["discover", "search", "read_card", "search"],
                [row["tool"] for row in rows],
            )
            for row in rows[:3]:
                self.assertEqual("mcp-call-log.v2", row["schema"])
                self.assertRegex(row["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
                self.assertTrue(re.fullmatch(r"[0-9a-f]{16}", row["call_id"]))
                self.assertIsNone(row["jsonrpc_id"])
                self.assertTrue(
                    re.fullmatch(r"[0-9a-f]{64}", row["response_sha256"] or "")
                )
                self.assertGreater(row["response_bytes"] or 0, 0)
            # one stable unique call id per call row, placed after ts and
            # before boot_id: multi-instance union merges deduplicate only
            # verbatim copies of the same row.
            self.assertEqual(len(rows), len({row["call_id"] for row in rows}))
            self.assertEqual(
                ["schema", "ts", "call_id", "boot_id"], list(rows[0])[:4]
            )

            search_row = rows[1]
            self.assertEqual(
                direct_payload["request_sha256"], search_row["request_sha256"]
            )
            self.assertEqual(
                [result["path"] for result in direct_payload["results"]],
                search_row["hits"],
            )
            self.assertEqual(
                [result["score"] for result in direct_payload["results"]],
                search_row["scores"],
            )
            self.assertEqual(len(search_row["hits"]), len(search_row["scores"]))

            read_row = rows[2]
            expected_sha = hashlib.sha256(
                (FIXTURE / "knowledge/ops/ascendc/apis/data_copy_pad.md").read_bytes()
            ).hexdigest()
            self.assertEqual(expected_sha, read_row["card_sha256"])
            self.assertEqual(card_payload["total_lines"], read_row["total_lines"])
            self.assertEqual(card_payload["returned_lines"], read_row["returned_lines"])
            self.assertEqual(card_payload["truncated"], read_row["truncated"])

            failure_row = rows[3]
            self.assertEqual("mcp-call-log.v2", failure_row["schema"])
            self.assertFalse(failure_row["ok"])
            self.assertEqual("platform_missing", failure_row["error_kind"])
            self.assertIsNone(failure_row["response_sha256"])
            self.assertIsNone(failure_row["request_sha256"])
        finally:
            shutil.rmtree(log_dir, ignore_errors=True)

    def test_stdio_logging_is_off_by_default_and_on_when_enabled(self) -> None:
        quiet_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-quiet-"))
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-logs-"))
        try:
            client = StdioClient(FIXTURE, HOME_DIR, CANNBOT_MCP_LOG_DIR=str(quiet_dir))
            try:
                client.initialize()
                client.call_tool("discover", {})
            finally:
                client.close()
            self.assertEqual([], list(quiet_dir.glob("**/*.jsonl")))

            tracked = [
                FIXTURE / "knowledge/ops/ascendc/apis/data_copy_pad.md",
                FIXTURE / "governance/schemas/registries.yaml",
                FIXTURE / "artifacts/indexes/knowledge.sqlite3",
            ]
            before = [(path, path.stat().st_mtime_ns) for path in tracked]
            client = StdioClient(
                FIXTURE, HOME_DIR, CANNBOT_MCP_LOG="on", CANNBOT_MCP_LOG_DIR=str(log_dir)
            )
            try:
                client.initialize()
                client.call_tool("discover", {})
                client.call_tool("search", {"query": "DataCopyPad", "platform": ["a2"]})
            finally:
                client.close()
            after = [(path, path.stat().st_mtime_ns) for path in tracked]
            self.assertEqual(before, after)
            files = list(log_dir.glob("*.jsonl"))
            self.assertEqual(1, len(files))
            rows = [
                json.loads(line)
                for line in files[0].read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(2, len(rows))
            self.assertEqual(["discover", "search"], [row["tool"] for row in rows])
            self.assertTrue(all(row["ok"] for row in rows))
            self.assertTrue(all(row["transport"] == "stdio" for row in rows))
            self.assertTrue(all(row["principal"] is None for row in rows))
            self.assertIsNotNone(rows[1]["request_sha256"])
            self.assertIsNotNone(rows[1]["index"])
        finally:
            shutil.rmtree(quiet_dir, ignore_errors=True)
            shutil.rmtree(log_dir, ignore_errors=True)

    def test_failed_calls_are_logged_too(self) -> None:
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-logs-"))
        try:
            client = StdioClient(
                FIXTURE, HOME_DIR, CANNBOT_MCP_LOG="on", CANNBOT_MCP_LOG_DIR=str(log_dir)
            )
            try:
                client.initialize()
                is_error, _text = client.call_tool("search", {"query": "DataCopyPad"})
                self.assertTrue(is_error)
            finally:
                client.close()
            files = list(log_dir.glob("*.jsonl"))
            self.assertEqual(1, len(files))
            rows = [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(rows))
            self.assertFalse(rows[0]["ok"])
            self.assertIn("platform is required", rows[0]["error"])
        finally:
            shutil.rmtree(log_dir, ignore_errors=True)


class HttpTransportTests(unittest.TestCase):
    def test_health_endpoint_answers_without_auth(self) -> None:
        server = HttpServer(FIXTURE, HOME_DIR, tokens="cbk_ready:ready")
        try:
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.port}/health", method="GET"
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                self.assertEqual(200, response.status)
                payload = json.loads(response.read().decode("utf-8"))
            self.assertEqual({"status": "ok"}, payload)
        finally:
            server.close()

    def test_auth_matrix_and_principal_logging(self) -> None:
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-http-"))
        server = HttpServer(
            FIXTURE, HOME_DIR,
            tokens="cbk_alice:alice, cbk_bob:bob, cbk_ready:ready",
            log_dir=log_dir,
        )
        try:
            status, _headers, messages = server.post(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, token="cbk_alice"
            )
            self.assertEqual(200, status)
            self.assertEqual(
                {"discover", "search", "read_card"},
                {tool["name"] for tool in messages[0]["result"]["tools"]},
            )
            status, _headers, messages = server.post(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "discover", "arguments": {}}},
                token="cbk_alice",
            )
            self.assertEqual(200, status)
            self.assertFalse(messages[0]["result"].get("isError"))
            status, _headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}, token="cbk_wrong"
            )
            self.assertEqual(401, status)
            status, _headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}
            )
            self.assertEqual(401, status)
        finally:
            server.close()
        rows = []
        for path in sorted(log_dir.glob("*.jsonl")):
            rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
        events = [row for row in rows if row.get("event")]
        calls = [row for row in rows if not row.get("event")]
        self.assertEqual(1, len(calls))
        self.assertEqual("http", calls[0]["transport"])
        self.assertEqual("alice", calls[0]["principal"])
        self.assertTrue(calls[0]["ok"])
        self.assertEqual({"no_match", "no_token"}, {event["reason"] for event in events})
        self.assertTrue(all(event["event"] == "auth_failed" for event in events))
        shutil.rmtree(log_dir, ignore_errors=True)

    def test_empty_token_list_refuses_to_start(self) -> None:
        process = subprocess.Popen(
            server_command(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=server_environment(
                FIXTURE,
                HOME_DIR,
                CANNBOT_MCP_TRANSPORT="http",
                CANNBOT_MCP_PORT=str(free_port()),
                CANNBOT_MCP_TOKENS="",
            ),
        )
        _out, err = process.communicate(timeout=60)
        self.assertNotEqual(0, process.returncode)
        self.assertIn("CANNBOT_MCP_TOKENS", err)

    def test_rate_limit_per_token(self) -> None:
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-rate-"))
        server = HttpServer(
            FIXTURE, HOME_DIR,
            tokens="cbk_alice:alice, cbk_bob:bob, cbk_ready:ready",
            rate_limit=3,
            log_dir=log_dir,
        )
        try:
            statuses = []
            for identifier in range(3):
                status, headers, _messages = server.post(
                    {"jsonrpc": "2.0", "id": identifier, "method": "tools/list"},
                    token="cbk_alice",
                )
                statuses.append(status)
                self.assertNotEqual(429, status)
            status, headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 99, "method": "tools/call",
                 "params": {"name": "discover", "arguments": {}}},
                token="cbk_alice",
            )
            self.assertEqual(429, status)
            self.assertGreaterEqual(retry_after_of(headers), 1)
            status, _headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 10, "method": "tools/list"}, token="cbk_bob"
            )
            self.assertEqual(200, status)
        finally:
            server.close()
        rows = []
        for path in sorted(log_dir.glob("*.jsonl")):
            rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
        limited = [row for row in rows if row.get("event") == "rate_limited"]
        self.assertEqual(1, len(limited))
        self.assertEqual("alice", limited[0]["principal"])
        self.assertEqual("discover", limited[0]["tool"])
        shutil.rmtree(log_dir, ignore_errors=True)

    def test_auth_failure_ip_cooldown_blocks_even_valid_tokens(self) -> None:
        server = HttpServer(
            FIXTURE, HOME_DIR,
            tokens="cbk_alice:alice, cbk_ready:ready",
            rate_limit=1000,
        )
        try:
            statuses = []
            for identifier in range(10):
                status, _headers, _messages = server.post(
                    {"jsonrpc": "2.0", "id": identifier, "method": "tools/list"},
                    token="cbk_wrong",
                )
                statuses.append(status)
            self.assertEqual([401] * 10, statuses)
            status, headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 20, "method": "tools/list"},
                token="cbk_alice",
            )
            self.assertEqual(429, status)
            self.assertGreaterEqual(retry_after_of(headers), 1)
        finally:
            server.close()

    def test_auth_failure_body_sent_in_second_packet_reads_full_response(self) -> None:
        """Regression: auth-failure responses must survive two-packet requests.

        urllib-style clients send the POST headers and body in separate TCP
        segments; the auth-failure branches used to answer and close without
        reading the body, so the second packet hit a closed socket and the
        kernel answered RST, surfacing as ConnectionResetError while reading
        the response. Mirrors the drain-before-respond behaviour the rate
        limit branch already had.
        """

        def raw_two_packet_post(
            port: int, body: bytes, authorization: str | None
        ) -> tuple[int, bytes]:
            headers = [
                "POST /mcp HTTP/1.1",
                "Host: 127.0.0.1",
                "Content-Type: application/json",
                "Accept: application/json, text/event-stream",
                f"Content-Length: {len(body)}",
            ]
            if authorization is not None:
                headers.append(f"Authorization: Bearer {authorization}")
            request = ("\r\n".join(headers) + "\r\n\r\n").encode("ascii")
            with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
                sock.sendall(request)
                # Give the server time to answer the headers packet and close
                # the connection before the body packet lands, pinning the
                # race that produced intermittent resets with real clients.
                time.sleep(0.1)
                sock.sendall(body)
                sock.shutdown(socket.SHUT_WR)
                chunks: list[bytes] = []
                while True:
                    try:
                        chunk = sock.recv(65536)
                    except ConnectionResetError:
                        self.fail("connection reset while reading auth-failure response")
                    if not chunk:
                        break
                    chunks.append(chunk)
            raw = b"".join(chunks)
            head, _, payload = raw.partition(b"\r\n\r\n")
            self.assertNotEqual(b"", payload, raw)
            status = int(head.split(b"\r\n")[0].split(b" ")[1])
            header_lines = dict(
                line.split(b": ", 1)
                for line in head.split(b"\r\n")[1:]
                if b": " in line
            )
            declared = int(header_lines[b"content-length"])
            self.assertEqual(declared, len(payload))
            return status, payload

        body = json.dumps(
            {"jsonrpc": "2.0", "id": 7, "method": "tools/list"}
        ).encode("utf-8")
        # 30 auth failures would trip the 10-failure IP cooldown; insert a
        # valid-token call every third iteration to reset the failure window.
        server = HttpServer(
            FIXTURE, HOME_DIR,
            tokens="cbk_alice:alice, cbk_ready:ready",
            rate_limit=1000,
        )
        try:
            raw_failures = 0
            for index in range(30):
                with self.subTest(iteration=index):
                    if index % 3 == 2:
                        status, _headers, _messages = server.post(
                            {"jsonrpc": "2.0", "id": 8, "method": "tools/list"},
                            token="cbk_alice",
                        )
                        self.assertEqual(200, status)
                        continue
                    if index % 2 == 0:
                        status, payload = raw_two_packet_post(server.port, body, None)
                    else:
                        status, payload = raw_two_packet_post(
                            server.port, body, "cbk_wrong"
                        )
                    raw_failures += 1
                    self.assertEqual(401, status)
                    message = json.loads(payload)
                    self.assertEqual(-32600, message["error"]["code"])
            self.assertEqual(20, raw_failures)
        finally:
            server.close()

    def test_http_log_off_is_respected(self) -> None:
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-off-"))
        try:
            server = HttpServer(
                FIXTURE, HOME_DIR,
                tokens="cbk_alice:alice, cbk_ready:ready",
                log_dir=log_dir,
                log_mode="off",
            )
            try:
                status, _headers, _messages = server.post(
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    token="cbk_alice",
                )
                self.assertEqual(200, status)
            finally:
                server.close()
            self.assertEqual([], list(log_dir.glob("**/*.jsonl")))
        finally:
            shutil.rmtree(log_dir, ignore_errors=True)


class LogUploadTests(unittest.TestCase):
    """Periodic upload: rows reach a real bare remote; LOG=off stays quiet."""

    @staticmethod
    def make_bare_remote(path: Path) -> Path:
        completed = subprocess.run(
            ["git", "init", "--bare", str(path)],
            check=False, capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stderr
        completed = subprocess.run(
            ["git", "-C", str(path), "symbolic-ref", "HEAD", "refs/heads/main"],
            check=False, capture_output=True, text=True,
        )
        assert completed.returncode == 0, completed.stderr
        return path

    def test_upload_thread_ships_call_rows_to_the_remote(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="cannbot-mcp-upload-"))
        log_dir = base / "logs"
        bare = self.make_bare_remote(base / "remote.git")
        server = HttpServer(
            FIXTURE, HOME_DIR,
            tokens="cbk_alice:alice, cbk_ready:ready",
            log_dir=log_dir,
            upload_remote=bare,
            upload_interval=1,
        )
        try:
            status, _headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                 "params": {"name": "discover", "arguments": {}}},
                token="cbk_alice",
            )
            self.assertEqual(200, status)
            time.sleep(2.5)
        finally:
            server.close()
        try:
            clone = base / "clone"
            completed = subprocess.run(
                ["git", "clone", "--branch", "main", str(bare), str(clone)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            uploaded = list(clone.glob("calls-*.jsonl"))
            self.assertEqual(1, len(uploaded))
            rows = [
                json.loads(line)
                for line in uploaded[0].read_text(encoding="utf-8").splitlines()
            ]
            calls = [row for row in rows if not row.get("event")]
            self.assertEqual(1, len(calls))
            self.assertEqual("discover", calls[0]["tool"])
            self.assertTrue(calls[0]["ok"])
            self.assertEqual("alice", calls[0]["principal"])
            self.assertRegex(calls[0]["boot_id"], r"^[0-9a-f]{8,12}$")
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_log_off_leaves_the_uploader_without_payload(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="cannbot-mcp-offup-"))
        log_dir = base / "logs"
        bare = self.make_bare_remote(base / "remote.git")
        server = HttpServer(
            FIXTURE, HOME_DIR,
            tokens="cbk_alice:alice, cbk_ready:ready",
            log_dir=log_dir,
            log_mode="off",
            upload_remote=bare,
            upload_interval=1,
        )
        try:
            status, _headers, _messages = server.post(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                token="cbk_alice",
            )
            self.assertEqual(200, status)
            time.sleep(2.0)
        finally:
            server.close()
        try:
            self.assertEqual([], list(log_dir.glob("**/*.jsonl")))
            completed = subprocess.run(
                ["git", "-C", str(bare), "rev-list", "--all", "--count"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual("0", completed.stdout.strip())
        finally:
            shutil.rmtree(base, ignore_errors=True)


class SubprocessGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.mkdtemp(prefix="cannbot-mcp-stub-")
        self.root = Path(self.temporary) / "knowledge-root"
        shutil.copytree(ROOT / "governance", self.root / "governance")
        apis = self.root / "knowledge/ops/ascendc/apis"
        apis.mkdir(parents=True)
        (self.root / "knowledge/index.md").write_text(
            '---\nokf_version: "0.2"\n---\n', encoding="utf-8"
        )
        self.marker = Path(self.temporary) / "concurrency.log"
        self.scripts = self.root / ".agents/skills/knowledge-query/scripts"
        self.scripts.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temporary, ignore_errors=True)

    def write_stub(self, body: str) -> None:
        (self.scripts / "knowledge_query.py").write_text(body, encoding="utf-8")

    def test_queued_calls_complete_without_loss(self) -> None:
        self.write_stub(
            "import json, time\n"
            f"marker = {str(self.marker)!r}\n"
            "with open(marker, 'a') as stream:\n"
            "    stream.write('start\\n'); stream.flush()\n"
            "time.sleep(1.5)\n"
            "with open(marker, 'a') as stream:\n"
            "    stream.write('end\\n'); stream.flush()\n"
            "print(json.dumps({'stub': True, 'cards': 1}))\n"
        )
        client = StdioClient(
            self.root, HOME_DIR, CANNBOT_MCP_MAX_SUBPROCS="1"
        )
        try:
            client.initialize()
            threads = []
            results: list = [None] * 3

            def worker(index: int) -> None:
                results[index] = client.call_tool("discover", {})

            for index in range(3):
                thread = threading.Thread(target=worker, args=(index,))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join(120)
            self.assertTrue(all(item is not None for item in results))
            for is_error, payload in results:
                self.assertFalse(is_error)
                self.assertEqual({"stub": True, "cards": 1}, payload)
            events = self.marker.read_text().splitlines()
            self.assertEqual(["start", "end"] * 3, events)
        finally:
            client.close()

    def test_hung_cli_times_out_with_structured_error(self) -> None:
        self.write_stub("import time\ntime.sleep(60)\n")
        client = StdioClient(
            self.root, HOME_DIR, CANNBOT_MCP_SUBPROC_TIMEOUT="2"
        )
        try:
            client.initialize()
            started = time.monotonic()
            is_error, text = client.call_tool("discover", {})
            elapsed = time.monotonic() - started
            self.assertTrue(is_error)
            self.assertIn("timeout", text)
            self.assertLess(elapsed, 30)
        finally:
            client.close()


class AnalyzeLogsTests(unittest.TestCase):
    def test_three_dimensions_from_constructed_logs(self) -> None:
        log_dir = Path(tempfile.mkdtemp(prefix="cannbot-mcp-analyze-"))
        output = log_dir.parent / "report.json"
        try:
            rows = [
                {
                    "ts": "2026-10-10T08:00:00Z", "transport": "http",
                    "principal": "zhangsan", "tool": "search",
                    "args": {"query": "TileLang sink", "technology": "triton",
                             "platform": ["a2"], "match": "literal", "limit": 5},
                    "ok": True, "count": 0, "latency_ms": 100.0,
                    "request_sha256": "s1", "index": None, "hits": [], "error": None,
                },
                {
                    "ts": "2026-10-10T08:30:00Z", "transport": "http",
                    "principal": "lisi", "tool": "search",
                    "args": {"query": "TileLang sink", "technology": "triton",
                             "platform": ["a2"], "match": "literal", "limit": 5},
                    "ok": True, "count": 0, "latency_ms": 90.0,
                    "request_sha256": "s1", "index": None, "hits": [], "error": None,
                },
                {
                    "ts": "2026-10-10T09:00:00Z", "transport": "http",
                    "principal": "lisi", "tool": "search",
                    "args": {"query": "DataCopyPad", "platform": ["a2"]},
                    "ok": True, "count": 1, "latency_ms": 80.0,
                    "request_sha256": "s2", "index": None,
                    "hits": ["ops/ascendc/apis/data_copy_pad.md"], "error": None,
                },
                {
                    "ts": "2026-10-10T10:00:00Z", "transport": "stdio",
                    "principal": None, "tool": "read_card",
                    "args": {"path": "ops/ascendc/apis/data_copy_pad.md",
                             "offset": 0, "limit": 200},
                    "ok": True, "count": None, "latency_ms": 20.0,
                    "request_sha256": None, "index": None, "hits": None, "error": None,
                },
            ]
            (log_dir / "calls-2026-10-10.jsonl").write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MCP_SERVER_DIR / "analyze_logs.py"),
                    "--log-dir", str(log_dir),
                    "--output", str(output),
                ],
                check=False, capture_output=True, text=True, cwd=str(ROOT),
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(report["anonymous_mode"])
            self.assertEqual(1, len(report["zero_hit"]))
            self.assertEqual(2, report["zero_hit"][0]["occurrences"])
            self.assertEqual(2, report["zero_hit"][0]["distinct_principals"])
            self.assertIn("查询词", report["zero_hit"][0]["issue_text"])
            self.assertIn("命中数：0", report["zero_hit"][0]["issue_text"])
            popularity = {
                item["query"]: item for item in report["query_popularity"]
            }
            self.assertEqual(2, popularity["TileLang sink"]["occurrences"])
            self.assertEqual(
                [{"path": "ops/ascendc/apis/data_copy_pad.md", "count": 1}],
                popularity["DataCopyPad"]["top_hits"],
            )
            self.assertEqual(1, len(report["read_popularity"]))
            self.assertEqual("ops", report["read_popularity"][0]["domain"])
            self.assertIn("匿名模式", completed.stdout) if report["anonymous_mode"] else None
        finally:
            shutil.rmtree(log_dir, ignore_errors=True)
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
