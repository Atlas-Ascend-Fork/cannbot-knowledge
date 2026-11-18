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

import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from urllib.parse import unquote
from unittest.mock import patch

from evals.run_retrieval import run_cases


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_index.py"
QUERY = ROOT / ".agents/skills/knowledge-query/scripts/knowledge_query.py"
STATE = ROOT / ".agents/skills/knowledge-query/scripts/retrieval_state.py"
OUTCOME = ROOT / ".agents/skills/knowledge-query/scripts/retrieval_outcome.py"

SYNTHETIC_CARD = """---
type: API
title: Synthetic API contract
description: Deterministic API fixture for retrieval tests.
tags: [task.lookup, topic.compilation]
status: stable
sources:
  - resource: https://example.com/cann/synthetic-api
    role: primary
created_at: "2026-08-18T00:00:00Z"
updated_at: "2026-08-18T00:00:00Z"
platforms: [a2]
---

# Synthetic API contract

This fixture verifies indexed API lookup and audit behavior without depending on
repository knowledge cards.
"""


def make_root(target: Path) -> None:
    shutil.copytree(ROOT / "governance", target / "governance")
    api_root = target / "knowledge/ops/ascendc/apis"
    api_root.mkdir(parents=True)
    (target / "knowledge/index.md").write_text(
        '---\nokf_version: "0.2"\n---\n\n# Test knowledge\n',
        encoding="utf-8",
    )
    (target / "knowledge/ops/index.md").write_text("# Test ops\n", encoding="utf-8")
    (target / "knowledge/ops/ascendc/index.md").write_text(
        "# Ascend C 算子知识\n\n- [API](apis/index.md)：测试夹具中的 API 知识。\n",
        encoding="utf-8",
    )
    (api_root / "index.md").write_text(
        "# API\n\n- [Synthetic API contract](synthetic_api.md)：确定性检索测试夹具。\n",
        encoding="utf-8",
    )
    (api_root / "synthetic_api.md").write_text(SYNTHETIC_CARD, encoding="utf-8")


def run_index(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INDEX), *arguments, "--knowledge-root", str(root)],
        check=False,
        text=True,
        capture_output=True,
    )


class RetrievalCaseTests(unittest.TestCase):
    def run_mocked_case(self, case, hits, returncode=0, *, quality=None, quality_gate=False):
        output, errors = io.StringIO(), io.StringIO()
        completed = subprocess.CompletedProcess(
            [], returncode, json.dumps({"count": len(hits), "hits": hits}), "query failed"
        )
        with patch("evals.run_retrieval.subprocess.run", return_value=completed), \
                patch("evals.run_retrieval.time.perf_counter", side_effect=[0.0, 1.0]), \
                redirect_stdout(output), redirect_stderr(errors):
            result = run_cases(
                {"cases": [{"id": "fixture", "query": "query", **case}], "quality": quality or {}},
                {"repository": ROOT}, quality_gate=quality_gate,
            )
        return result, output.getvalue(), errors.getvalue()

    def test_alternatives_do_not_replace_other_required_evidence(self):
        case = {"expected": ["c"], "expected_any": [["a", "b"]]}
        for paths, expected_result, recall in ((["b", "c"], 0, "1.000"),
                                                (["a", "b"], 1, "0.500"),
                                                (["c"], 1, "0.500")):
            with self.subTest(paths=paths):
                hits = [{"path": path, "rank": rank} for rank, path in enumerate(paths, 1)]
                result, output, _ = self.run_mocked_case(case, hits)
                self.assertEqual(expected_result, result)
                self.assertIn(f"recall@k={recall}", output)

    def test_failed_query_stays_in_quality_denominator(self):
        result, output, _ = self.run_mocked_case({"expected_any": [["a", "b"]]}, [], 2)
        self.assertEqual(1, result)
        self.assertIn("recall@k=0.000 MRR=0.000", output)

    def test_scope_is_checked_even_when_expected_card_is_returned(self):
        case = {"expected": ["a"], "filters": {"type": "apis", "platform": ["a2", "a3"]}}
        for profile, platforms, expected_result in (
            ("apis", ["a2", "a3"], 0), ("apis", ["agnostic"], 0),
            ("runbooks", ["a2", "a3"], 1), ("apis", ["a2"], 1),
        ):
            with self.subTest(profile=profile, platforms=platforms):
                result, _, _ = self.run_mocked_case(
                    case, [{"path": "a", "rank": 1, "profile": profile, "platforms": platforms}]
                )
                self.assertEqual(expected_result, result)

    def test_invalid_or_groups_are_not_vacuous_success(self):
        for groups in ([[]], ["not-a-list"], [[""]]):
            with self.subTest(groups=groups), self.assertRaisesRegex(ValueError, "nonempty"):
                self.run_mocked_case({"expected_any": groups}, [])

    def test_quality_gate_accepts_partial_recall_above_threshold_but_strict_mode_fails(self):
        case = {"expected": ["c"], "expected_any": [["a", "b"]]}
        quality = {"min_recall_at_k": 0.49, "min_mrr": 0.49}
        hits = [{"path": "unrelated", "rank": 1}, {"path": "b", "rank": 2}]
        for quality_gate, expected_result in ((False, 1), (True, 0)):
            with self.subTest(quality_gate=quality_gate):
                result, output, errors = self.run_mocked_case(
                    case, hits, quality=quality, quality_gate=quality_gate,
                )
                self.assertEqual(expected_result, result)
                self.assertIn("recall@k=0.500 MRR=0.500 p95=1000.0ms", output)
                self.assertIn("MISS fixture:" if quality_gate else "FAIL fixture:", errors)
                self.assertNotIn("PASS fixture", output)

    def test_quality_gate_rejects_each_metric_at_or_below_target(self):
        quality = {"min_recall_at_k": 0.49, "min_mrr": 0.49}
        for key, value, metric in (
            ("min_recall_at_k", 0.5, "recall@k"),
            ("min_recall_at_k", 0.501, "recall@k"),
            ("min_mrr", 0.5, "MRR"),
            ("min_mrr", 0.501, "MRR"),
        ):
            with self.subTest(key=key):
                result, _, errors = self.run_mocked_case(
                    {"expected": ["a", "b"]}, [{"path": "a", "rank": 2}],
                    quality={**quality, key: value}, quality_gate=True,
                )
                self.assertEqual(1, result)
                self.assertIn(f"FAIL quality: {metric}", errors)
                self.assertEqual(1, errors.count("FAIL quality:"))

    def test_default_mode_keeps_inclusive_quality_thresholds(self):
        result, _, errors = self.run_mocked_case(
            {"expected": ["a"]}, [{"path": "a", "rank": 1}],
            quality={"min_recall_at_k": 1.0, "min_mrr": 1.0},
        )
        self.assertEqual(0, result)
        self.assertEqual("", errors)

    def test_quality_gate_preserves_hard_contract_failures(self):
        quality = {"min_recall_at_k": 0.49, "min_mrr": 0.49}
        for assertion, hits, returncode in (
            ({}, [], 2),
            ({"expected_error": "platform is required"}, [], 2),
            ({"expected_count": 0}, [{"path": "a", "rank": 1}], 0),
            ({"excluded": ["b"]}, [{"path": "a", "rank": 1}, {"path": "b", "rank": 2}], 0),
            ({"expected_fields": ["description"]}, [{"path": "a", "rank": 1}], 0),
            ({"filters": {"platform": ["950"]}}, [{"path": "a", "rank": 1, "platforms": ["a2"]}], 0),
            ({"filters": {"type": "apis"}}, [{"path": "a", "rank": 1, "profile": "runbooks"}], 0),
        ):
            with self.subTest(assertion=assertion, returncode=returncode):
                result, _, errors = self.run_mocked_case(
                    {"expected": ["a"], **assertion}, hits, returncode,
                    quality=quality, quality_gate=True,
                )
                self.assertEqual(1, result)
                self.assertIn("FAIL fixture:", errors)
                self.assertNotIn("MISS fixture:", errors)

    def test_quality_gate_rejects_missing_or_invalid_thresholds(self):
        quality = {"min_recall_at_k": 0.5, "min_mrr": 0.5}
        for key in quality:
            invalid = (None, True, 0, -1, "0.5", float("nan"), float("inf"))
            invalid += (1, 1.1)
            for value in invalid:
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, key):
                    self.run_mocked_case(
                        {"expected": ["a"]}, [],
                        quality={**quality, key: value}, quality_gate=True,
                    )
            with self.subTest(missing=key), self.assertRaisesRegex(ValueError, key):
                self.run_mocked_case(
                    {"expected": ["a"]}, [],
                    quality={k: v for k, v in quality.items() if k != key}, quality_gate=True,
                )

    def test_quality_gate_rejects_no_positive_evidence_cases(self):
        quality = {"min_recall_at_k": 0.5, "min_mrr": 0.5}
        for cases in ([], [{"id": "empty", "query": "query", "expected_count": 0}]):
            output, errors = io.StringIO(), io.StringIO()
            completed = subprocess.CompletedProcess([], 0, '{"count": 0, "hits": []}', "")
            with patch("evals.run_retrieval.subprocess.run", return_value=completed), \
                    redirect_stdout(output), redirect_stderr(errors):
                result = run_cases({"cases": cases, "quality": quality},
                                   {"repository": ROOT}, quality_gate=True)
            self.assertEqual(1, result)
            self.assertIn("no positive evidence cases", errors.getvalue())


class RetrievalIndexTests(unittest.TestCase):
    def test_execution_topic_filters_are_exact_and_conjunctive(self) -> None:
        topics = (
            "topic.implementation.resource_lifecycle",
            "topic.implementation.resource_query",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            runtime = root / "knowledge/runtime/apis"
            runtime.mkdir(parents=True)
            (runtime / "unrelated.md").write_text(SYNTHETIC_CARD, encoding="utf-8")
            for tag in topics:
                (runtime / f"{tag.rsplit('.', 1)[1]}.md").write_text(
                    SYNTHETIC_CARD.replace("topic.compilation", tag), encoding="utf-8",
                )
            built = run_index(root, "build")
            self.assertEqual(0, built.returncode, built.stderr)
            command = [sys.executable, str(QUERY), "--knowledge-root", str(root), "search",
                       "--query", "Synthetic API", "--domain", "runtime", "--type", "apis",
                       "--platform", "a2", "--match", "literal", "-k", "20"]

            def search(*filters):
                return subprocess.run([*command, *filters], capture_output=True, text=True)

            unfiltered = search()
            self.assertEqual(0, unfiltered.returncode, unfiltered.stderr)
            self.assertEqual(len(topics) + 1, json.loads(unfiltered.stdout)["count"])
            for tag in topics:
                with self.subTest(tag=tag):
                    result = search("--tag", tag, "--task", "lookup")
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(
                        [f"runtime/apis/{tag.rsplit('.', 1)[1]}"],
                        [hit["path"] for hit in json.loads(result.stdout)["results"]],
                    )
                    invalid = search("--tag", tag + ".unknown")
                    self.assertEqual(2, invalid.returncode)
                    self.assertIn("unknown tag", invalid.stderr)
            for filters in (
                ("--tag", "topic.implementation"),
                ("--tag", topics[0], "--tag", topics[1]),
                ("--tag", topics[0], "--task", "implementation"),
            ):
                with self.subTest(filters=filters):
                    result = search(*filters)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual([], json.loads(result.stdout)["results"])

    def test_kirin_api_filter_keeps_platform_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            for platform in ("kirin_x90", "kirin_9030"):
                (root / f"knowledge/ops/ascendc/apis/{platform}.md").write_text(
                    SYNTHETIC_CARD.replace("platforms: [a2]", f"platforms: [{platform}]")
                )
            built = run_index(root, "build")
            self.assertEqual(0, built.returncode, built.stderr)
            command = [sys.executable, str(QUERY), "--knowledge-root", str(root), "search",
                       "--query", "Synthetic API", "--technology", "ascendc", "--type", "apis"]
            for platform in ("kirin_x90", "kirin_9030", "a2"):
                result = subprocess.run([*command, "--platform", platform], capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                results = json.loads(result.stdout)["results"]
                self.assertEqual(1, len(results))
                self.assertEqual([platform], results[0]["platforms"])
            invalid = subprocess.run([*command, "--platform", "kirin_unknown"], capture_output=True, text=True)
            self.assertNotEqual(0, invalid.returncode)

    def test_quality_metrics_are_not_fabricated_without_positive_cases(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = run_cases(
                {
                    "cases": [],
                    "quality": {"min_recall_at_k": 1.0, "min_mrr": 1.0},
                },
                {},
            )
        self.assertEqual(result, 0)
        self.assertIn("recall@k=N/A MRR=N/A", output.getvalue())

    def test_index_build_verify_and_stale_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            build = run_index(root, "build", "--json")
            self.assertEqual(build.returncode, 0, build.stderr)
            metadata = json.loads(build.stdout)["index"]
            self.assertEqual(metadata["card_count"], 1)
            self.assertTrue(metadata["content_fingerprint"])
            verify = run_index(root, "verify", "--level", "full", "--json")
            self.assertEqual(verify.returncode, 0, verify.stderr)

            card = root / "knowledge/ops/ascendc/apis/synthetic_api.md"
            card.write_text(card.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            stale = subprocess.run(
                [
                    sys.executable,
                    str(QUERY),
                    "search",
                    "--knowledge-root",
                    str(root),
                    "--query",
                    "Synthetic API",
                    "--technology",
                    "ascendc",
                    "--platform",
                    "a2",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(stale.returncode, 2)
            self.assertIn("changed after index build", stale.stderr)

            rebuild = run_index(root, "build")
            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)
            registries = root / "governance/schemas/registries.yaml"
            registries.write_text(
                registries.read_text(encoding="utf-8") + "\n# test drift\n",
                encoding="utf-8",
            )
            governance_stale = subprocess.run(
                [
                    sys.executable,
                    str(QUERY),
                    "--knowledge-root",
                    str(root),
                    "search",
                    "--query",
                    "Synthetic API",
                    "--technology",
                    "ascendc",
                    "--platform",
                    "a2",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(governance_stale.returncode, 2)
            self.assertIn("governance changed", governance_stale.stderr)

    def test_full_verify_rejects_tampered_query_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            database = root / "artifacts/indexes/knowledge.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE documents SET title = ?, search_text = ?",
                    ("Forged index title", "forged index title"),
                )
                connection.commit()

            verified = run_index(root, "verify", "--level", "full")
            self.assertEqual(verified.returncode, 2)
            self.assertIn("document differs from governed card", verified.stderr)

            rebuild = run_index(root, "build")
            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE postings SET title_tf = title_tf + 1 "
                    "WHERE (term, doc_id) = (SELECT term, doc_id FROM postings LIMIT 1)"
                )
                connection.commit()
            postings_verified = run_index(root, "verify", "--level", "full")
            self.assertEqual(postings_verified.returncode, 2)
            self.assertIn("postings differ from governed card", postings_verified.stderr)

    def test_target_contract_is_compared_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            marker = root / "target-contract-executed"
            (root / "governance/contracts/knowledge.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
                encoding="utf-8",
            )
            build = run_index(root, "build")
            executed = marker.exists()
        self.assertEqual(build.returncode, 2)
        self.assertIn("does not match", build.stderr)
        self.assertFalse(executed)

    def test_query_contract_and_cli_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            command = [
                sys.executable,
                str(QUERY),
                "search",
                "--knowledge-root",
                str(root),
                "--query",
                "Synthetic API",
                "--technology",
                "ascendc",
                "--platform",
                "a2",
                "--k",
                "1",
            ]
            result = subprocess.run(command, check=False, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema_version"], "knowledge-search.v5")
            self.assertEqual(payload["results"], payload["hits"])
            self.assertEqual(payload["results"][0]["rank"], 1)
            self.assertGreater(payload["results"][0]["card_lines"], 0)
            self.assertTrue(payload["index"]["content_fingerprint"])
            self.assertNotIn("cann_versions", payload["request"])
            self.assertNotIn("cann_versions", payload["filters"])

            version_filter = subprocess.run(
                [*command, "--cann-version", "9.1.0"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(version_filter.returncode, 2)
            self.assertIn("unrecognized arguments: --cann-version", version_filter.stderr)

            missing_platform_command = command.copy()
            platform_index = missing_platform_command.index("--platform")
            del missing_platform_command[platform_index : platform_index + 2]
            missing_platform = subprocess.run(
                missing_platform_command, check=False, text=True, capture_output=True
            )
            self.assertEqual(missing_platform.returncode, 2)
            self.assertIn("platform is required", missing_platform.stderr)
            self.assertEqual(
                json.loads(missing_platform.stdout), json.loads(missing_platform.stderr)
            )

            parse_error_cases = (
                ([*command, "--platform"], "expected one argument"),
                ([*command, "--limit", "oops"], "invalid int value"),
                ([*command, "--status", "bogus"], "invalid choice"),
                ([*command, "--unknown"], "unrecognized arguments"),
            )
            for invalid_command, expected_message in parse_error_cases:
                with self.subTest(expected_message=expected_message):
                    parsed = subprocess.run(
                        invalid_command, check=False, text=True, capture_output=True
                    )
                    self.assertEqual(parsed.returncode, 2)
                    stdout_payload = json.loads(parsed.stdout)
                    stderr_payload = json.loads(parsed.stderr)
                    self.assertEqual(stdout_payload, stderr_payload)
                    self.assertEqual(
                        "ValueError", stdout_payload["error"]["type"]
                    )
                    self.assertIn(expected_message, stdout_payload["error"]["message"])

            root_help = subprocess.run(
                [sys.executable, str(QUERY), "--help"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(root_help.returncode, 0)
            self.assertIn("usage:", root_help.stdout)
            self.assertEqual("", root_help.stderr)
            search_help = subprocess.run(
                [sys.executable, str(QUERY), "search", "--help"],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(search_help.returncode, 0)
            self.assertIn("usage:", search_help.stdout)
            self.assertEqual("", search_help.stderr)

    def test_search_ignores_platform_and_query_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            for name, platforms in (
                ("a2_only", "a2"), ("a3_only", "a3"),
                ("both", "a2, a3"), ("agnostic", "agnostic"),
            ):
                card = SYNTHETIC_CARD.replace(
                    "Synthetic API contract", f"DataCopyPad {name}"
                ).replace("platforms: [a2]", f"platforms: [{platforms}]")
                card += "\nCall DataCopyPad with copy pad and get_swi_glu.\n"
                (api_root / f"{name}.md").write_text(card, encoding="utf-8")

            for tokenizer in ("v3", "subword"):
                built = run_index(root, "build", "--tokenizer", tokenizer)
                self.assertEqual(built.returncode, 0, built.stderr)

                def search(query, platforms, match):
                    command = [
                        sys.executable, str(QUERY), "--knowledge-root", str(root),
                        "search", "--query", query, "--technology", "ascendc",
                        "--match", match,
                    ]
                    for platform in platforms:
                        command.extend(["--platform", platform])
                    completed = subprocess.run(
                        command, check=False, text=True, capture_output=True,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    return json.loads(completed.stdout)

                for match in ("text", "literal"):
                    for query in ("DataCopyPad", "Copy Pad", "Get_Swi_Glu"):
                        expected = search(query.lower(), ["a2"], match)
                        self.assertEqual(3, expected["count"])
                        for variant in (query, query.upper(), query.swapcase()):
                            with self.subTest(tokenizer=tokenizer, match=match, query=variant):
                                actual = search(variant, ["a2"], match)
                                self.assertEqual(expected["results"], actual["results"])
                                self.assertEqual(variant, actual["query"])
                                self.assertEqual(variant, actual["request"]["query"])

                    for platforms, names in (
                        (["A2"], {"a2_only", "both", "agnostic"}),
                        (["A3"], {"a3_only", "both", "agnostic"}),
                        (["A2", "a3"], {"both", "agnostic"}),
                    ):
                        with self.subTest(tokenizer=tokenizer, match=match, platforms=platforms):
                            normalized = [value.lower() for value in platforms]
                            expected = search("DataCopyPad", normalized, match)
                            actual = search("DataCopyPad", platforms, match)
                            self.assertEqual(expected["results"], actual["results"])
                            self.assertEqual(
                                names, {item["path"].rsplit("/", 1)[-1] for item in actual["results"]}
                            )
                            self.assertEqual(expected["request"], actual["request"])
                            self.assertEqual(expected["request_sha256"], actual["request_sha256"])

                invalid = subprocess.run(
                    [sys.executable, str(QUERY), "--knowledge-root", str(root),
                     "search", "--query", "DataCopyPad", "--platform", "A2_TYPO"],
                    check=False, text=True, capture_output=True,
                )
                self.assertEqual(2, invalid.returncode)
                self.assertIn("unknown platforms", invalid.stderr)
                self.assertEqual(json.loads(invalid.stdout), json.loads(invalid.stderr))

    def test_case_insensitive_subword_search_keeps_split_only_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            for name, title, body, platforms in (
                ("split_title", "Data Copy Pad alignment", "Aligned transfers.", "a2"),
                ("split_body", "Transfer guide", "Use data copy pad for aligned transfers.", "a2"),
                ("other_platform", "Data Copy Pad on A3", "Aligned transfers.", "a3"),
            ):
                card = SYNTHETIC_CARD.replace("Synthetic API contract", title).replace(
                    "platforms: [a2]", f"platforms: [{platforms}]"
                ) + "\n" + body + "\n"
                self.assertNotIn("datacopypad", card.lower())
                (api_root / f"{name}.md").write_text(card, encoding="utf-8")
            built = run_index(root, "build", "--tokenizer", "subword")
            self.assertEqual(built.returncode, 0, built.stderr)
            database = root / "artifacts/indexes/knowledge.sqlite3"
            before = hashlib.sha256(database.read_bytes()).hexdigest()
            expected = None
            for query in ("DataCopyPad", "datacopypad", "DATACOPYPAD", "dAtAcOpYpAd"):
                for match in ("text", "literal"):
                    with self.subTest(query=query, match=match):
                        completed = subprocess.run(
                            [sys.executable, str(QUERY), "--knowledge-root", str(root),
                             "search", "--query", query, "--technology", "ascendc",
                             "--platform", "A2", "--match", match],
                            check=False, text=True, capture_output=True,
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                        payload = json.loads(completed.stdout)
                        results = payload["results"]
                        if match == "literal":
                            self.assertEqual([], results)
                            continue
                        self.assertEqual(
                            {"split_title", "split_body"},
                            {item["path"].rsplit("/", 1)[-1] for item in results},
                        )
                        self.assertEqual("Data Copy Pad alignment", results[0]["title"])
                        self.assertTrue(all(item["score"] > 0 for item in results))
                        if expected is None:
                            expected = results
                        else:
                            self.assertEqual(expected, results)
            self.assertEqual(before, hashlib.sha256(database.read_bytes()).hexdigest())

    def test_subword_split_selection_uses_evidence_before_longer_words(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            for name, title in (
                ("synthetic_api", "Data Copy Pad alignment"),
                ("datacopy", "datacopy notes"),
            ):
                card = SYNTHETIC_CARD.replace("Synthetic API contract", title)
                self.assertNotIn("datacopypad", card.lower())
                (api_root / f"{name}.md").write_text(card, encoding="utf-8")
            for second_distractor in (False, True):
                if second_distractor:
                    card = SYNTHETIC_CARD.replace("Synthetic API contract", "copypad notes")
                    (api_root / "copypad.md").write_text(card, encoding="utf-8")
                built = run_index(root, "build", "--tokenizer", "subword")
                self.assertEqual(built.returncode, 0, built.stderr)
                expected = None
                for query in ("DataCopyPad", "datacopypad", "DATACOPYPAD"):
                    with self.subTest(second_distractor=second_distractor, query=query):
                        completed = subprocess.run(
                            [sys.executable, str(QUERY), "--knowledge-root", str(root),
                             "search", "--query", query, "--technology", "ascendc",
                             "--platform", "A2", "--match", "text"],
                            check=False, text=True, capture_output=True,
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                        results = json.loads(completed.stdout)["results"]
                        self.assertEqual(["Data Copy Pad alignment"], [item["title"] for item in results])
                        self.assertGreater(results[0]["score"], 0)
                        if expected is None:
                            expected = results
                        else:
                            self.assertEqual(expected, results)

    def test_subword_expansion_requires_name_or_contiguous_phrase_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            for name, title in (
                ("synthetic_api", "Black tensor layout"), ("bird", "Bird scheduling"),
            ):
                card = SYNTHETIC_CARD.replace("Synthetic API contract", title)
                self.assertNotIn("blackbird", card.lower())
                self.assertNotIn("black bird", card.lower())
                (api_root / f"{name}.md").write_text(card, encoding="utf-8")

            for evidence in (None, "Use BlackBird for named lookup.", "Use black bird for named lookup."):
                if evidence is not None:
                    card = SYNTHETIC_CARD.replace("Synthetic API contract", "Named lookup")
                    card += "\n" + evidence + "\n"
                    (api_root / "actual_name.md").write_text(card, encoding="utf-8")
                built = run_index(root, "build", "--tokenizer", "subword")
                self.assertEqual(built.returncode, 0, built.stderr)
                expected = None
                for query in ("blackbird", "Blackbird", "BLACKBIRD", "BlackBird"):
                    for match in ("text", "literal"):
                        with self.subTest(evidence=evidence, query=query, match=match):
                            completed = subprocess.run(
                                [sys.executable, str(QUERY), "--knowledge-root", str(root),
                                 "search", "--query", query, "--technology", "ascendc",
                                 "--platform", "A2", "--match", match],
                                check=False, text=True, capture_output=True,
                            )
                            self.assertEqual(completed.returncode, 0, completed.stderr)
                            results = json.loads(completed.stdout)["results"]
                            if match == "literal":
                                names = {"actual_name"} if evidence and "BlackBird" in evidence else set()
                            else:
                                names = {"synthetic_api", "bird", "actual_name"} if evidence else set()
                            self.assertEqual(names, {
                                item["path"].rsplit("/", 1)[-1] for item in results
                            })
                            if match == "text":
                                if expected is None:
                                    expected = results
                                else:
                                    self.assertEqual(expected, results)

    def test_subword_name_recovery_preserves_accessors_and_complete_words(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            for name, title, body in (
                ("arch", "GetCurNpuArch", "Architecture lookup."),
                ("arch_split", "Cur Npu Arch details", "Architecture lookup."),
                ("body_getter", "Version lookup", "Call GetSocVersion."),
                ("soc_split", "Soc Version details", "Version lookup."),
                ("data_copy", "DataCopy", "Copy lookup."),
                ("split_copy_pad", "Data Copy Pad alignment", "Aligned transfers."),
                ("getting", "Getting started", "Introduction."),
                ("get", "Get ready", "Introduction."),
                ("ting", "Ting notes", "Introduction."),
                ("partial", "Alpha Beta", "Introduction."),
            ):
                card = SYNTHETIC_CARD.replace("Synthetic API contract", title) + "\n" + body + "\n"
                (api_root / f"{name}.md").write_text(card, encoding="utf-8")
            built = run_index(root, "build", "--tokenizer", "subword")
            self.assertEqual(built.returncode, 0, built.stderr)
            for query, expected_paths in (
                ("GetCurNpuArch", {"arch", "arch_split"}),
                ("GetSocVersion", {"body_getter", "soc_split"}),
                ("DataCopyPad", {"data_copy", "split_copy_pad"}),
                ("Getting", {"getting"}),
                ("AlphaMissingBeta", set()),
            ):
                expected = None
                for variant in (query, query.lower(), query.upper()):
                    with self.subTest(query=variant):
                        completed = subprocess.run(
                            [sys.executable, str(QUERY), "--knowledge-root", str(root),
                             "search", "--query", variant, "--technology", "ascendc",
                             "--platform", "a2", "--match", "text"],
                            check=False, text=True, capture_output=True,
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                        results = json.loads(completed.stdout)["results"]
                        self.assertEqual(
                            expected_paths,
                            {item["path"].rsplit("/", 1)[-1] for item in results},
                        )
                        if expected is None:
                            expected = results
                        else:
                            self.assertEqual(expected, results)

    def test_search_uses_project_default_platform_and_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            project = work / "project"
            make_root(root)
            project.mkdir()
            (project / ".cannbot").mkdir()
            (project / ".cannbot/knowledge.env").write_text(
                f'export CANNBOT_KNOWLEDGE_ROOT="{root}"\n'
                "export CANNBOT_KNOWLEDGE_PLATFORM=A2\n",
                encoding="utf-8",
            )
            built = run_index(root, "build")
            self.assertEqual(built.returncode, 0, built.stderr)
            command = [
                sys.executable,
                str(QUERY),
                "search",
                "--query",
                "Synthetic API",
                "--technology",
                "ascendc",
            ]
            environment = dict(os.environ)
            environment.pop("CANNBOT_KNOWLEDGE_PLATFORM", None)
            defaulted = subprocess.run(
                command,
                cwd=project,
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(defaulted.returncode, 0, defaulted.stderr)
            default_payload = json.loads(defaulted.stdout)
            self.assertEqual(["a2"], default_payload["request"]["platforms"])
            self.assertEqual(1, default_payload["count"])

            explicit = subprocess.run(
                [*command, "--platform", "A3"],
                cwd=project,
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(explicit.returncode, 0, explicit.stderr)
            explicit_payload = json.loads(explicit.stdout)
            self.assertEqual(["a3"], explicit_payload["request"]["platforms"])
            self.assertEqual(0, explicit_payload["count"])

            environment["CANNBOT_KNOWLEDGE_PLATFORM"] = "A3"
            from_environment = subprocess.run(
                command, cwd=project, env=environment,
                check=False, text=True, capture_output=True,
            )
            self.assertEqual(from_environment.returncode, 0, from_environment.stderr)
            environment_payload = json.loads(from_environment.stdout)
            self.assertEqual(["a3"], environment_payload["request"]["platforms"])
            self.assertEqual(0, environment_payload["count"])

    def test_literal_search_prioritizes_title_and_includes_ordinary_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            target = SYNTHETIC_CARD.replace(
                "Synthetic API contract", "GetCurNpuArch"
            ).replace(
                "This fixture verifies indexed API lookup and audit behavior without depending on\n"
                "repository knowledge cards.",
                "Returns the current NPU architecture.",
            )
            (api_root / "get_cur_npu_arch.md").write_text(target, encoding="utf-8")
            usage = SYNTHETIC_CARD.replace(
                "Synthetic API contract", "Platform API usage"
            ).replace(
                "This fixture verifies indexed API lookup and audit behavior without depending on\n"
                "repository knowledge cards.",
                "Call GetCurNpuArch when selecting an architecture-specific implementation.",
            )
            (api_root / "platform_usage.md").write_text(usage, encoding="utf-8")
            related = SYNTHETIC_CARD.replace(
                "Synthetic API contract", "Related navigation only"
            ).replace(
                "This fixture verifies indexed API lookup and audit behavior without depending on\n"
                "repository knowledge cards.",
                "参见 [GetCurNpuArch](get_cur_npu_arch.md)。",
            )
            (api_root / "related_navigation.md").write_text(related, encoding="utf-8")

            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            query = subprocess.run(
                [
                    sys.executable,
                    str(QUERY),
                    "--knowledge-root",
                    str(root),
                    "search",
                    "--query",
                    "GetCurNpuArch",
                    "--technology",
                    "ascendc",
                    "--platform",
                    "a2",
                    "--match",
                    "literal",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(query.returncode, 0, query.stderr)
            results = json.loads(query.stdout)["results"]
            self.assertEqual("GetCurNpuArch", results[0]["title"])
            self.assertIn("Platform API usage", [item["title"] for item in results[1:]])
            self.assertIn("Related navigation only", [item["title"] for item in results[1:]])

            # A literal query is one contiguous phrase, not an AND of keywords.
            for match, expected_count in (("literal", 0), ("text", 3)):
                with self.subTest(match=match):
                    combined = subprocess.run(
                        [
                            sys.executable, str(QUERY), "--knowledge-root", str(root),
                            "search", "--query", "GetCurNpuArch architecture",
                            "--technology", "ascendc", "--type", "apis",
                            "--platform", "a2", "--match", match,
                        ],
                        check=False, text=True, capture_output=True,
                    )
                    self.assertEqual(combined.returncode, 0, combined.stderr)
                    self.assertEqual(expected_count, json.loads(combined.stdout)["count"])

    def test_literal_unicode_case_normalization_keeps_field_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            fixtures = {
                "greek_exact_title.md": (
                    "Θ Exact title",
                    "Generic API description.",
                ),
                "greek_description.md": (
                    "Other API result",
                    "θ Exact title is described here.",
                ),
                "ascii_exact_title.md": (
                    "GetCurNpuArch",
                    "Generic API description.",
                ),
                "ascii_description.md": (
                    "Other ASCII result",
                    "GetCurNpuArch is described here.",
                ),
            }
            for filename, (title, description) in fixtures.items():
                card = SYNTHETIC_CARD.replace("Synthetic API contract", title).replace(
                    "Deterministic API fixture for retrieval tests.", description
                )
                (api_root / filename).write_text(card, encoding="utf-8")

            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)

            for search_text, expected in (
                ("Θ Exact title", "greek_exact_title"),
                ("GetCurNpuArch", "ascii_exact_title"),
            ):
                with self.subTest(query=search_text):
                    query = subprocess.run(
                        [
                            sys.executable,
                            str(QUERY),
                            "--knowledge-root",
                            str(root),
                            "search",
                            "--query",
                            search_text,
                            "--technology",
                            "ascendc",
                            "--platform",
                            "a2",
                            "--match",
                            "literal",
                            "-k",
                            "5",
                        ],
                        check=False,
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(query.returncode, 0, query.stderr)
                    results = json.loads(query.stdout)["results"]
                    self.assertEqual(expected, Path(results[0]["path"]).name)

    def test_platform_workflow_filters_and_unlocated_fallback_are_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            fixtures = {
                "a3": ("stable", "[a3]"),
                "common": ("stable", "[a2, a3]"),
                "neutral": ("stable", "[agnostic]"),
                "unlocated": ("draft", "[]"),
                "located_draft": ("draft", "[a2]"),
                "950": ("stable", '["950"]'),
                "310p": ("stable", "[310p]"),
                "310b": ("stable", "[310b]"),
                "910": ("stable", '["910"]'),
                "kirin_x90": ("stable", "[kirin_x90]"),
                "kirin_9030": ("stable", "[kirin_9030]"),
            }
            for name, (status, platforms) in fixtures.items():
                (api_root / f"fixture_{name}.md").write_text(
                    SYNTHETIC_CARD.replace("status: stable", f"status: {status}")
                    .replace("platforms: [a2]", f"platforms: {platforms}"),
                    encoding="utf-8",
                )
            built = run_index(root, "build")
            self.assertEqual(built.returncode, 0, built.stderr)

            def snapshot() -> dict[str, str]:
                return {
                    path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in root.rglob("*") if path.is_file()
                }

            before = snapshot()
            cases = [
                (["--platform", "a2"], {"synthetic_api", "fixture_common", "fixture_neutral"}),
                (["--platform", "a3"], {"fixture_a3", "fixture_common", "fixture_neutral"}),
                (["--platform", "a2", "--platform", "a3"], {"fixture_common", "fixture_neutral"}),
                (["--platform", "agnostic"], {"fixture_neutral"}),
                (["--include-unlocated", "--status", "draft"], {"fixture_unlocated"}),
                (["--platform", "a2", "--status", "draft"], {"fixture_located_draft"}),
                (["--platform", "a2", "-k", "1"], None),
            ]
            cases.extend(
                (["--platform", platform], {f"fixture_{platform}", "fixture_neutral"})
                for platform in ("950", "310p", "310b", "910", "kirin_x90", "kirin_9030")
            )
            command = [
                sys.executable, str(QUERY), "--knowledge-root", str(root), "search",
                "--query", "Synthetic API", "--domain", "ops", "--technology", "ascendc",
                "--type", "apis", "--match", "literal", "-k", "20",
            ]
            for arguments, expected in cases:
                with self.subTest(arguments=arguments):
                    result = subprocess.run(
                        [*command, *arguments], check=False, text=True, capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    if expected is None:
                        self.assertEqual(1, payload["count"])
                    else:
                        self.assertEqual(expected, {Path(hit["path"]).name for hit in payload["results"]})
                        self.assertEqual(len(expected), payload["count"])
                    concise = subprocess.run(
                        [*command, *arguments, "--text"], check=False, text=True, capture_output=True,
                    )
                    self.assertEqual(0, concise.returncode, concise.stderr)
                    self.assertEqual(
                        [hit["path"] for hit in payload["results"]],
                        [line.removeprefix("  path: ") for line in concise.stdout.splitlines()
                         if line.startswith("  path: ")],
                    )
                    for hit in payload["results"]:
                        self.assertIn(hit["title"], concise.stdout)
                        self.assertIn(hit["description"], concise.stdout)
                        self.assertIn(hit["local_path"], concise.stdout)
                    citations = [
                        line.split("](<", 1)[1].removesuffix(">)")
                        for line in concise.stdout.splitlines() if line.startswith("[")
                    ]
                    self.assertEqual(
                        [hit["local_path"] for hit in payload["results"]],
                        [unquote(target) for target in citations],
                    )
                    self.assertNotIn('"sources"', concise.stdout)

            empty = subprocess.run(
                [*command, "--platform", "a2", "--query", "absent-symbol", "--text"],
                check=False, text=True, capture_output=True,
            )
            self.assertEqual(0, empty.returncode, empty.stderr)
            self.assertEqual("no matches\n", empty.stdout)

            invalid = [
                [],
                ["--platform", "a5"],
                ["--platform", "310_unknown"],
                ["--platform", "DAV_2201"],
                ["--platform", "ASCEND910B"],
                ["--platform", "a2", "--include-unlocated", "--status", "draft"],
                ["--include-unlocated", "--status", "stable"],
            ]
            for arguments in invalid:
                for output_mode in ("--json", "--text"):
                    with self.subTest(invalid=arguments, output=output_mode):
                        result = subprocess.run(
                            [*command, *arguments, output_mode], check=False, text=True, capture_output=True,
                        )
                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertEqual(
                            json.loads(result.stdout), json.loads(result.stderr)
                        )
            self.assertEqual(before, snapshot(), "Search must not mutate cards, governance or index")

    def test_text_citation_escapes_title_and_round_trips_special_root_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "space # > % ?mode=rw 中文"
            make_root(root)
            card = root / "knowledge/ops/ascendc/apis/synthetic_api.md"
            title = r"Synthetic API [name] <T> \suffix"
            card.write_text(
                SYNTHETIC_CARD.replace("title: Synthetic API contract", "title: " + json.dumps(title)),
                encoding="utf-8",
            )
            built = run_index(root, "build")
            self.assertEqual(0, built.returncode, built.stderr)

            def snapshot():
                return {
                    path.relative_to(temporary).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
                    for path in Path(temporary).rglob("*") if path.is_file()
                }

            before = snapshot()
            result = subprocess.run(
                [sys.executable, str(QUERY), "--knowledge-root", str(root), "search",
                 "--query", "Synthetic API", "--platform", "a2", "--match", "literal", "--text"],
                check=False, text=True, capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            citation = result.stdout.splitlines()[0]
            label, target = citation.split("](<", 1)
            self.assertEqual(r"[1] [Synthetic API \[name\] &lt;T&gt; \\suffix", label)
            self.assertEqual(card, Path(unquote(target.removesuffix(">)"))))
            self.assertNotIn("#", target)
            self.assertNotIn("file://", target)
            self.assertEqual(before, snapshot(), "Reading special paths must not create a different database")


class RetrievalAuditTests(unittest.TestCase):
    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def create_search_receipt(
        self,
        root: Path,
        path: Path,
        *,
        platform: str,
        query_text: str = "Synthetic API",
    ) -> dict[str, object]:
        query = subprocess.run(
            [
                sys.executable,
                str(QUERY),
                "--knowledge-root",
                str(root),
                "search",
                "--query",
                query_text,
                "--match",
                "literal",
                "--decision",
                "api-contract",
                "--technology",
                "ascendc",
                "--platform",
                platform,
                "--receipt",
                str(path),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(query.returncode, 0, query.stderr)
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def write_state(
        path: Path,
        receipt_path: Path,
        receipt: dict[str, object],
        *,
        platform: str,
    ) -> None:
        result = receipt["result"]
        assert isinstance(result, dict)
        hits = result["results"]
        assert isinstance(hits, list) and hits and isinstance(hits[0], dict)
        hit = hits[0]
        path.write_text(
            json.dumps(
                {
                    "schema_version": "cannbot-retrieval-state.v1",
                    "target": {"entity": "Synthetic API", "platforms": [platform]},
                    "decisions": [
                        {
                            "id": "api-contract",
                            "question": "Which API contract applies?",
                            "status": "covered",
                            "receipts": [str(receipt_path)],
                            "evidence": [
                                {
                                    "path": hit["path"],
                                    "card_sha256": hit["card_sha256"],
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def validate_state(root: Path, state: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(STATE),
                str(state),
                "--knowledge-root",
                str(root),
                "--require-ready",
            ],
            check=False,
            text=True,
            capture_output=True,
        )

    def assert_existing_receipts_rejected(self, command: list[str], work: Path) -> None:
        work.mkdir()
        protected = work / "protected.json"
        protected.write_bytes(b"existing receipt\n")
        redirected = work / "uncreated" / "redirected.json"
        dangling = work / "dangling.json"
        dangling.symlink_to(redirected)
        linked = work / "linked.json"
        linked.symlink_to(protected)
        directory = work / "directory.json"
        directory.mkdir()
        for target in (protected, dangling, linked, directory):
            with self.subTest(command=Path(command[1]).name, target=target.name):
                result = subprocess.run(
                    [*command, "--receipt", str(target)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn("refusing to overwrite receipt", result.stdout + result.stderr)
                self.assertEqual(b"existing receipt\n", protected.read_bytes())
                self.assertTrue(dangling.is_symlink())
                self.assertEqual(redirected, dangling.readlink())
                self.assertFalse(redirected.parent.exists())
                self.assertTrue(linked.is_symlink())
                self.assertTrue(directory.is_dir())
                self.assertEqual([], list(work.glob("*.tmp")))

    def test_ready_state_and_outcome_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            make_root(root)
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            search_receipt = work / "search.json"
            query = subprocess.run(
                [
                    sys.executable,
                    str(QUERY),
                    "--knowledge-root",
                    str(root),
                    "search",
                    "--query",
                    "Synthetic API",
                    "--decision",
                    "api-contract",
                    "--technology",
                    "ascendc",
                    "--platform",
                    "a2",
                    "--receipt",
                    str(search_receipt),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(query.returncode, 0, query.stderr)
            hit = json.loads(search_receipt.read_text(encoding="utf-8"))["result"]["results"][0]
            state_path = work / "retrieval_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": "cannbot-retrieval-state.v1",
                        "target": {"entity": "Synthetic API", "platforms": ["a2"]},
                        "decisions": [
                            {
                                "id": "api-contract",
                                "question": "Which API contract applies?",
                                "status": "covered",
                                "receipts": [str(search_receipt)],
                                "evidence": [
                                    {
                                        "path": hit["path"],
                                        "card_sha256": hit["card_sha256"],
                                    }
                                ],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            ready = work / "retrieval_ready.json"
            validate_state = subprocess.run(
                [
                    sys.executable,
                    str(STATE),
                    str(state_path),
                    "--knowledge-root",
                    str(root),
                    "--require-ready",
                    "--receipt",
                    str(ready),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(validate_state.returncode, 0, validate_state.stderr)
            self.assertTrue(json.loads(validate_state.stdout)["ready"])
            ready_payload = json.loads(ready.read_text(encoding="utf-8"))
            self.assertEqual(
                ready_payload["receipt_sha256s"][str(search_receipt)],
                self.sha256(search_receipt),
            )

            artifact = work / "test-result.txt"
            artifact.write_text("verified\n", encoding="utf-8")
            manifest = work / "retrieval_outcome.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "cannbot-retrieval-outcome.v1",
                        "state": str(state_path),
                        "state_sha256": self.sha256(state_path),
                        "ready_receipt": str(ready),
                        "ready_receipt_sha256": self.sha256(ready),
                        "events": [
                            {
                                "decision": "api-contract",
                                "outcome": "verified",
                                "summary": "Target-platform check passed.",
                                "observed": ["test passed"],
                                "artifacts": [
                                    {
                                        "path": str(artifact),
                                        "sha256": self.sha256(artifact),
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            outcome_receipt = work / "retrieval_outcome_receipt.json"
            validate_outcome = subprocess.run(
                [
                    sys.executable,
                    str(OUTCOME),
                    str(manifest),
                    "--require-complete",
                    "--receipt",
                    str(outcome_receipt),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(validate_outcome.returncode, 0, validate_outcome.stderr)
            self.assertTrue(json.loads(validate_outcome.stdout)["complete"])
            self.assertTrue(outcome_receipt.is_file())

            for name, command in (
                ("search", [sys.executable, str(QUERY), "--knowledge-root", str(root),
                            "search", "--query", "Synthetic API", "--technology", "ascendc",
                            "--platform", "a2"]),
                ("state", [sys.executable, str(STATE), str(state_path), "--knowledge-root",
                           str(root), "--require-ready"]),
                ("outcome", [sys.executable, str(OUTCOME), str(manifest), "--require-complete"]),
            ):
                self.assert_existing_receipts_rejected(command, work / f"reject_{name}")

            search_receipt.write_text(
                search_receipt.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            stale_chain = subprocess.run(
                [
                    sys.executable,
                    str(OUTCOME),
                    str(manifest),
                    "--require-complete",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(stale_chain.returncode, 1)
            self.assertIn("ready.receipt_sha256", stale_chain.stdout)

    def test_tampered_search_request_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            make_root(root)
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            search_receipt = work / "search.json"
            query = subprocess.run(
                [
                    sys.executable,
                    str(QUERY),
                    "--knowledge-root",
                    str(root),
                    "search",
                    "--query",
                    "Synthetic API",
                    "--decision",
                    "api-contract",
                    "--technology",
                    "ascendc",
                    "--platform",
                    "a2",
                    "--receipt",
                    str(search_receipt),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(query.returncode, 0, query.stderr)
            receipt_payload = json.loads(search_receipt.read_text(encoding="utf-8"))
            hit = receipt_payload["result"]["results"][0]
            receipt_payload["request"]["decision"] = "tampered-decision"
            search_receipt.write_text(json.dumps(receipt_payload), encoding="utf-8")

            state_path = work / "retrieval_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": "cannbot-retrieval-state.v1",
                        "target": {"entity": "Synthetic API", "platforms": ["a2"]},
                        "decisions": [
                            {
                                "id": "api-contract",
                                "question": "Which API contract applies?",
                                "status": "covered",
                                "receipts": [str(search_receipt)],
                                "evidence": [
                                    {
                                        "path": hit["path"],
                                        "card_sha256": hit["card_sha256"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            checked = subprocess.run(
                [
                    sys.executable,
                    str(STATE),
                    str(state_path),
                    "--knowledge-root",
                    str(root),
                    "--require-ready",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(checked.returncode, 1)
            error_codes = {item["code"] for item in json.loads(checked.stdout)["errors"]}
            self.assertIn("receipt.request_hash", error_codes)
            self.assertIn("receipt.result_request", error_codes)

    def test_state_rejects_receipt_for_another_platform(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            make_root(root)
            card = root / "knowledge/ops/ascendc/apis/synthetic_api.md"
            card.write_text(
                card.read_text(encoding="utf-8").replace("platforms: [a2]", "platforms: [a3]"),
                encoding="utf-8",
            )
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            receipt_path = work / "search.json"
            receipt = self.create_search_receipt(root, receipt_path, platform="a3")
            state_path = work / "state.json"
            self.write_state(state_path, receipt_path, receipt, platform="a2")

            checked = self.validate_state(root, state_path)
            payload = json.loads(checked.stdout)
        self.assertEqual(checked.returncode, 1)
        self.assertFalse(payload["ready"])
        self.assertIn("receipt.platform", {item["code"] for item in payload["errors"]})

    def test_linked_card_needs_a_bound_matching_receipt_before_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            make_root(root)
            api_root = root / "knowledge/ops/ascendc/apis"
            neighbor = api_root / "neighbor.md"
            neighbor.write_text(
                SYNTHETIC_CARD.replace("Synthetic API contract", "NeighborContract"),
                encoding="utf-8",
            )
            original = api_root / "synthetic_api.md"
            original.write_text(
                original.read_text(encoding="utf-8")
                + "\n\n- [NeighborContract](neighbor.md)\n",
                encoding="utf-8",
            )
            built = run_index(root, "build")
            self.assertEqual(built.returncode, 0, built.stderr)
            first_path = work / "first.json"
            first = self.create_search_receipt(root, first_path, platform="a2")
            self.assertEqual(1, first["result"]["count"])
            first_hash = self.sha256(first_path)
            second_path = work / "neighbor.json"
            second = self.create_search_receipt(
                root, second_path, platform="a2", query_text="NeighborContract",
            )
            self.assertEqual(2, second["result"]["count"])
            neighbor_hit = second["result"]["results"][0]
            state = work / "state.json"
            self.write_state(state, first_path, first, platform="a2")
            payload = json.loads(state.read_text(encoding="utf-8"))
            payload["decisions"][0]["evidence"].append({
                "path": neighbor_hit["path"],
                "card_sha256": neighbor_hit["card_sha256"],
            })
            state.write_text(json.dumps(payload), encoding="utf-8")
            rejected = self.validate_state(root, state)
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self.assertEqual({"evidence.receipt"}, {
                error["code"] for error in json.loads(rejected.stdout)["errors"]
            })

            payload["decisions"][0]["receipts"].append(str(second_path))
            state.write_text(json.dumps(payload), encoding="utf-8")
            accepted = self.validate_state(root, state)
            self.assertEqual(accepted.returncode, 0, accepted.stderr + accepted.stdout)
            self.assertTrue(json.loads(accepted.stdout)["ready"])
            self.assertEqual(first_hash, self.sha256(first_path))

    def test_state_rejects_wrong_current_index_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            make_root(root)
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            receipt_path = work / "search.json"
            receipt = self.create_search_receipt(root, receipt_path, platform="a2")
            result = receipt["result"]
            assert isinstance(result, dict)
            receipt_index = receipt["index"]
            result_index = result["index"]
            assert isinstance(receipt_index, dict) and isinstance(result_index, dict)
            receipt_index["index_version"] = 999999
            result_index["index_version"] = 999999
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            state_path = work / "state.json"
            self.write_state(state_path, receipt_path, receipt, platform="a2")

            checked = self.validate_state(root, state_path)
            payload = json.loads(checked.stdout)
        self.assertEqual(checked.returncode, 1)
        self.assertFalse(payload["ready"])
        self.assertIn("receipt.stale", {item["code"] for item in payload["errors"]})

    def test_state_replays_and_rejects_forged_hits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = work / "repository"
            make_root(root)
            build = run_index(root, "build")
            self.assertEqual(build.returncode, 0, build.stderr)
            receipt_path = work / "search.json"
            receipt = self.create_search_receipt(root, receipt_path, platform="a2")
            result = receipt["result"]
            assert isinstance(result, dict)
            results = result["results"]
            assert isinstance(results, list) and results and isinstance(results[0], dict)
            results[0]["title"] = "Forged receipt title"
            result["hits"] = results
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            state_path = work / "state.json"
            self.write_state(state_path, receipt_path, receipt, platform="a2")

            checked = self.validate_state(root, state_path)
            payload = json.loads(checked.stdout)
        self.assertEqual(checked.returncode, 1)
        self.assertFalse(payload["ready"])
        self.assertIn("receipt.replay", {item["code"] for item in payload["errors"]})


class RuntimeQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.root = self.work / "repository"
        make_root(self.root)
        api_root = self.root / "knowledge/runtime/apis"
        api_root.mkdir(parents=True)
        fixtures = (
            ("a2_only", "[a2]", "stable"), ("a3_only", "[a3]", "stable"),
            ("common", "[a2, a3]", "stable"), ("neutral", "[agnostic]", "stable"),
            ("located_draft", "[a2]", "draft"), ("unlocated", "[]", "draft"),
        )
        for name, platforms, status in fixtures:
            (api_root / f"{name}.md").write_text(
                SYNTHETIC_CARD.replace("platforms: [a2]", f"platforms: {platforms}")
                .replace("status: stable", f"status: {status}"), encoding="utf-8",
            )
        built = run_index(self.root, "build")
        self.assertEqual(0, built.returncode, built.stderr)
        self.environment = dict(os.environ)
        self.environment.pop("CANNBOT_KNOWLEDGE_PLATFORM", None)
        self.environment.pop("CANNBOT_KNOWLEDGE_ROOT", None)

    def query(
        self, *arguments: str, query_text: str = "Synthetic API",
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(QUERY), "--knowledge-root", str(self.root), "search",
             "--query", query_text, "--match", "literal", "-k", "20", *arguments],
            cwd=self.root, env=self.environment, check=False, text=True, capture_output=True,
        )

    def test_runtime_exact_api_is_recalled_beyond_platform_prefix_hits(self) -> None:
        api = "acltdtCreateChannel"
        prefix_api = "acltdtCreateChannelWithCapacity"
        api_root = self.root / "knowledge/runtime/apis"
        # Synthetic cards pin the retrieval case, not Agent definition verification.
        for status in ("stable", "draft"):
            with self.subTest(status=status):
                for name, title, platforms in (
                    ("exact_channel", api, '["910"]'),
                    ("prefix_channel", prefix_api, "[a2]"),
                ):
                    (api_root / f"{name}.md").write_text(
                        SYNTHETIC_CARD.replace("Synthetic API contract", title)
                        .replace("platforms: [a2]", f"platforms: {platforms}")
                        .replace("status: stable", f"status: {status}"),
                        encoding="utf-8",
                    )
                built = run_index(self.root, "build")
                self.assertEqual(0, built.returncode, built.stderr)
                for arguments, expected in (
                    (["--platform", "a2"], [prefix_api]),
                    (["--all-platforms"], [api, prefix_api]),
                    (["--platform", "910"], [api]),
                ):
                    with self.subTest(arguments=arguments):
                        result = self.query(
                            "--domain", "runtime", "--type", "apis", "--status", status,
                            *arguments, query_text=api,
                        )
                        self.assertEqual(0, result.returncode, result.stderr)
                        payload = json.loads(result.stdout)
                        self.assertEqual(expected, [hit["title"] for hit in payload["results"]])

    def test_runtime_all_platforms_is_explicit_and_preserves_filters(self) -> None:
        stable = {"a2_only", "a3_only", "common", "neutral"}
        for arguments, expected in (
            (["--all-platforms"], stable),
            (["--all-platforms", "--status", "draft"], {"located_draft"}),
            (["--all-platforms", "--status", "all"], stable | {"located_draft"}),
            (["--platform", "a2"], {"a2_only", "common", "neutral"}),
            (["--platform", "a2", "--platform", "a3"], {"common", "neutral"}),
            (["--include-unlocated", "--status", "draft"], {"unlocated"}),
        ):
            with self.subTest(arguments=arguments):
                result = self.query("--domain", "runtime", *arguments)
                self.assertEqual(0, result.returncode, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(expected, {Path(hit["path"]).stem for hit in payload["results"]})
                self.assertTrue(all(hit["domain"] == "runtime" for hit in payload["results"]))
                if "--all-platforms" in arguments:
                    self.assertEqual([], payload["request"]["platforms"])
                    self.assertIs(True, payload["request"]["all_platforms"])
                    self.assertIs(True, payload["filters"]["all_platforms"])
                else:
                    self.assertNotIn("all_platforms", payload["request"])
                    self.assertNotIn("all_platforms", payload["filters"])
        for arguments, message in (
            ([], "platform is required"),
            (["--domain", "runtime"], "platform is required"),
            (["--domain", "ops"], "platform is required"),
            (["--all-platforms"], "requires --domain runtime"),
            (["--domain", "ops", "--all-platforms"], "requires --domain runtime"),
            (["--domain", "model", "--all-platforms"], "requires --domain runtime"),
            (["--domain", "runtime", "--all-platforms", "--platform", "a2"], "cannot override"),
            (["--domain", "runtime", "--all-platforms", "--include-unlocated", "--status", "draft"],
             "cannot be combined with --include-unlocated"),
        ):
            with self.subTest(arguments=arguments):
                result = self.query(*arguments)
                self.assertEqual(2, result.returncode, result.stdout)
                self.assertIn(message, json.loads(result.stdout)["error"]["message"])

    def test_runtime_option_preserves_project_defaults_and_index_failures(self) -> None:
        config = self.root / ".cannbot/knowledge.env"
        config.parent.mkdir()
        config.write_text("export CANNBOT_KNOWLEDGE_PLATFORM=a2\n", encoding="utf-8")
        for arguments, expected in (
            ([], {"a2_only", "common", "neutral"}),
            (["--platform", "a3"], {"a3_only", "common", "neutral"}),
        ):
            with self.subTest(arguments=arguments):
                result = self.query("--domain", "runtime", *arguments)
                self.assertEqual(0, result.returncode, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(expected, {Path(hit["path"]).stem for hit in payload["results"]})
                self.assertNotIn("all_platforms", payload["request"])
        blocked = self.query("--domain", "runtime", "--all-platforms")
        self.assertEqual(2, blocked.returncode)
        self.assertIn("cannot override", json.loads(blocked.stdout)["error"]["message"])
        config.unlink()
        card = self.root / "knowledge/runtime/apis/a2_only.md"
        card.write_text(card.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        stale = self.query("--domain", "runtime", "--all-platforms")
        self.assertEqual(2, stale.returncode)
        self.assertIn("changed after index build", json.loads(stale.stdout)["error"]["message"])
        (self.root / "artifacts/indexes/knowledge.sqlite3").unlink()
        missing = self.query("--domain", "runtime", "--all-platforms")
        self.assertEqual(2, missing.returncode)
        self.assertIn("index", json.loads(missing.stdout)["error"]["message"].lower())

    def test_runtime_receipt_binds_opt_in_and_cannot_certify_platform_ready(self) -> None:
        receipt_path = self.work / "search.json"
        result = self.query("--domain", "runtime", "--all-platforms",
                            "--decision", "api-contract", "--receipt", str(receipt_path))
        self.assertEqual(0, result.returncode, result.stderr)
        receipt_text = receipt_path.read_text(encoding="utf-8")
        receipt = json.loads(receipt_text)
        state_path = self.work / "state.json"
        RetrievalAuditTests.write_state(state_path, receipt_path, receipt, platform="a2")
        checked = RetrievalAuditTests.validate_state(self.root, state_path)
        self.assertEqual(1, checked.returncode, checked.stderr)
        payload = json.loads(checked.stdout)
        self.assertFalse(payload["ready"])
        self.assertEqual({"receipt.platform"}, {item["code"] for item in payload["errors"]})
        self.assertEqual(receipt_text, receipt_path.read_text(encoding="utf-8"))
        for change, expected_error in (
            ("missing", "receipt.replay"), ("mismatch", "receipt.request_shape"),
            ("non_boolean", "receipt.request_shape"), ("other_domain", "receipt.replay"),
        ):
            with self.subTest(change=change):
                altered = json.loads(receipt_text)
                request = altered["request"]
                if change == "missing":
                    del request["all_platforms"]
                    del request["filters"]["all_platforms"]
                elif change == "mismatch":
                    request["filters"]["all_platforms"] = False
                elif change == "non_boolean":
                    request["all_platforms"] = request["filters"]["all_platforms"] = 1
                else:
                    request["domain"] = request["filters"]["domain"] = "ops"
                request_hash = hashlib.sha256(json.dumps(
                    request, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                ).encode("utf-8")).hexdigest()
                altered["request_sha256"] = altered["result"]["request_sha256"] = request_hash
                altered["result"]["request"] = request
                altered["result"]["filters"] = request["filters"]
                receipt_path.write_text(json.dumps(altered), encoding="utf-8")
                rejected = RetrievalAuditTests.validate_state(self.root, state_path)
                self.assertEqual(1, rejected.returncode)
                self.assertIn(expected_error, {item["code"] for item in json.loads(rejected.stdout)["errors"]})


class BilingualSearchTests(unittest.TestCase):
    ZH_QUERY = "均值 方差 原语 手写 循环"
    EN_ALT = "welford mean variance primitives replace hand rolled loops"

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.root = self.work / "repository"
        make_root(self.root)
        api_root = self.root / "knowledge/ops/ascendc/apis"
        cards = (
            (
                "zh_mean_variance",
                "均值 方差 原语 优化",
                "在线 均值 方差 计算与 手写 循环 替代",
                "均值 方差 原语 正文。手写 循环 可以被 原语 替代。",
            ),
            (
                "en_welford_primitives",
                "welford mean variance primitives",
                "replace hand rolled loops with welford primitives",
                "welford primitives body text about mean variance accumulation.",
            ),
            (
                "shared_both_legs",
                "welford mean variance 均值 方差",
                "welford primitives plus 均值 方差 对照",
                "welford primitives body also mentions 均值 方差 terms.",
            ),
        )
        for name, title, description, body in cards:
            (api_root / f"{name}.md").write_text(
                SYNTHETIC_CARD.replace("Synthetic API contract", title)
                .replace(
                    "Deterministic API fixture for retrieval tests.",
                    description,
                )
                .replace(
                    "This fixture verifies indexed API lookup and audit behavior without depending on\nrepository knowledge cards.",
                    body,
                ),
                encoding="utf-8",
            )
        built = run_index(self.root, "build")
        self.assertEqual(0, built.returncode, built.stderr)
        self.environment = dict(os.environ)
        self.environment.pop("CANNBOT_KNOWLEDGE_PLATFORM", None)
        self.environment.pop("CANNBOT_KNOWLEDGE_ROOT", None)

    def query(
        self, *arguments: str, query_text: str = ZH_QUERY, alt_query: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable, str(QUERY), "--knowledge-root", str(self.root), "search",
            "--query", query_text, "--match", "text", "--technology", "ascendc",
            "--platform", "a2", "--status", "stable", "-k", "10", *arguments,
        ]
        if alt_query is not None:
            command += ["--alt-query", alt_query]
        return subprocess.run(
            command, cwd=self.root, env=self.environment,
            check=False, text=True, capture_output=True,
        )

    def test_bilingual_interleaves_legs_and_records_ranks(self) -> None:
        result = self.query(alt_query=self.EN_ALT)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("knowledge-search.v6", payload["schema_version"])
        self.assertEqual(self.EN_ALT, payload["alt_query"])
        self.assertEqual(
            {
                "method": "rank-interleave",
                "order": ["original", "alt"],
                "original_hits": 2,
                "alt_hits": 2,
            },
            payload["fusion"],
        )
        paths = [hit["path"] for hit in payload["results"]]
        self.assertEqual("ops/ascendc/apis/zh_mean_variance", paths[0])
        self.assertEqual("ops/ascendc/apis/en_welford_primitives", paths[1])
        en_hit = payload["results"][1]
        self.assertIsNone(en_hit["bilingual"]["original_rank"])
        self.assertIsNone(en_hit["bilingual"]["original_score"])
        self.assertEqual(1, en_hit["bilingual"]["alt_rank"])
        self.assertIsNotNone(en_hit["bilingual"]["alt_score"])
        self.assertEqual("alt", en_hit["bilingual"]["score_leg"])
        self.assertEqual(self.EN_ALT, payload["request"]["alt_query"])

    def test_bilingual_dedupes_card_present_in_both_legs(self) -> None:
        result = self.query(alt_query=self.EN_ALT)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        paths = [hit["path"] for hit in payload["results"]]
        self.assertEqual(1, paths.count("ops/ascendc/apis/shared_both_legs"))
        shared = next(
            hit for hit in payload["results"]
            if hit["path"] == "ops/ascendc/apis/shared_both_legs"
        )
        self.assertIsNotNone(shared["bilingual"]["original_rank"])
        self.assertIsNotNone(shared["bilingual"]["alt_rank"])
        self.assertEqual(
            2 * shared["bilingual"]["original_rank"] - 1,
            shared["rank"],
        )

    def test_bilingual_limit_applies_after_fusion(self) -> None:
        result = self.query("-k", "1", alt_query=self.EN_ALT)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(1, payload["count"])
        self.assertEqual("ops/ascendc/apis/zh_mean_variance", payload["results"][0]["path"])

    def test_default_search_omits_bilingual_fields(self) -> None:
        result = self.query()
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("knowledge-search.v5", payload["schema_version"])
        self.assertNotIn("alt_query", payload)
        self.assertNotIn("fusion", payload)
        self.assertNotIn("alt_query", payload["request"])
        for hit in payload["results"]:
            self.assertNotIn("bilingual", hit)
        default_paths = [hit["path"] for hit in payload["results"]]
        self.assertEqual("ops/ascendc/apis/zh_mean_variance", default_paths[0])

    def test_alt_query_rejects_literal_match(self) -> None:
        result = self.query("--match", "literal", alt_query=self.EN_ALT)
        self.assertEqual(2, result.returncode)
        self.assertIn("--alt-query requires --match text", result.stderr)

    def test_alt_query_must_differ_from_query(self) -> None:
        for alt, expected_error in (
            ("均值 方差 原语 手写 循环", "--alt-query must differ from --query"),
            ("  ", "--alt-query must not be empty"),
            ("均值 方差 原语 手写 循环 ", "--alt-query must differ from --query"),
        ):
            with self.subTest(alt=alt):
                result = self.query(alt_query=alt)
                self.assertEqual(2, result.returncode)
                self.assertIn(expected_error, result.stderr)

    def test_bilingual_receipt_replays_deterministically(self) -> None:
        receipt_path = self.work / "bilingual-receipt.json"
        result = self.query("--receipt", str(receipt_path), alt_query=self.EN_ALT)
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(self.EN_ALT, receipt["request"]["alt_query"])

        spec = importlib.util.spec_from_file_location("bilingual_query", QUERY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        connection, index_metadata = module.open_index(self.root)
        self.addCleanup(connection.close)
        cards = module.load_cards(connection)
        args = module.search_args_from_request(receipt["request"])
        replayed = module.search_payload(
            self.root, cards, index_metadata, connection, args,
            include_current_repository=False,
        )
        self.assertEqual(receipt["result"]["request_sha256"], replayed["request_sha256"])
        self.assertEqual(receipt["result"]["alt_query"], replayed["alt_query"])
        self.assertEqual(receipt["result"]["fusion"], replayed["fusion"])

        def replay_view(entry: dict) -> dict:
            return {
                key: entry.get(key)
                for key in ("path", "rank", "score", "bilingual", "scope_match")
            }

        # local_path embeds the OS-dependent absolute fixture path; only the
        # replay-relevant fields are compared so the case stays portable.
        self.assertEqual(
            [replay_view(hit) for hit in receipt["result"]["results"]],
            [replay_view(hit) for hit in replayed["results"]],
        )
        for hit in replayed["results"]:
            self.assertEqual(
                {"original_rank", "alt_rank", "score_leg", "original_score", "alt_score"},
                set(hit["bilingual"]),
            )

    def test_bilingual_receipt_state_ready(self) -> None:
        """A v6 bilingual receipt must pass retrieval_state validation end to end."""
        receipt_path = self.work / "bilingual-state-receipt.json"
        result = self.query(
            "--decision", "bilingual-recall",
            "--receipt", str(receipt_path),
            alt_query=self.EN_ALT,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual("knowledge-search.v6", receipt["result"]["schema_version"])
        hit = receipt["result"]["results"][0]
        state_path = self.work / "retrieval_state.json"
        state_path.write_text(
            json.dumps(
                {
                    "schema_version": "cannbot-retrieval-state.v1",
                    "target": {"entity": "均值 方差", "platforms": ["a2"]},
                    "decisions": [
                        {
                            "id": "bilingual-recall",
                            "question": "Which card covers the query?",
                            "status": "covered",
                            "receipts": [str(receipt_path)],
                            "evidence": [
                                {"path": hit["path"], "card_sha256": hit["card_sha256"]}
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        validate_state = subprocess.run(
            [
                sys.executable, str(STATE), str(state_path),
                "--knowledge-root", str(self.root), "--require-ready",
            ],
            check=False, text=True, capture_output=True,
        )
        self.assertEqual(0, validate_state.returncode, validate_state.stdout)
        report = json.loads(validate_state.stdout)
        self.assertEqual([], report["errors"])
        self.assertTrue(report["ready"])


class BilingualScopeSearchTests(unittest.TestCase):
    """Bilingual search must merge Scope audits across legs without duplication."""

    ZH_QUERY = "均值 方差 原语 手写 循环"
    EN_ALT = "welford mean variance primitives replace hand rolled loops"
    SCOPE = {"schema": "model.inference.v1", "any_of": [{"all_of": {"phase": ["prefill"]}}]}

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.root = self.work / "repository"
        make_root(self.root)
        cards_dir = self.root / "knowledge/model/inference/optimizations"
        cards_dir.mkdir(parents=True)
        definitions = {
            "scope_conflict_decode": (
                "双语冲突 welford 均值 方差",
                "conflict card body with welford mean variance 均值 方差 terms.",
                {"phase": ["decode"]},
            ),
            "scope_match_prefill": (
                "双语匹配 welford 均值 方差",
                "match card body with welford mean variance 均值 方差 terms.",
                {"phase": ["prefill"]},
            ),
            "scope_unknown_zh": (
                "未知范围 均值 方差 原语",
                "unknown card body only 均值 方差 原语 手写 循环 terms.",
                None,
            ),
        }
        for slug, (title, body, declaration) in definitions.items():
            metadata = {
                "type": "Optimization",
                "title": title,
                "description": "Bilingual Scope fixture for dual search tests.",
                "tags": ["task.optimization", "topic.graph_execution"],
                "status": "stable",
                "sources": [{"resource": "https://example.com/cann/synthetic-api", "role": "primary"}],
                "created_at": "2026-08-18T00:00:00Z",
                "updated_at": "2026-08-18T00:00:00Z",
                "platforms": ["a3"],
            }
            if declaration is not None:
                metadata["scope"] = {"schema": "model.inference.v1", "any_of": [{"all_of": declaration}]}
            (cards_dir / f"{slug}.md").write_text(
                "---\n" + json.dumps(metadata, ensure_ascii=False) + "\n---\n\n# " + title + "\n\n" + body + "\n",
                encoding="utf-8",
            )
        built = run_index(self.root, "build")
        self.assertEqual(0, built.returncode, built.stderr)
        self.environment = dict(os.environ)
        self.environment.pop("CANNBOT_KNOWLEDGE_PLATFORM", None)
        self.environment.pop("CANNBOT_KNOWLEDGE_ROOT", None)

    def query(self, *arguments: str, alt_query: str | None = None) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable, str(QUERY), "--knowledge-root", str(self.root), "search",
            "--query", self.ZH_QUERY, "--match", "text", "--technology", "inference",
            "--platform", "a3", "--status", "stable", "-k", "10",
            "--scope-json", json.dumps(self.SCOPE, ensure_ascii=False), *arguments,
        ]
        if alt_query is not None:
            command += ["--alt-query", alt_query]
        return subprocess.run(
            command, cwd=self.root, env=self.environment,
            check=False, text=True, capture_output=True,
        )

    def test_bilingual_scope_merges_conflicts_once_and_keeps_states(self) -> None:
        dual = self.query(alt_query=self.EN_ALT)
        self.assertEqual(0, dual.returncode, dual.stderr)
        payload = json.loads(dual.stdout)
        self.assertEqual("knowledge-search.v6", payload["schema_version"])
        self.assertTrue(payload["scope_filter"]["enabled"])
        # The conflicting card matches both legs; the merged audit must list it once.
        excluded_paths = [item["path"] for item in payload["scope_filter"]["excluded"]]
        self.assertEqual(
            ["model/inference/optimizations/scope_conflict_decode"], excluded_paths
        )
        self.assertEqual(1, payload["scope_filter"]["excluded_count"])
        self.assertEqual(
            "conflict", payload["scope_filter"]["excluded"][0]["scope_match"]["state"]
        )
        self.assertEqual(
            {"method": "rank-interleave", "order": ["original", "alt"], "original_hits": 2, "alt_hits": 1},
            payload["fusion"],
        )
        hits = {hit["path"]: hit for hit in payload["results"]}
        self.assertNotIn("model/inference/optimizations/scope_conflict_decode", hits)
        self.assertEqual("match", hits["model/inference/optimizations/scope_match_prefill"]["scope_match"]["state"])
        self.assertEqual("unknown", hits["model/inference/optimizations/scope_unknown_zh"]["scope_match"]["state"])

        # The single-leg run must report the identical exclusion audit.
        single = self.query()
        self.assertEqual(0, single.returncode, single.stderr)
        single_payload = json.loads(single.stdout)
        self.assertEqual(
            single_payload["scope_filter"]["excluded"],
            payload["scope_filter"]["excluded"],
        )
        self.assertEqual(
            single_payload["scope_filter"]["excluded_count"],
            payload["scope_filter"]["excluded_count"],
        )

    def test_scope_audit_is_part_of_v6_receipt_replay(self) -> None:
        """Tampering with or dropping the merged Scope audit must fail replay."""
        receipt_path = self.work / "bilingual-scope-receipt.json"
        result = self.query(
            "--decision", "scope-replay",
            "--receipt", str(receipt_path),
            alt_query=self.EN_ALT,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(1, receipt["result"]["scope_filter"]["excluded_count"])

        state_path = self.work / "retrieval_state.json"
        hit = receipt["result"]["results"][0]
        state_path.write_text(
            json.dumps(
                {
                    "schema_version": "cannbot-retrieval-state.v1",
                    "target": {"entity": "均值 方差", "platforms": ["a3"]},
                    "decisions": [
                        {
                            "id": "scope-replay",
                            "question": "Which card covers the query?",
                            "status": "covered",
                            "receipts": [str(receipt_path)],
                            "evidence": [
                                {"path": hit["path"], "card_sha256": hit["card_sha256"]}
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        def validate() -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [
                    sys.executable, str(STATE), str(state_path),
                    "--knowledge-root", str(self.root), "--require-ready",
                ],
                check=False, text=True, capture_output=True,
            )

        original = validate()
        self.assertEqual(0, original.returncode, original.stdout)

        tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
        tampered["result"]["scope_filter"]["excluded"] = []
        tampered["result"]["scope_filter"]["excluded_count"] = 0
        receipt_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
        emptied = validate()
        self.assertEqual(1, emptied.returncode)
        self.assertIn("scope_filter", emptied.stdout)

        tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
        del tampered["result"]["scope_filter"]
        receipt_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
        dropped = validate()
        self.assertEqual(1, dropped.returncode)
        self.assertIn("scope_filter", dropped.stdout)


if __name__ == "__main__":
    unittest.main()
