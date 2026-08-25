from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
GRAPH_SCRIPT = SKILL_ROOT / "scripts/knowledge_graph.py"
INGEST_SCRIPT = SKILL_ROOT / "scripts/knowledge_ingest.py"
REPOSITORY_ROOT = SKILL_ROOT.parents[2]


class KnowledgeGraphTests(unittest.TestCase):
    def card(self, title: str, card_type: str, description: str) -> str:
        return (
            "---\n"
            f"type: {card_type}\n"
            f"title: {title}\n"
            f"description: {description}\n"
            "tags: [task.lookup, topic.data_movement]\n"
            "status: draft\n"
            "sources: []\n"
            "platforms: []\n"
            "created_at: '2026-08-22T00:00:00Z'\n"
            "updated_at: '2026-08-22T00:00:00Z'\n"
            "---\n\n"
            f"# {title}\n\n{description}\n"
        )

    def make_root(self, base: Path, api_count: int = 1) -> Path:
        root = base / "repository"
        shutil.copytree(REPOSITORY_ROOT / "governance", root / "governance")
        api_root = root / "knowledge/ops/ascendc/apis"
        runbook_root = root / "knowledge/ops/ascendc/runbooks/compilation"
        api_root.mkdir(parents=True)
        runbook_root.mkdir(parents=True)
        for index in range(api_count):
            (api_root / f"get_tiling_data_{index}.md").write_text(
                self.card(
                    f"GET_TILING_DATA SharedContract {index}",
                    "API",
                    f"GET_TILING_DATA SharedContract interface contract variant {index}.",
                ),
                encoding="utf-8",
            )
        (runbook_root / "get_tiling_data_failure.md").write_text(
            self.card(
                "GET_TILING_DATA failure",
                "Runbook",
                "GET_TILING_DATA failure triage and interface boundary.",
            ),
            encoding="utf-8",
        )
        synchronized = subprocess.run(
            [
                sys.executable,
                str(INGEST_SCRIPT),
                "--knowledge-root",
                str(root),
                "sync-indexes",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, synchronized.returncode, synchronized.stderr)
        return root

    def run_graph(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(GRAPH_SCRIPT),
                "--knowledge-root",
                str(root),
                *arguments,
            ],
            check=False,
            text=True,
            capture_output=True,
        )

    def prepare_reviews(
        self, root: Path, accept_all_api_candidates: bool = False
    ) -> list[Path]:
        self.assertEqual(0, self.run_graph(root, "candidates").returncode)
        self.assertEqual(0, self.run_graph(root, "make-shards", "--count", "2").returncode)
        manifest = json.loads(
            (root / "artifacts/graphs/judgment_shards/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        outputs: list[Path] = []
        for shard in manifest["shards"]:
            packet = json.loads((root / shard["path"]).read_text(encoding="utf-8"))
            results = []
            for item in packet["focals"]:
                focal = item["focal"]
                kept = []
                for candidate in item["candidates"]:
                    profiles = {focal["profile"], candidate["profile"]}
                    accept = profiles == {"runbooks", "apis"}
                    accept = accept or (
                        accept_all_api_candidates
                        and focal["profile"] == candidate["profile"] == "apis"
                    )
                    if accept:
                        kept.append(
                            {
                                "target_id": candidate["id"],
                                "relation": candidate["provisional_relation"],
                                "reason": (
                                    "Agent read both complete cards and found that the practical "
                                    "failure boundary directly depends on the interface contract."
                                ),
                                "confidence": "high",
                                "strength": "direct",
                                "evidence": {"bridge": "shared executable contract"},
                            }
                        )
                results.append(
                    {
                        "focal_id": focal["id"],
                        "candidate_set_fingerprint": item["candidate_set_fingerprint"],
                        "kept": kept,
                        "needs_adjudication": [],
                    }
                )
            output = root / f"review-{shard['shard_id']}.json"
            output.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "shard_id": shard["shard_id"],
                        "shard_fingerprint": shard["shard_fingerprint"],
                        "judge": f"subagent:test-{shard['shard_id']}",
                        "results": results,
                    }
                ),
                encoding="utf-8",
            )
            outputs.append(output)
        return outputs

    def aggregate(self, root: Path, reviews: list[Path]) -> subprocess.CompletedProcess[str]:
        arguments = ["aggregate"]
        for review in reviews:
            arguments.extend(("--input", str(review)))
        return self.run_graph(root, *arguments)

    def test_agent_review_build_is_idempotent_and_managed_links_are_not_authored_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            reviews = self.prepare_reviews(root)
            runbook = root / "knowledge/ops/ascendc/runbooks/compilation/get_tiling_data_failure.md"
            original_text = runbook.read_text(encoding="utf-8")
            aggregated = self.aggregate(root, reviews)
            self.assertEqual(0, aggregated.returncode, aggregated.stderr)
            first = self.run_graph(root, "finalize")
            self.assertEqual(0, first.returncode, first.stderr)
            first_text = runbook.read_text(encoding="utf-8")
            self.assertIn("<!-- cannbot:related:start -->", first_text)
            self.assertIn("get_tiling_data_0.md", first_text)
            authored_text = first_text.split("<!-- cannbot:related:start -->", 1)[0].rstrip() + "\n"
            self.assertEqual(original_text, authored_text)

            graph_path = root / "artifacts/graphs/graph.json"
            first_graph = graph_path.read_bytes()
            graph = json.loads(first_graph)
            self.assertTrue(any(edge["relation"] == "exemplifies" for edge in graph["edges"]))
            self.assertFalse(any(edge["relation"] == "links_to" for edge in graph["edges"]))
            self.assertTrue(any(edge["relation"] == "part_of" for edge in graph["edges"]))

            second = self.run_graph(root, "finalize")
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(first_text, runbook.read_text(encoding="utf-8"))
            self.assertEqual(first_graph, graph_path.read_bytes())

    def test_verify_fails_closed_when_a_card_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            reviews = self.prepare_reviews(root)
            self.assertEqual(0, self.aggregate(root, reviews).returncode)
            self.assertEqual(0, self.run_graph(root, "finalize").returncode)
            card = root / "knowledge/ops/ascendc/apis/get_tiling_data_0.md"
            card.write_text(
                card.read_text(encoding="utf-8").replace(
                    "interface contract", "updated interface contract"
                ),
                encoding="utf-8",
            )
            verified = self.run_graph(root, "verify")
        self.assertEqual(2, verified.returncode)
        self.assertIn("edge judgment cache is stale", verified.stderr)

    def test_agent_edges_are_not_limited_to_four_per_card(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary), api_count=6)
            reviews = self.prepare_reviews(root, accept_all_api_candidates=True)
            aggregated = self.aggregate(root, reviews)
            self.assertEqual(0, aggregated.returncode, aggregated.stderr)
            finalized = self.run_graph(root, "finalize")
            self.assertEqual(0, finalized.returncode, finalized.stderr)
            graph = json.loads(
                (root / "artifacts/graphs/graph.json").read_text(encoding="utf-8")
            )
            focal_id = "ops/ascendc/apis/get_tiling_data_0"
            degree = sum(
                edge["relation"] in {"same_topic", "related"}
                and focal_id in {edge["source"], edge["target"]}
                for edge in graph["edges"]
            )
        self.assertGreaterEqual(degree, 5)

    def test_broad_recall_includes_body_symbol_mentions_in_both_directions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            runbook = root / "knowledge/ops/ascendc/runbooks/compilation/get_tiling_data_failure.md"
            runbook.write_text(
                runbook.read_text(encoding="utf-8")
                + "\nThe recovery path calls UniqueRecoverySymbol before retrying.\n",
                encoding="utf-8",
            )
            api = root / "knowledge/ops/ascendc/apis/unique_recovery_symbol.md"
            api.write_text(
                self.card(
                    "UniqueRecoverySymbol",
                    "API",
                    "A unique interface contract used by the recovery path.",
                ),
                encoding="utf-8",
            )
            synchronized = subprocess.run(
                [
                    sys.executable,
                    str(INGEST_SCRIPT),
                    "--knowledge-root",
                    str(root),
                    "sync-indexes",
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, synchronized.returncode, synchronized.stderr)
            recalled = self.run_graph(root, "candidates", "--limit", "1")
            self.assertEqual(0, recalled.returncode, recalled.stderr)
            candidates = json.loads(
                (root / "artifacts/graphs/candidates.json").read_text(encoding="utf-8")
            )["candidates"]
            left = "ops/ascendc/runbooks/compilation/get_tiling_data_failure"
            right = "ops/ascendc/apis/unique_recovery_symbol"
            left_items = {item["target"]: item for item in candidates[left]}
            right_items = {item["target"]: item for item in candidates[right]}
        self.assertIn(right, left_items)
        self.assertIn(left, right_items)
        self.assertIn("body_symbol_mention", left_items[right]["recall_channels"])

    def test_candidate_recall_does_not_filter_by_platform_or_cann_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            left_path = root / "knowledge/ops/ascendc/apis/get_tiling_data_0.md"
            left_path.write_text(
                left_path.read_text(encoding="utf-8").replace(
                    "platforms: []\n",
                    "platforms: [a2]\ncann_versions: ['8.0']\n",
                ),
                encoding="utf-8",
            )
            right_path = root / "knowledge/ops/ascendc/runbooks/compilation/get_tiling_data_failure.md"
            right_path.write_text(
                right_path.read_text(encoding="utf-8").replace(
                    "platforms: []\n",
                    "platforms: ['950']\ncann_versions: ['9.1']\n",
                ),
                encoding="utf-8",
            )
            recalled = self.run_graph(root, "candidates", "--limit", "1")
            self.assertEqual(0, recalled.returncode, recalled.stderr)
            candidates = json.loads(
                (root / "artifacts/graphs/candidates.json").read_text(encoding="utf-8")
            )["candidates"]
            left = "ops/ascendc/apis/get_tiling_data_0"
            right = "ops/ascendc/runbooks/compilation/get_tiling_data_failure"
        self.assertIn(right, {item["target"] for item in candidates[left]})
        self.assertIn(left, {item["target"] for item in candidates[right]})

    def test_agent_can_add_a_fingerprinted_relation_outside_the_shortlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            self.assertEqual(0, self.run_graph(root, "candidates").returncode)
            candidate_path = root / "artifacts/graphs/candidates.json"
            candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
            left = "ops/ascendc/runbooks/compilation/get_tiling_data_failure"
            right = "ops/ascendc/apis/get_tiling_data_0"
            candidates["candidates"][left] = [
                item
                for item in candidates["candidates"][left]
                if item["target"] != right
            ]
            candidates["candidates"][right] = [
                item
                for item in candidates["candidates"][right]
                if item["target"] != left
            ]
            candidate_path.write_text(json.dumps(candidates), encoding="utf-8")
            self.assertEqual(
                0, self.run_graph(root, "make-shards", "--count", "2").returncode
            )
            manifest = json.loads(
                (root / "artifacts/graphs/judgment_shards/manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            reviews = []
            for shard in manifest["shards"]:
                packet = json.loads((root / shard["path"]).read_text(encoding="utf-8"))
                results = []
                for item in packet["focals"]:
                    focal_id = item["focal"]["id"]
                    kept = []
                    if focal_id == left:
                        kept.append(
                            {
                                "target_id": right,
                                "agent_discovered": True,
                                "target_fingerprint": candidates["card_fingerprints"][right],
                                "relation": "exemplifies",
                                "judge": "subagent:targeted-auditor",
                                "reason": (
                                    "The Agent read both complete cards and found the failure "
                                    "depends directly on this interface contract."
                                ),
                                "confidence": "high",
                                "strength": "direct",
                                "evidence": {"bridge": "failure to interface contract"},
                            }
                        )
                    results.append(
                        {
                            "focal_id": focal_id,
                            "candidate_set_fingerprint": item[
                                "candidate_set_fingerprint"
                            ],
                            "kept": kept,
                            "needs_adjudication": [],
                        }
                    )
                review = root / f"review-{shard['shard_id']}.json"
                review.write_text(
                    json.dumps(
                        {
                            "schema_version": 2,
                            "shard_id": shard["shard_id"],
                            "shard_fingerprint": shard["shard_fingerprint"],
                            "judge": f"subagent:discovery-{shard['shard_id']}",
                            "results": results,
                        }
                    ),
                    encoding="utf-8",
                )
                reviews.append(review)
            aggregated = self.aggregate(root, reviews)
            self.assertEqual(0, aggregated.returncode, aggregated.stderr)
            cache = json.loads(
                (root / "artifacts/graphs/edge_judgments.json").read_text(
                    encoding="utf-8"
                )
            )
        accepted = next(
            item
            for item in cache["judgments"]
            if item["relation"] == "exemplifies"
            and {item["source"], item["target"]} == {left, right}
        )
        self.assertIn("subagent:targeted-auditor", accepted["judge"])

    def test_aggregate_requires_multiple_agent_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            reviews = self.prepare_reviews(root)
            for review in reviews:
                payload = json.loads(review.read_text(encoding="utf-8"))
                payload["judge"] = "subagent:only-one"
                review.write_text(json.dumps(payload), encoding="utf-8")
            aggregated = self.aggregate(root, reviews)
        self.assertEqual(2, aggregated.returncode)
        self.assertIn("at least two independent Agent judges", aggregated.stderr)

    def test_relation_type_conflict_requires_agent_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary), api_count=3)
            reviews = self.prepare_reviews(root, accept_all_api_candidates=True)
            conflict_pairs = {
                frozenset(
                    {
                        "ops/ascendc/apis/get_tiling_data_0",
                        "ops/ascendc/apis/get_tiling_data_1",
                    }
                ),
                frozenset(
                    {
                        "ops/ascendc/apis/get_tiling_data_0",
                        "ops/ascendc/apis/get_tiling_data_2",
                    }
                ),
            }
            changed: set[frozenset[str]] = set()
            for review in reviews:
                payload = json.loads(review.read_text(encoding="utf-8"))
                for result in payload["results"]:
                    for decision in result["kept"]:
                        pair = frozenset(
                            {result["focal_id"], decision["target_id"]}
                        )
                        if pair in conflict_pairs and pair not in changed:
                            decision["relation"] = "related"
                            changed.add(pair)
                review.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(conflict_pairs, changed)
            conflicted = self.aggregate(root, reviews)
            self.assertEqual(2, conflicted.returncode)
            self.assertIn("require Agent adjudication", conflicted.stderr)
            conflict_packet = json.loads(
                (root / "artifacts/graphs/adjudication/conflicts.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(2, len(conflict_packet["conflicts"]))
            adjudications = []
            for index, conflict in enumerate(conflict_packet["conflicts"]):
                adjudication = root / f"adjudication-{index}.json"
                adjudication.write_text(
                    json.dumps(
                        {
                            "schema_version": 2,
                            "conflict_fingerprint": conflict_packet[
                                "conflict_fingerprint"
                            ],
                            "judge": f"subagent:adjudicator-{index}",
                            "decisions": [
                                {
                                    "left": conflict["pair"][0],
                                    "right": conflict["pair"][1],
                                    "relation": "related",
                                    "reason": (
                                        "After reading both complete cards, the Agent found "
                                        "distinct variants in one workflow rather than one "
                                        "identical contract."
                                    ),
                                    "confidence": "high",
                                    "strength": "supporting",
                                    "evidence": {
                                        "bridge": "shared workflow, distinct variants"
                                    },
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                adjudications.append(adjudication)
            arguments = ["aggregate"]
            for review in reviews:
                arguments.extend(("--input", str(review)))
            for adjudication in adjudications:
                arguments.extend(("--adjudication", str(adjudication)))
            aggregated = self.run_graph(root, *arguments)
            self.assertEqual(0, aggregated.returncode, aggregated.stderr)
            cache = json.loads(
                (root / "artifacts/graphs/edge_judgments.json").read_text(
                    encoding="utf-8"
                )
            )
        accepted = [
            item
            for item in cache["judgments"]
            if frozenset({item["source"], item["target"]}) in conflict_pairs
        ]
        self.assertEqual(2, len(accepted))
        self.assertTrue(all(item["relation"] == "related" for item in accepted))

    def test_aggregate_requires_every_agent_shard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            reviews = self.prepare_reviews(root)
            incomplete = self.aggregate(root, reviews[:1])
        self.assertEqual(2, incomplete.returncode)
        self.assertIn("missing Agent review shards", incomplete.stderr)


if __name__ == "__main__":
    unittest.main()
