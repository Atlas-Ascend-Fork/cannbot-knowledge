# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------
"""Compare source registration against the same fixed acceptance and rejection cases."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REVISION = "b523035a08ef573b6bc476c8ab2a34733ba069a4"
OPS_REVISION = "955f8b33985b6d72989ebff341bb9c2c564a51bc"
LOCAL = f"cann-runtime-raw/runtime/{REVISION}/include/external/acl/acl_rt.h"
REMOTE = f"https://gitcode.com/cann/runtime/blob/{REVISION}/include/external/acl/acl_rt.h"
OPS = f"cann-ops-raw/ascendc/ops-nn/{OPS_REVISION}/README.md"
# Expectations are fixed before execution. Unknown repositories are not resolved.
SAMPLES = [
    ("runtime_local", LOCAL, "unregistered", "accepted"),
    ("runtime_remote", REMOTE, "unregistered", "accepted"),
    ("runtime_unknown_revision", LOCAL.replace(REVISION, "a" * 40), "unregistered", "rejected"),
    ("runtime_traversal", LOCAL.replace("/include/", "/../include/"), "unregistered", "rejected"),
    ("runtime_branch", REMOTE.replace(REVISION, "master"), "unregistered", "rejected"),
    ("unknown_root", f"unknown-source/{REVISION}/file.h", "unregistered", "unregistered"),
    ("operator_local", OPS, "accepted", "accepted"),
    ("operator_unknown_revision", OPS.replace(OPS_REVISION, "a" * 40), "rejected", "rejected"),
    ("operator_traversal", OPS.replace("/README.md", "/../README.md"), "rejected", "rejected"),
    ("operator_remote", f"https://gitcode.com/cann/ops-nn/blob/{OPS_REVISION}/README.md", "accepted", "accepted"),
]


def probe(root):
    sys.path.insert(0, str(root))
    from governance.contracts.knowledge import Contract
    from governance.contracts.source_resources import git_source

    contract = Contract(root)
    rows = []
    for name, resource, _, _ in SAMPLES:
        try:
            source = git_source(contract, resource)
            outcome = "accepted" if source is not None else "unregistered"
        except ValueError:
            outcome = "rejected"
        rows.append({"id": name, "input": resource, "outcome": outcome})
    metadata = {
        "type": "API", "title": "Synthetic source fixture", "description": "Source contract fixture.",
        "tags": ["task.lookup", "topic.compilation"], "status": "stable", "platforms": ["a2"],
        "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
        "sources": [{"resource": LOCAL}], "source_headers": ["include/external/acl/acl_rt.h"],
    }
    issues = contract.validate_card(Path("knowledge/runtime/apis/synthetic_api.md"), metadata, "# Fixture\n")
    rows.append({"id": "runtime_card", "outcome": "rejected" if issues else "accepted"})
    metadata["sources"] = [{"resource": "https://example.invalid/fixture"}]
    issues = contract.validate_card(Path("knowledge/runtime/apis/synthetic_api.md"), metadata, "# Fixture\n")
    rows.append({"id": "existing_api_metadata", "outcome": "rejected" if issues else "accepted"})
    rows.append({"id": "git_source_count", "outcome": str(sum(d.get("kind") == "git" for d in contract.local_sources.values()))})
    return rows


class RuntimeSourceRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep these imports lazy so CLI probes still load each checkout's contract.
        sys.path.insert(0, str(ROOT))
        from governance.contracts.knowledge import Contract
        from governance.contracts.source_resources import git_source

        cls.contract_type = Contract
        cls.git_source = staticmethod(git_source)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / "governance/schemas", self.root / "governance/schemas")
        self.contract = self.contract_type(self.root)
        self.runtime = self.contract.local_sources["runtime"]
        self.revision = self.runtime["revisions"][0]
        self.header = "include/external/acl/acl_rt.h"
        self.local = f"{self.runtime['root']}/{self.revision}/{self.header}"
        self.remote = f"{self.runtime['repository']}/blob/{self.revision}/{self.header}"
        self.unknown_revision = "0" * 40
        self.assertNotIn(self.unknown_revision, self.runtime["revisions"])

    def test_runtime_registration(self):
        self.assertEqual("git", self.runtime["kind"])
        self.assertEqual("cann-runtime-raw/runtime", self.runtime["root"])
        self.assertEqual("https://gitcode.com/cann/runtime", self.runtime["repository"])
        self.assertEqual("get_resources.sh", self.runtime["fetch_script"])
        for revision in self.runtime["revisions"]:
            with self.subTest(revision=revision):
                self.assertRegex(revision, r"^[0-9a-f]{40}$")

    def test_runtime_local_and_remote_sources(self):
        for revision in self.runtime["revisions"]:
            local = f"{self.runtime['root']}/{revision}/{self.header}"
            remote = f"{self.runtime['repository']}/blob/{revision}/{self.header}"
            for resource in (local, remote):
                with self.subTest(resource=resource):
                    source = self.git_source(self.contract, resource)
                    self.assertIsNotNone(source)
                    self.assertEqual(local, source.resource)
                    self.assertEqual(remote, source.url)

    def test_runtime_invalid_sources(self):
        invalid = (
            self.local.replace(self.revision, self.unknown_revision),
            self.remote.replace(self.revision, self.unknown_revision),
            self.local.replace(self.revision, "master"),
            self.remote.replace(self.revision, "master"),
            self.local.replace("/include/", "/../include/"),
            self.remote.replace("/include/", "/%2e%2e/include/"),
            self.local.replace(self.header, ".git/config"),
            self.remote.replace(self.header, ".git/config"),
        )
        for resource in invalid:
            with self.subTest(resource=resource), self.assertRaises(ValueError):
                self.git_source(self.contract, resource)

    def test_unknown_source_is_unregistered(self):
        for resource in (
            f"unknown-source/{self.revision}/file.h",
            f"https://example.invalid/unknown/blob/{self.revision}/file.h",
        ):
            with self.subTest(resource=resource):
                self.assertIsNone(self.git_source(self.contract, resource))

    def test_existing_operator_sources_remain_compatible(self):
        definition = self.contract.local_sources["ops_nn"]
        self.assertNotIn(self.unknown_revision, definition["revisions"])
        for revision in definition["revisions"]:
            local = f"{definition['root']}/{revision}/README.md"
            remote = f"{definition['repository']}/blob/{revision}/README.md"
            for resource in (local, remote):
                with self.subTest(resource=resource):
                    self.assertEqual(local, self.git_source(self.contract, resource).resource)
            for resource in (
                local.replace(revision, self.unknown_revision),
                local.replace("/README.md", "/../README.md"),
            ):
                with self.subTest(resource=resource), self.assertRaises(ValueError):
                    self.git_source(self.contract, resource)

    def test_runtime_api_card_admission(self):
        metadata = {
            "type": "API", "title": "Synthetic source fixture", "description": "Source contract fixture.",
            "tags": ["task.lookup", "topic.compilation"], "status": "stable", "platforms": ["a2"],
            "created_at": "2026-08-18T00:00:00Z", "updated_at": "2026-08-18T00:00:00Z",
            "sources": [{"resource": self.local}], "source_headers": [self.header],
        }
        relative = Path("knowledge/runtime/apis/synthetic_api.md")
        for resource in (self.local, "https://example.invalid/fixture"):
            metadata["sources"] = [{"resource": resource}]
            with self.subTest(resource=resource):
                self.assertEqual([], self.contract.validate_card(relative, metadata, "# Fixture\n"))
        for resource in (
            self.local.replace(self.revision, self.unknown_revision),
            self.local.replace("/include/", "/../include/"),
        ):
            metadata["sources"] = [{"resource": resource}]
            with self.subTest(resource=resource):
                self.assertTrue(self.contract.validate_card(relative, metadata, "# Fixture\n"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--probe-root", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.probe_root:
        print(json.dumps(probe(args.probe_root.resolve())))
        return 0
    if not args.baseline_root or not args.candidate_root:
        parser.error("--baseline-root and --candidate-root are required")
    candidate = args.candidate_root.resolve()
    output = (args.output or candidate / "artifacts/evals/runtime_source_registration_ab.json").resolve()
    if not output.is_relative_to(candidate / "artifacts"):
        parser.error("output must stay below the candidate artifacts directory")
    expected = [(a, b) for _, _, a, b in SAMPLES] + [("rejected", "accepted"), ("accepted", "accepted"), ("4", "5")]
    report = {"dataset_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "versions": {}, "cases": []}
    observations = []
    for label, root in (("A", args.baseline_root.resolve()), ("B", candidate)):
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--probe-root", str(root)],
                                check=True, capture_output=True, text=True)
        observations.append(json.loads(result.stdout))
        report["versions"][label] = {
            "head": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
            "registry_sha256": hashlib.sha256((root / "governance/schemas/registries.yaml").read_bytes()).hexdigest(),
        }
    for a, b, (want_a, want_b) in zip(*observations, expected, strict=True):
        assert a["id"] == b["id"]
        report["cases"].append({"id": a["id"], "A": a["outcome"], "B": b["outcome"],
                                "expected_A": want_a, "expected_B": want_b,
                                "passed": a["outcome"] == want_a and b["outcome"] == want_b})
    report["passed"] = all(case["passed"] for case in report["cases"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(report["cases"]), "passed": report["passed"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
