#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------

"""Regression acceptance for PR1264 migration facts and traceable dispositions.

Read the actual knowledge decision tables. Unequal request lengths and FP8
provide counterexamples to the faulty rules identified during review. These
checks verify the stored facts; they do not simulate an Agent or NPU execution.
"""

from copy import deepcopy
import hashlib
from itertools import accumulate
from pathlib import Path
import re
import unicodedata
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIA = "model/inference/concepts/kernels/fused_infer_attention_score"
PROFILER = "model/inference/guides/optimization/npu_profiling_collection_and_metrics"
LI_MODE = "model/inference/concepts/quantization/li_cache_quantization_mode_contract"
SK_ANALYSIS = "model/inference/guides/optimization/superkernel_scope_analysis_and_validation"
API = "https://www.hiascend.com/doc_center/source/zh/Pytorch/600/apiref/apilist/ptaoplist_000837.html"


def card(concept):
    raw = (ROOT / "knowledge" / (concept + ".md")).read_text()
    _, metadata, body = raw.split("---", 2)
    return yaml.safe_load(metadata), body


def table(body, first_column):
    """Read a human-facing Markdown decision table by its header."""
    rows = iter(body.splitlines())
    for line in rows:
        if line.startswith("| " + first_column + " |"):
            next(rows)  # Markdown separator
            result = {}
            for line in rows:
                if not line.startswith("|"):
                    return result
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if cells[0] in result:
                    raise ValueError("duplicate decision row: " + cells[0])
                result[cells[0]] = cells[1:]
            return result
    raise ValueError("missing decision table: " + first_column)


def section_fact_errors(ledger, coverage):
    """Check source ownership independently of the section's chosen fact IDs."""
    facts = {fact["id"]: fact for fact in coverage["facts"]}
    errors = []
    for path, sections in ledger["sections"].items():
        for section in sections:
            for fact_id in section.get("facts", []):
                if path not in facts.get(fact_id, {}).get("source_paths", []):
                    errors.append((path, section["id"], fact_id))
    return errors


def normalized_fact_text(text):
    """Ignore Markdown spelling and whitespace, preserving words and negation."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[\s`*\\]", "", text)


def api_source_fact_errors(row, body):
    """Check independently curated source clauses against the technical body."""
    content = normalized_fact_text(body.split("\n## Evidence", 1)[0])
    return [
        (fact["source_excerpt"], term)
        for fact in row["source_facts"]
        for term in fact["required_content"]
        if normalized_fact_text(term) not in content
    ]


class InferenceSkillMigrationFacts(unittest.TestCase):
    def assert_call(self, path, q_lengths, kv_lengths, expected_kv, cache,
                    sparse_mode=3, mask="causal"):
        _, body = card(FIA)
        row = table(body, "路径 ID")[path]
        self.assertEqual(6, len(row) + 1)
        kv_source, q_field, kv_field, sparse, actual_mask = row
        fields = {
            "actual_seq_lengths_cu_q": list(accumulate(q_lengths)),
            "actual_seq_lengths_cu_list_q": list(accumulate(q_lengths)),
            "actual_seq_lengths_kv": kv_lengths,
            "actual_seq_lengths_list_kv": kv_lengths,
            "actual_seq_lengths_cu_kv": list(accumulate(kv_lengths)),
        }
        self.assertEqual(list(accumulate(q_lengths)), fields[q_field])
        self.assertEqual(expected_kv, fields[kv_field])
        self.assertEqual(cache, kv_source)
        self.assertEqual(sparse_mode, int(sparse))
        self.assertEqual(mask, actual_mask)

    def test_dense_paged_prefill_does_not_cumulate_kv(self):
        self.assert_call("qwen_dense_prefill", [3, 5], [3, 5], [3, 5], "paged")

    def test_moe_direct_prefill_cumulates_kv(self):
        self.assert_call("qwen3_moe_prefill", [3, 5], [3, 5], [3, 8], "current")

    def test_decode_uses_request_lengths_with_cumulative_queries(self):
        for path in ("qwen_dense_decode", "qwen_dense_decode_npugraph_ex",
                     "qwen3_moe_decode_bf16"):
            with self.subTest(path=path):
                self.assert_call(path, [1, 1], [9, 13], [9, 13], "paged")

    def test_float8_decode_has_separate_mask_branch(self):
        self.assert_call("qwen3_moe_decode_float8", [1, 1], [9, 13],
                         [9, 13], "paged", sparse_mode=0, mask="None")
        _, body = card(FIA)
        self.assertIn("key_quant_mode=value_quant_mode=4", body)
        self.assertIn("dequant_scale_key/value", body)

    def test_noncontiguous_paged_slots_keep_request_isolation(self):
        _, body = card("model/inference/concepts/frameworks/kv_cache_manager")
        section = body.split("### 普通分页缓存的物理槽位", 1)[1].split("\n## ", 1)[0]
        expression = section.split("```python\n", 1)[1].split("```", 1)[0]
        # Execute the published scalar address recipe against noncontiguous
        # allocations; contiguous tables would hide the old linear-index bug.
        for batch_idx, position, expected in ((0, 129, 257), (1, 129, 641), (0, 2, 898)):
            with self.subTest(batch_idx=batch_idx, position=position):
                values = {"block_table": [[7, 2], [3, 5]], "block_size": 128,
                          "batch_idx": batch_idx, "position": position}
                exec(compile(expression, "published_slot_recipe", "exec"),
                     {"__builtins__": {}, "divmod": divmod}, values)
                self.assertEqual(expected, values["slot"])
        for exception in ("RingCache", "压缩缓存", "Mamba"):
            self.assertIn(exception, section)

    def test_v1_invalid_row_modes_and_version_boundary(self):
        metadata, body = card(FIA)
        self.assertEqual({
            "0": ["high_precision", "disabled"],
            "1": ["high_performance", "disabled"],
            "2": ["high_precision", "enabled"],
            "3": ["high_performance", "enabled"],
        }, table(body, "inner_precise"))
        self.assertIn(API, [s["resource"] for s in metadata["sources"]])
        section = body.split("## v1 6.0 的单 Query 与全遮蔽行边界", 1)[1].split("\n## ", 1)[0]
        for boundary in ("Atlas A2", "Q_S=1", "只允许0或1", "sparse_mode",
                         "pre_tokens", "next_tokens", "不生效", "不替代", "v2"):
            self.assertIn(boundary, section)

    def test_manual_profiling_remains_unknown_for_other_frameworks(self):
        metadata, body = card(PROFILER)
        # A framework-only hard filter would hide the generic manual path again.
        for alternative in metadata.get("scope", {}).get("any_of", []):
            self.assertNotIn("framework", alternative["all_of"])
        self.assertEqual({"a2", "a3"}, set(metadata["platforms"]))
        self.assertIn("## CANN Executor 的内置窗口", body)
        self.assertIn("## 独立于 Executor 的手动注入入口", body)
        for boundary in ("SGLang", "vLLM", "未在这里验证", "不能直接套用", "unknown"):
            self.assertIn(boundary, body)

    def test_precision_runbook_keeps_dense_and_float8_exceptions(self):
        _, body = card("model/inference/runbooks/precision/precision_kvcache_fa_fusion_pitfalls")
        self.assertIn("float8 KV Decode", body)
        self.assertIn("Qwen Dense 的分页 Prefill 和 Decode 都取普通 KV 长度", body)
        self.assertIn("fused_infer_attention_score.md", body)
        self.assertNotIn("Qwen/Qwen3-MoE 的标准 TND 路径两阶段", body)

    def test_moe_quantization_encodings_belong_to_each_interface(self):
        metadata, body = card("model/inference/guides/integration/parallel_groups_and_weight_shards")
        # op-plugin 7.3.0 parameter contracts use different numeric enums.
        expected = {
            "npu_moe_init_routing_v2": (-1, 1),
            "npu_moe_distribute_dispatch_v2": (0, 2),
        }
        self.assertEqual(
            {f"`{name}`": [str(value) for value in modes]
             for name, modes in expected.items()},
            table(body, "MoE 接口"),
        )
        sources = {source["resource"] for source in metadata["sources"]}
        for name, (unquantized, dynamic) in expected.items():
            with self.subTest(api=name):
                api_metadata, api_body = card("model/inference/apis/torch_npu/" + name)
                self.assertIn(api_metadata["sources"][0]["resource"], sources)
                self.assertIn(f"非量化模式为 `quant_mode={unquantized}`", api_body)
                self.assertIn(f"动态量化为 `quant_mode={dynamic}`", api_body)
        _, routing_body = card("model/inference/apis/torch_npu/npu_moe_init_routing_v2")
        self.assertIn("静态量化", routing_body)
        self.assertIn("暂不支持", routing_body)

    def test_precision_runbook_limits_linear_offsets_to_contiguous_slices(self):
        _, body = card("model/inference/runbooks/precision/precision_kvcache_fa_fusion_pitfalls")
        rule = body.split("\n4. ", 1)[1].split("\n5. ", 1)[0]
        for term in ("仅适用于", "按请求固定切片", "连续缓存", "max_seq_len",
                     "分页", "block_table", "不能用",
                     "kv_cache_manager.md#普通分页缓存的物理槽位"):
            self.assertIn(term, rule)


class InferenceSkillMigrationCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = yaml.safe_load((ROOT / "evals/inference_skill_migration_coverage.yaml").read_text())
        cls.cases = yaml.safe_load((ROOT / "evals/inference_skill_migration_cases.yaml").read_text())["cases"]

    def test_each_pr_file_has_a_disposition_and_fixed_blob(self):
        data = self.coverage
        for key in ("base", "head", "technical_revision"):
            self.assertRegex(data[key], r"^[0-9a-f]{40}$")
        files = data["files"]
        self.assertEqual(109, len(files))
        self.assertEqual(len(files), len({f["path"] for f in files}))
        decisions = {d["id"] for d in data["decisions"]}
        used = set()
        for source in files:
            with self.subTest(path=source["path"]):
                self.assertRegex(source["base_blob"], r"^[0-9a-f]{40}$")
                self.assertRegex(source["deleted_sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(source["decisions"])
                self.assertFalse(set(source["decisions"]) - decisions)
                used.update(source["decisions"])
        self.assertEqual(decisions, used)

    def test_accepted_decisions_have_existing_cards_and_positive_cases(self):
        cases = {c["id"]: c for c in self.cases}
        self.assertEqual(len(cases), len(self.cases))
        decisions = self.coverage["decisions"]
        self.assertEqual(len(decisions), len({d["id"] for d in decisions}))
        for decision in decisions:
            with self.subTest(decision=decision["id"]):
                action = decision["disposition"]
                self.assertIn(action, {"migrated", "reuse", "defer", "workflow"})
                if action in {"defer", "workflow"}:
                    self.assertTrue(decision["reason"])
                    self.assertNotIn("target", decision)
                    continue
                metadata, _ = card(decision["target"])
                self.assertEqual("stable", metadata["status"])
                self.assertTrue(decision["retrieval_cases"])
                for case_id in decision["retrieval_cases"]:
                    case = cases[case_id]
                    positive = case.get("expected", []) + [p for group in case.get("expected_any", []) for p in group]
                    self.assertIn(decision["target"], positive)
                    self.assertEqual(5, case["filters"]["k"])

    def test_latest_pr_followup_has_explicit_nontechnical_dispositions(self):
        self.assertRegex(self.coverage["reviewed_head"], r"^[0-9a-f]{40}$")
        followup = self.coverage["followup_files"]
        self.assertEqual(15, len(followup))
        paths = {row["path"] for row in self.coverage["files"]}
        for row in followup:
            with self.subTest(path=row["path"]):
                self.assertFalse(row["path"].startswith(".agents/skills/"))
                self.assertEqual("workflow", row["disposition"])
                self.assertTrue(row["reason"])
                self.assertRegex(row["after_blob"], r"^[0-9a-f]{40}$")
                if row["before_blob"] is not None:
                    self.assertRegex(row["before_blob"], r"^[0-9a-f]{40}$")
                for key in ("deleted_sha256", "added_sha256"):
                    self.assertRegex(row[key], r"^[0-9a-f]{64}$")
                paths.add(row["path"])
        self.assertEqual(self.coverage["reviewed_file_count"], len(paths))
        self.assertEqual(112, len(paths))

    def test_standalone_parallel_branch_does_not_claim_framework_support(self):
        metadata, body = card("model/inference/guides/integration/parallel_groups_and_weight_shards")
        self.assertNotIn("scope", metadata)
        self.assertIn("SGLang/vLLM", body)
        self.assertIn("未在这里验证", body)
        self.assertIn('dist.init_process_group("hccl")', body)

    def test_every_accepted_fact_has_body_content_and_retrieval_evidence(self):
        cases = {case["id"]: case for case in self.cases}
        facts = self.coverage["facts"]
        self.assertEqual(len(facts), len({fact["id"] for fact in facts}))
        accepted = {d["id"] for d in self.coverage["decisions"] if d["disposition"] in {"migrated", "reuse"}}
        self.assertTrue(accepted <= {fact["id"] for fact in facts})
        for fact in facts:
            with self.subTest(fact=fact["id"]):
                metadata, body = card(fact["target"])
                content = body.split("\n## Evidence", 1)[0]
                self.assertEqual("stable", metadata["status"])
                self.assertTrue(fact["required_content"])
                for term in fact["required_content"]:
                    self.assertIn(term, content)
                self.assertTrue(fact["retrieval_cases"])
                for case_id in fact["retrieval_cases"]:
                    case = cases[case_id]
                    positive = case.get("expected", []) + [p for group in case.get("expected_any", []) for p in group]
                    self.assertIn(fact["target"], positive)

    def test_profiler_columns_use_complete_real_names(self):
        _, body = card("model/inference/guides/optimization/kernel_details_field_interpretation")
        self.assertEqual(57, len(self.coverage["profiler_columns"]))
        for column in self.coverage["profiler_columns"]:
            with self.subTest(column=column):
                self.assertIn(column, body.split("\n## Evidence", 1)[0])
        self.assertIn("aic_mte1_ratio", body)
        self.assertIn("aic_mte2_ratio", body)
        self.assertIn("aiv_mte3_ratio", body)
        self.assertEqual(7, len(self.coverage["profiler_task_types"]))
        for task_type in self.coverage["profiler_task_types"]:
            self.assertIn(task_type, body.split("\n## Evidence", 1)[0])

    def test_all_reference_config_values_match_frozen_source_gold(self):
        _, body = card("model/inference/guides/deployment/parallel_reference_config_selection")
        rows = table(body, "YAML")
        keys = ("world_size", "attn_tp_size", "dense_tp_size", "moe_tp_size",
                "embed_tp_size", "lmhead_tp_size", "o_proj_tp_size", "cp_size")
        for gold in self.coverage["configuration_rows"]:
            with self.subTest(config=gold["source"]):
                expected = [str(gold["parallel_config"][key]) if gold["parallel_config"][key] is not None else "—" for key in keys]
                self.assertEqual(expected, rows[gold["source"]])
        self.assertNotIn("不按旧表虚构 pd/prefill.yaml", body)
        self.assertEqual("32", rows["models/kimi_k2_thinking/config/pd/prefill.yaml"][-1])
        self.assertEqual("1", rows["models/kimi_k2_thinking/config/pd/decode.yaml"][-1])

    def test_ge_and_npugraph_combinations_preserve_rejection_and_unknown(self):
        _, body = card("model/inference/optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api")
        rows = table(body, "场景 ID")
        expected = {
            "ge_static_single_and_multi": "forbidden",
            "ge_dynamic_auto_and_explicit": "explicit",
            "ge_local_and_global_cores": "local",
            "npugraph_non_ascendc": "unsupported",
            "npugraph_same_stream_threads": "unsupported",
            "npugraph_static_and_limit_cann_le_8_5": "limit_core_num",
            "npugraph_static_and_limit_newer": "unknown",
        }
        self.assertEqual(expected, {key: values[0] for key, values in rows.items()})

    def test_glm_li_modes_and_scale_cache_are_not_plain_kv_flags(self):
        _, mode_body = card(LI_MODE)
        rows = table(mode_body, "模式路径")
        self.assertEqual("unquant", rows["glm_no_quant_config"][0])
        self.assertEqual("int8", rows["glm_a3_quant_config"][0])
        self.assertEqual("float8", rows["glm_950_float_mm"][0])
        self.assertEqual("int8", rows["v32_int8_cache"][0])
        self.assertIn("FP16", rows["glm_a3_quant_config"][2])
        self.assertIn("FP32", rows["glm_950_float_mm"][2])
        _, body = card("model/inference/guides/integration/lightning_indexer_quantization_scale_cache")
        for key in ("restore_indices", "persistent_valid_indices", "persistent_slot_mapping",
                    "global_slot_mapping", "local_prev_token_num", "local_next_token_num"):
            self.assertIn(key, body)
        self.assertIn("与权重产物无关的独立 YAML", mode_body)

    def test_monitored_barrier_does_not_claim_hccl_backend_support(self):
        _, body = card("model/inference/runbooks/runtime/hccl_timeout_secondary_to_rank_failure_oom")
        self.assertIn("仅支持 GLOO 后端", body)
        self.assertIn("不能在 HCCL 组上照搬", body)

    def test_reused_longcat_rule_scope_includes_both_supported_graph_backends(self):
        metadata, _ = card("model/inference/optimizations/rules/decode_multi_stream_overlap_core_balance")
        self.assertEqual({"ge_graph", "npugraph_ex"}, set(metadata["scope"]["any_of"][0]["all_of"]["execution_mode"]))

    def test_every_deleted_section_has_an_explicit_disposition(self):
        ledger = yaml.safe_load((ROOT / "evals/inference_skill_migration_sections.yaml").read_text())
        self.assertEqual(self.coverage["base"], ledger["base"])
        self.assertEqual(self.coverage["head"], ledger["head"])
        facts = {fact["id"] for fact in self.coverage["facts"]}
        files = {source["path"] for source in self.coverage["files"]}
        ids = []
        for path, sections in ledger["sections"].items():
            self.assertIn(path, files)
            for section in sections:
                with self.subTest(path=path, section=section["heading"]):
                    ids.append(section["id"])
                    self.assertLessEqual(section["lines"][0], section["lines"][1])
                    self.assertRegex(section["removed_sha256"], r"^[0-9a-f]{64}$")
                    self.assertIn(section["disposition"], {"knowledge", "workflow", "navigation"})
                    if section["disposition"] == "knowledge":
                        self.assertTrue(section["facts"])
                        self.assertFalse(set(section["facts"]) - facts)
                    else:
                        self.assertTrue(section["reason"])
        self.assertEqual(set(range(927)), set(ids))
        self.assertEqual(927, len(ids))
        self.assertEqual([], section_fact_errors(ledger, self.coverage))

    def test_fact_sources_are_present_and_belong_to_this_pr(self):
        files = {row["path"] for row in self.coverage["files"]}
        for fact in self.coverage["facts"]:
            with self.subTest(fact=fact["id"]):
                self.assertTrue(fact["source_paths"])
                self.assertFalse(set(fact["source_paths"]) - files)

    def test_wrong_superkernel_topic_mapping_is_rejected(self):
        ledger = yaml.safe_load((ROOT / "evals/inference_skill_migration_sections.yaml").read_text())
        changed = deepcopy(ledger)
        count = 0
        for path, sections in changed["sections"].items():
            if "/model-infer-superkernel/" not in path:
                continue
            for section in sections:
                if section["disposition"] == "knowledge":
                    section["facts"] = ["quant_evidence"]
                    count += 1
        self.assertEqual(72, count)
        self.assertEqual(count, len(section_fact_errors(changed, self.coverage)))

    def test_quantization_runtime_layers_are_not_claimed_as_speedup_evidence(self):
        ledger = yaml.safe_load((ROOT / "evals/inference_skill_migration_sections.yaml").read_text())
        sections = ledger["sections"][".agents/skills/model-infer-quantization/references/quantization-contract.md"]
        row = next(section for section in sections if section["heading"] == "## 6. 四层落点")
        self.assertEqual(["quant_runtime_layers"], row["facts"])

    def test_superkernel_comparison_requires_the_same_backend_and_warmup(self):
        _, body = card(SK_ANALYSIS)
        decisions = {key: value[0] for key, value in table(body, "场景").items()}
        self.assertEqual({
            "same_ge_one_switch": "yes", "eager_vs_ge": "no",
            "compile_in_steady_window": "no", "multiple_changes": "no",
            "scope_marker_only": "no", "static_layer_loop": "needs_graph",
            "dynamic_data_branch": "needs_graph",
        }, decisions)

    def test_li_configuration_is_separate_from_hardware_support(self):
        metadata, body = card(LI_MODE)
        self.assertEqual(["agnostic"], metadata["platforms"])
        self.assertIn("不证明目标设备", body)
        self.assertIn('platform_version == "950" and "float" in mm_quant_mode', body)
        metadata, guide = card("model/inference/guides/integration/lightning_indexer_quantization_scale_cache")
        self.assertEqual(["a3"], metadata["platforms"])
        self.assertIn("li_cache_quantization_mode_contract.md", guide)
        self.assertNotIn("| glm_950_float_mm |", guide)

    def test_every_source_api_has_a_body_and_platform_aware_retrieval_case(self):
        inventory = yaml.safe_load((ROOT / "evals/inference_skill_migration_apis.yaml").read_text())
        rows = inventory["entries"]
        self.assertEqual(144, len(rows))
        self.assertEqual(144, len({row["api"] for row in rows}))
        cases = {case["id"]: case for case in self.cases}
        allowed_exclusions = {"torch_npu." + name for name in (
            "_npu_dropout", "npu_apply_adam", "npu_bert_apply_adam",
            "npu_grid_assign_positive", "npu_sparse_lightning_indexer_grad_kl_loss",
            "npu_softmax_cross_entropy_with_logits", "npu_cross_entropy_loss",
            "npu_yolo_boxes_encode", "npu_bounding_box_encode", "npu_dropout_with_add_softmax",
        )}
        excluded = set()
        for row in rows:
            with self.subTest(api=row["api"]):
                self.assertRegex(row["source_row_sha256"], r"^[0-9a-f]{64}$")
                self.assertIn(inventory["op_plugin_revision"], row["source_doc"])
                if row["disposition"] == "out_of_scope":
                    excluded.add(row["api"])
                    self.assertIn(row["api"], allowed_exclusions)
                    self.assertTrue(row["reason"])
                    self.assertNotIn("target", row)
                    continue
                self.assertEqual("migrated", row["disposition"])
                metadata, body = card(row["target"])
                self.assertEqual("API", metadata["type"])
                self.assertEqual(row["status"], metadata["status"])
                self.assertEqual(row["platforms"], metadata["platforms"])
                self.assertEqual(row["source_doc"], metadata["sources"][0]["resource"])
                self.assertEqual("primary", metadata["sources"][0]["role"])
                content = body.split("\n## Evidence", 1)[0]
                for term in row["required_content"]:
                    self.assertIn(term, content)
                platforms = set()
                for case_id in row["retrieval_cases"]:
                    case = cases[case_id]
                    self.assertIn(row["target"], case["expected"])
                    self.assertEqual(5, case["filters"]["k"])
                    if row["status"] == "draft":
                        self.assertTrue(case["filters"]["include_unlocated"])
                        self.assertEqual("draft", case["filters"]["status"])
                        self.assertNotIn("platform", case["filters"])
                    else:
                        platforms.add(case["filters"]["platform"])
                self.assertEqual(set(row["platforms"]), platforms)
        self.assertEqual(allowed_exclusions, excluded)
        self.assertEqual(134, sum(row["disposition"] == "migrated" for row in rows))

    def test_legacy_product_names_are_not_promoted_to_a3(self):
        for name in ("npu_batch_nms", "npu_fused_attention_score"):
            metadata, body = card("model/inference/apis/torch_npu/" + name)
            self.assertEqual("draft", metadata["status"])
            self.assertEqual([], metadata["platforms"])
            self.assertIn("旧的 Atlas", body)

    def test_api_source_rows_and_every_sentence_have_independent_fact_checks(self):
        inventory = yaml.safe_load((ROOT / "evals/inference_skill_migration_apis.yaml").read_text())
        for row in inventory["entries"]:
            with self.subTest(api=row["api"]):
                original = f"| [{row['source_label']}]({row['source_url']}) | {row['source_summary']} |"
                self.assertEqual(row["source_row_sha256"], hashlib.sha256(original.encode()).hexdigest())
                if row["disposition"] == "out_of_scope":
                    continue
                self.assertEqual(
                    [s for s in row["source_summary"].split("。") if s],
                    [f["source_excerpt"] for f in row["source_facts"]],
                )
                metadata, body = card(row["target"])
                for fact in row["source_facts"]:
                    self.assertTrue(fact["required_content"])
                    self.assertTrue(all(isinstance(t, str) and t for t in fact["required_content"]))
                    if "correction" in fact:
                        self.assertIn(fact["correction_source"], [s["resource"] for s in metadata["sources"]])
                self.assertEqual([], api_source_fact_errors(row, body))

    def test_every_migrated_api_has_a_capability_query_without_its_api_name(self):
        inventory = yaml.safe_load((ROOT / "evals/inference_skill_migration_apis.yaml").read_text())
        cases = {case["id"]: case for case in self.cases}
        for row in inventory["entries"]:
            if row["disposition"] != "migrated":
                continue
            with self.subTest(api=row["api"]):
                self.assertTrue(row["capability_cases"])
                for case_id in row["capability_cases"]:
                    case = cases[case_id]
                    self.assertNotIn(row["api"], case["query"])
                    self.assertNotIn(row["api"].rsplit(".", 1)[-1], case["query"])
                    self.assertIn(row["target"], case["expected"])
                    self.assertEqual("text", case["filters"]["match"])
                    self.assertEqual("apis", case["filters"]["type"])
                    self.assertEqual(5, case["filters"]["k"])
                    if row["status"] == "draft":
                        self.assertTrue(case["filters"]["include_unlocated"])
                        self.assertEqual("draft", case["filters"]["status"])
                        self.assertNotIn("platform", case["filters"])
                    else:
                        self.assertIn(case["filters"]["platform"], row["platforms"])

    def test_transpose_batchmatmul_rejects_non_three_dimensional_inputs(self):
        _, body = card("model/inference/apis/torch_npu/npu_transpose_batchmatmul")
        self.assertEqual({"2": ["no"], "3": ["yes"], "4": ["no"]}, table(body, "输入维数"))
        for term in ("perm_x1 对应 input", "perm_x2 对应 weight", "perm_y 对应输出"):
            self.assertIn(term, body)

    def test_mm_reduce_scatter_keeps_both_quantization_axes(self):
        _, body = card("model/inference/apis/torch_npu/npu_mm_reduce_scatter_base")
        self.assertEqual({
            "x1_scale": ["pertoken", "[m,1]", "float32"],
            "x2_scale": ["perchannel", "[1,n]", "float32/int64"],
        }, table(body, "量化参数"))
        self.assertIn("npu_trans_quant_param", body)

    def test_source_function_names_and_review_queries_remain_retrievable(self):
        for name, alias in (("npu_lstm", "DynamicRNN"), ("npu_gru", "DynamicGRUV2"),
                            ("npu_recurrent_gated_delta_rule", "RGDR")):
            metadata, body = card("model/inference/apis/torch_npu/" + name)
            self.assertIn(alias, metadata["aliases"])
            self.assertIn(alias, body)
        cases = {case["id"]: case for case in self.cases}
        for key, query, match in (
            ("dynamicrnn", "DynamicRNN", "literal"),
            ("dynamicgruv2", "DynamicGRUV2", "literal"),
            ("rgdr", "RGDR", "literal"),
            ("quant_reduce_scatter", "reduce_scatter pertoken量化", "text"),
            ("transpose_rank3", "批量矩阵乘 三维转置", "text"),
        ):
            case = cases["infer_skill_r4_" + key]
            self.assertEqual(query, case["query"])
            self.assertEqual(match, case["filters"]["match"])
            self.assertEqual("a3", case["filters"]["platform"])
            self.assertEqual("apis", case["filters"]["type"])
            self.assertEqual(5, case["filters"]["k"])

    def test_source_fact_checks_reject_the_reviewed_semantic_losses(self):
        inventory = yaml.safe_load((ROOT / "evals/inference_skill_migration_apis.yaml").read_text())
        rows = {row["api"]: row for row in inventory["entries"]}
        for name, removed in (
            ("npu_transpose_batchmatmul", "仅支持三维 Tensor"),
            ("npu_mm_reduce_scatter_base", "支持 perchannel"),
            ("npu_lstm", "DynamicRNN"),
            ("npu_gru", "DynamicGRUV2"),
            ("npu_recurrent_gated_delta_rule", "RGDR"),
        ):
            row = rows["torch_npu." + name]
            _, body = card(row["target"])
            self.assertIn(removed, body)
            self.assertEqual([], api_source_fact_errors(row, body))
            self.assertTrue(api_source_fact_errors(row, body.replace(removed, "")))

    def test_sign_bit_encoding_keeps_mapping_and_byte_order(self):
        _, packed = card("model/inference/apis/torch_npu/npu_sign_bits_pack")
        _, unpacked = card("model/inference/apis/torch_npu/npu_sign_bits_unpack")
        self.assertEqual({"-1.0": ["0"], "1.0": ["1"]}, table(packed, "输入符号"))
        self.assertEqual({"0": ["-1.0"], "1": ["1.0"]}, table(unpacked, "编码位"))
        for body in (packed, unpacked):
            self.assertIn("小端序", body)
            self.assertIn("uint8", body)
            self.assertIn("8个", body)

    def test_mixed_templates_keep_their_technical_obligations(self):
        ledger = yaml.safe_load((ROOT / "evals/inference_skill_migration_sections.yaml").read_text())
        obligations = (
            ("model-infer-optimize/templates/optimization_report_template.md", "<preamble>", "runtime_mc2"),
            ("model-infer-sota-approach/references/scenario-setup.md", "## 3. 跑通基线并采样输出", "profile_compile"),
        )
        for path, heading, fact in obligations:
            with self.subTest(path=path):
                sections = ledger["sections"][".agents/skills/" + path]
                section = next(row for row in sections if row["heading"] == heading)
                self.assertEqual("knowledge", section["disposition"])
                self.assertIn(fact, section["facts"])

    def test_local_batch_algebra_does_not_invert_dp_effect(self):
        _, body = card("model/inference/guides/deployment/parallel_reference_config_selection")
        expressions = dict(re.findall(r"(attn_dp_size|batch_size_per_dp_rank)=([a-z_ /]+)", body))
        for tp, expected_dp, expected_local in ((1, 8, 16), (2, 4, 32)):
            values = {"world_size": 8, "attn_tp_size": tp, "batch_size": 128}
            values["attn_dp_size"] = eval(expressions["attn_dp_size"], {"__builtins__": {}}, values)
            local = eval(expressions["batch_size_per_dp_rank"], {"__builtins__": {}}, values)
            self.assertEqual(expected_dp, values["attn_dp_size"])
            self.assertEqual(expected_local, local)

    def test_mamba_alternative_has_the_actual_workaround_and_version_boundary(self):
        _, body = card("model/inference/runbooks/precision/precision_mamba_gdn_linear_attention")
        for term in ("max-mamba-cache-size", "512", "非根治", "CANN 9.1.0"):
            self.assertIn(term, body)

    def test_frozen_review_questions_and_scope_counterexamples_remain(self):
        cases = {c["id"]: c for c in self.cases}
        for suffix, text in {
            "review_postload": "GroupedMatmul Dim 1 mismatch",
            "review_parallel_boundary": "不同 TP 模块 交换激活",
            "review_benefit": "W8A8 量化 显存不降",
            "review_masked_row": "inner_precise 全遮蔽行",
            "review_bsh_single": "BSH Q_S=1 sparse_mode pre_tokens",
        }.items():
            self.assertEqual(text, cases["infer_skill_" + suffix]["query"])
        for framework in ("sglang", "vllm"):
            case = cases["infer_skill_repair_profiling_" + framework]
            self.assertEqual("unknown", case["expected_scope_states"][PROFILER])
            self.assertIn(PROFILER, case["expected"])


if __name__ == "__main__":
    unittest.main()
