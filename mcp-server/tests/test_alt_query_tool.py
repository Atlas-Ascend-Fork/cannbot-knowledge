"""alt_query exposure on the MCP search tool face.

The CLI and evals have supported the bilingual dual-search leg
(alt-query + rank-interleave fusion) all along; ticket B3 opens it to
MCP clients. These tests go through the tool surface - the registered
tool schema and the search() tool function with an injected engine - and
assert the bilingual payload shape, parity with the CLI (the subprocess
adapter is the CLI passthrough) and the CLI-consistent errors for the
illegal combinations.
"""

from __future__ import annotations

import asyncio
import inspect
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))

from test_retrieval_engine import (  # noqa: E402
    engine_fixture_root,
    error_of,
    run_search,
)

import server  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

ILLEGAL_COMBINATIONS = [
    (
        "--alt-query requires --match text; literal queries must not be rewritten",
        {"query": "DataCopyPad", "match": "literal", "alt_query": "alignment"},
    ),
    (
        "--alt-query must not be empty",
        {"query": "DataCopyPad", "alt_query": ""},
    ),
    (
        "--alt-query must not be empty",
        {"query": "DataCopyPad", "alt_query": "   "},
    ),
    (
        "--alt-query must differ from --query",
        {"query": "DataCopyPad", "alt_query": "DataCopyPad"},
    ),
    (
        "--alt-query must differ from --query",
        {"query": "DataCopyPad", "alt_query": "  datacopypad  "},
    ),
]


def validated_tool_arguments(**arguments: object) -> dict:
    """Resolve the pydantic Field defaults the MCP framework resolves.

    The SDK validates a client's arguments and calls the tool body with
    every parameter resolved; a direct python call would see raw FieldInfo
    defaults instead. This helper applies the same declared defaults so
    the tests exercise the tool body under production call conventions.
    """
    resolved = dict(arguments)
    for name, parameter in inspect.signature(server.search).parameters.items():
        if name in resolved or parameter.default is inspect.Parameter.empty:
            continue
        default = parameter.default
        resolved[name] = getattr(default, "default", default)
    return resolved


def tool_search(**arguments: object) -> dict:
    return asyncio.run(server.search(**validated_tool_arguments(**arguments)))  # type: ignore[arg-type]


def tool_search_error(**arguments: object) -> ToolError:
    try:
        tool_search(**arguments)
    except ToolError as caught:
        return caught
    raise AssertionError("expected a structured tool error")


class AltQueryToolFaceTests(unittest.TestCase):
    """Bilingual dual search through the MCP tool surface."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = engine_fixture_root(Path(self.temporary.name) / "root")
        self.cli_engine = server.CliRunner(
            self.root / ".agents/skills/knowledge-query/scripts/knowledge_query.py",
            self.root,
            2,
            30.0,
        )
        self.engine = server.InProcessEngine(self.root)
        self.addCleanup(self.engine.close)
        saved_engine, server._ENGINE = server._ENGINE, self.engine

        def restore_engine() -> None:
            server._ENGINE = saved_engine

        self.addCleanup(restore_engine)

    def test_tool_schema_exposes_alt_query_as_optional(self) -> None:
        tools = asyncio.run(server.mcp_server.list_tools())
        schema = next(t for t in tools if t.name == "search").input_schema
        self.assertIn("alt_query", schema["properties"])
        self.assertNotIn("alt_query", schema.get("required", []))

    def test_alt_query_returns_bilingual_payload(self) -> None:
        payload = tool_search(
            query="DataCopyPad 对齐",
            alt_query="alignment copy padding",
            platform=["950"],
            limit=5,
        )
        self.assertEqual("knowledge-search.v6", payload["schema_version"])
        self.assertEqual("alignment copy padding", payload["alt_query"])
        fusion = payload["fusion"]
        self.assertEqual("rank-interleave", fusion["method"])
        self.assertEqual(["original", "alt"], fusion["order"])
        self.assertIsInstance(fusion["original_hits"], int)
        self.assertIsInstance(fusion["alt_hits"], int)
        self.assertTrue(payload["results"])
        for result in payload["results"]:
            self.assertIn("original_rank", result["bilingual"])
            self.assertIn("alt_rank", result["bilingual"])
            self.assertIn("score_leg", result["bilingual"])
            self.assertIn("original_score", result["bilingual"])
            self.assertIn("alt_score", result["bilingual"])

    def test_bilingual_payload_matches_the_cli_field_by_field(self) -> None:
        request = {
            "query": "DataCopyPad 对齐",
            "alt_query": "alignment copy padding",
            "platform": ["950"],
            "limit": 5,
        }
        cli_payload = run_search(self.cli_engine, **request)
        tool_payload = tool_search(**request)
        self.assertEqual(cli_payload, tool_payload)
        self.assertEqual("knowledge-search.v6", cli_payload["schema_version"])

    def test_bilingual_legs_share_every_filter(self) -> None:
        both_legs_hit = tool_search(
            query="DataCopyPad",
            alt_query="helper",
            platform=["950"],
            domain="ops",
            limit=5,
        )
        for result in both_legs_hit["results"]:
            self.assertEqual("ops", result["domain"])
            self.assertIn("950", result["platforms"])

    def test_illegal_combinations_fail_with_the_cli_errors(self) -> None:
        for message, arguments in ILLEGAL_COMBINATIONS:
            with self.subTest(arguments=arguments):
                exc = tool_search_error(platform=["950"], **arguments)
                self.assertEqual("cli_error", exc.kind)
                self.assertIn(message, str(exc))

    def test_illegal_combination_errors_match_the_cli(self) -> None:
        for message, arguments in ILLEGAL_COMBINATIONS:
            with self.subTest(arguments=arguments):
                request = dict(arguments, platform=["950"])
                cli_exc = error_of(
                    lambda request=request: run_search(self.cli_engine, **request)
                )
                tool_exc = tool_search_error(**request)
                self.assertEqual(cli_exc.kind, tool_exc.kind)
                self.assertIn(message, str(cli_exc))
                self.assertIn(message, str(tool_exc))

    def test_without_alt_query_the_payload_stays_single_leg(self) -> None:
        payload = tool_search(query="DataCopyPad", platform=["950"], limit=5)
        self.assertEqual("knowledge-search.v5", payload["schema_version"])
        self.assertNotIn("alt_query", payload)
        self.assertNotIn("fusion", payload)
        for result in payload["results"]:
            self.assertNotIn("bilingual", result)


if __name__ == "__main__":
    unittest.main()
