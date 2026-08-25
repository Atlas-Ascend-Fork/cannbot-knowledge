from __future__ import annotations

import hashlib
import io
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

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


class RetrievalIndexTests(unittest.TestCase):
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

    def test_literal_search_prioritizes_title_and_ignores_managed_related_block(self) -> None:
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
                "<!-- cannbot:related:start -->\n\n"
                "# Related\n\n- [GetCurNpuArch](get_cur_npu_arch.md)\n\n"
                "<!-- cannbot:related:end -->",
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
            self.assertEqual("Platform API usage", results[1]["title"])
            self.assertNotIn("Related navigation only", [item["title"] for item in results])


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
    ) -> dict[str, object]:
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


if __name__ == "__main__":
    unittest.main()
