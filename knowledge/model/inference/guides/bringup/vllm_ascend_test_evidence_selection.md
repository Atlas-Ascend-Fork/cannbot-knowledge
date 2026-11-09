---
type: Guide
title: vLLM Ascend 测试证据选择：CPU、NPU、精准CI与文档用例
description: 按固定上游测试指南区分mock、真实设备、E2E和性能证据，核对精准选择与runner路由、缩层随机权重、文档固定代码块及实际触发方式。 补充 /e2e 的派发鉴权、双版本、skip/accuracy 路由及贡献交付边界。 补充固定3164测试差异的Attention、缓存、混合状态、量化加载、采样和失败回退选择。
tags:
- task.testing
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/testing.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/testing.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/e2e_ci_test.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/index.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/e2e_ci_test.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/index.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_e2e_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/slash_command_dispatch.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/test_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/runner_label.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/select_tests.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/ci_log_summary.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/coverage_taxonomy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/generate_coverage_html.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/upstream_test_plugin.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/coverage.html
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/doctests/001-quickstart-test.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/doctests/002-installation-test.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/doctests/scripts/common.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/doctests/scripts/run_doctests.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/coveragerc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/TEST_README.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/misc/model_dataset_list.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/assemble_coverage.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/collect_merged_new_tests.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/conftest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/coverage.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/detect_po_changes.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/estimated_times.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/main2main_tests.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/merge_extra_recommended_tests.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/po_translate.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/resolve_daily_tests.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/resolve_latest_release_branch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/run_selected_tests.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/run_suite.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/test_selector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/update_estimated_times.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/upstream_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.pre-commit-config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/format.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/mypy.ini
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/actionlint.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_boolean_context_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_forbidden_imports.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_logger.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_long_functions.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_python_src_init.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_repo.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/check_symbolic_meta.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/mypy.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/png-lint.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/shellcheck.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/features/context_parallel/DeepSeek-V4.1-Flash-W8A8-DSpark-PCP.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/features/kv_pool/DS-V4-Flash-W8A8-A3-Mooncake.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/features/pp/GLM-5.3-W8A8C8-A3-200k-PP-PD.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/models/configs/GLM/GLM-5.2-W8A8C8-A3_128k-static-super-kernels.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/models/configs/GLM/GLM-5.3-Flash-W8A8-130k-PD.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/models/configs/Kimi/Kimi-K3-MRV2-A3.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/cases/models/configs/MiniMax/MiniMax-M3-w8a8-PP-prefix-PD.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/common/single_node/kv_pool_runtime.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/coverage.html
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/coverage_taxonomy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/doctests/002-installation-test.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_sfa_cache_store.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_sfa_dcp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_causal_conv1d_v310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_fused_scatter_copy_sparse_flash_attention.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_grouped_matmul_situ_quant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_hc_pre.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_kv_quant_sparse_flash_attention_vllm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_moe_gating_top_k.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_moe_gating_top_k_hash.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_quant_lightning_indexer_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_recurrent_gated_delta_rule_v310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_scatter_nd_update_sk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_sparse_flash_mla.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_swiglu_group_quant_mxfp_tail.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_triton_ple.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/test_uva_view.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_apply_grammar_bitmask_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_bincount.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_categorical_sample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping_fused.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_copy_and_expand_dflash_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_copy_conv_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_dflash_candidate_sampler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fill_logprob_token_ids_kernel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_gdn_prepare.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_cann_keypool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_int8_kpool_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_state_gather_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_tail_slot_mapping_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kda_recoverssm_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kda_state_copy_integration.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kda_state_copy_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kv_block_zeroer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_num_nans.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_postprocess_mamba.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_postprocess_temporal_copy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_precopy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_dflash_inputs.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_indexer_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_inputs_padded.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_qfa_c8_paged_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_quantize_indexer_query.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_qwen4_exp_qsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rejection_sample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rejection_sample_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_resample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_sampling_mask.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_sfa_dcp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_swiglu_quant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/nightly/single_node/ops/test_minimax_qknorm_rope_cache_performance.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/_310p/test_moe_model_310p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/context_parallel/test_accuracy_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/context_parallel/test_deepseek_v4.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/model_runner_v2/test_deepseek_v4.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/model_runner_v2/test_kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/model_runner_v2/test_spec_decode_data_parallel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/model_runner_v2/test_spec_pp_accuracy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/spec_decode/test_dspark_deepseekv4.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/test_data_parallel_tp2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/test_deepseek_v4.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/test_glm5_3_flash.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/test_kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/test_sparse_hccl_checkpoint.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/lora/test_lora_with_spec_decode.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/lora/test_qwen3_reranker_lora.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/lora/test_qwenvl_lora.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/model_runner_v2/test_deepseek_v2_lite_w8a8_basic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_0_6B_basic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/model_runner_v2/test_uva_prefix.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/pooling/test_classification.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/pooling/test_embedding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/pooling/test_scoring.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/rlhf/state_transitions/test_npu_ipc_weight_transfer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/rlhf/state_transitions/test_sleep_wake.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/spec_decode/test_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/spec_decode/test_eagle.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/spec_decode/test_extract_hidden_states.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_cpu_weight_offload.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_flash_attn_precision.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_gdn_block_packed_states.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_glm5next_pooled_cache_write.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_guided_decoding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_gumbel_sampling.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_minicpm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_minimax_qknorm_rope_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_multistream_overlap_shared_expert.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_qwen3_8b_w8a8.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_simple_cpu_offload.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_swiglu_mx_quant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_vlm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/one_card/test_xlite.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/two_card/model_runner_v2/test_qwen3_8_lilicorr.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/two_card/test_hixl_eplb_registration.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/manual/test_gbsa_qsa_compile_graph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/manual/test_qsa_lightning_indexer_a5.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/manual/test_qwen4_exp_hc_triton_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/_310p/fused_moe/test_shared_experts_overlap_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/_310p/fused_moe/test_shared_fused_moe_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/_310p/test_mamba_align_fallback_310p_source.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/_310p/test_multistream_logits_initialization_310p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_cache_store.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_common_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_dsa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_dsa_metadata_builders.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_dsa_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_dsa_v41_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_dsv4_block_geometry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_flash_attn.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_flashmla_prolog_v3_cpu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_mla_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_mla_layerwise_load_cpu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_mla_prolog_v3_route.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_mla_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_o_proj_forward_lifecycle.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_sfa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_sfa_cp_precision.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_sfa_dcp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_sfa_nope_forward.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_sfa_nope_metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/attention/test_sfa_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/compilation/test_fusion_pattern_registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/compilation/test_muls_add_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/conftest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/core/test_batch_job_aware_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/core/test_kv_cache_interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/core/test_qsa_kv_cache_grouping.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/core/test_recompute_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/core/test_swa_replay_downgrade.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/device/test_hardware_profile.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_ascend_store_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_glm53_store.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_layerwise_cache_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_layerwise_keys.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_mooncake_hybrid.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_mooncake_layerwise.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_mooncake_pipeline.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_pool_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_qsa_basic_pooling.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_reuse_publication_fence.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_reuse_snapshot_blocks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/ascend_store/test_reuse_snapshot_identity.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/eplb/test_hixl_communicator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/eplb/test_policy_load_stats.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/eplb/test_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/kv_transfer/sparse_kv_offload/test_sparse_kv_offload_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/kv_transfer/test_mooncake_transfer_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/weight_transfer/test_sparse_hccl_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/eplb/adaptor/test_vllm_adaptor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/mooncake_v2/helpers.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/mooncake_v2/test_base_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/mooncake_v2/test_base_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/mooncake_v2/test_pull_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/mooncake_v2/test_pull_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/test_pool_worker_pp_layer_count.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/test_pool_worker_pp_object_bounds.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_offload/test_preempt_offload_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/kv_transfer/test_layerwise_dcp_sharding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/test_glm_mla_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/helpers.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_jit_warmup_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_jit_warmup_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_jit_warmup_penalties.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_jit_warmup_rejection.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_jit_warmup_rms.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_kernel_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_executor/warmup/test_nz_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/model_loader/rfork/test_identity_validation.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/minimax_m3/test_msa_m3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/gbsa_reference.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_fia_dispatch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_gbsa_adapter.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_gbsa_preparation.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_mtp_quant_mapping.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_ple_internal_format.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_qsa_layerwise_hooks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_qsa_lightning_dynamic_page.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/qwen4_exp/test_qsa_upstream_abi.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_decoder_replay.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_decoder_replay_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_operator_contracts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_preprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v41_replay_distributed.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v4_vision_preprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_deepseek_v4_weight_loader_reload.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_engram.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_cache_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_int8_kpool.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_kda_contracts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_kda_dispatch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_kda_pcp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_kpool_model_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_recoverssm_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_recoverssm_metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_glm5next_vision_nz.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_kimi_k3_adapter.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_qwen4_exp_cache_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_qwen4_exp_soc_gating.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_qwen4_exp_source_regression.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/models/test_qwen4_exp_spec_cpu_length_sync.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_allgather_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_cann_keypool_adapters.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_eplb_v2_recording.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_fused_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_gdn_layerwise_kv.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_gdn_mixed_batch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_layernorm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_linear.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_mla.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_qwen4_exp_qsa_cache_store.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_register_custom_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_rotary_embedding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_token_dispatcher.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/ops/test_triton_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/platform/test_patch_balance_schedule.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/platform/test_patch_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/platform/test_prefix_cache_cp_patches.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_bind_kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_deepseek_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_dspark_pp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_eagle3_pp_aux.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_mamba_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_mamba_utils_uniform_groups.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_uva_prefix.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_uva_zeros.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/patch/worker/test_patch_v2_gumbel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/configs/test_modelslim_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/conftest_quantization.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/methods/test_moe_logical_experts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/methods/w4a8/test_w4a8.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/methods/w4a8/test_w4a8_mxfp4.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/methods/w8a8/test_swiglu_mx_quant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/quantization/test_weight_switch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/spec_decode/test_dflash2_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/spec_decode/test_dflash2_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/spec_decode/test_eagle_aclgraph_source_regression.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/spec_decode/test_eagle_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/spec_decode/test_mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/spec_decode/test_speculators_vwn_eagle3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/test_ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/test_dependency_metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/test_mrv2_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/test_platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/test_sleep_mode_tensor_ownership.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/test_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_adaptive_verification.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_attn_utils_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_dcp_speculator_metadata_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_encoder_acl_graph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_glm5next_pooled_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_mamba_kv_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_model_runner_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_model_runner_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_model_runner_v2_kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_model_runner_v2_mamba.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_pcp_manager_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_replay_slot_padding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_worker_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/test_worker_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/v2/test_block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/v2/test_entropy_verify.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/v2/test_eplb_controller.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/v2/test_kv_block_zeroer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/worker/v2/test_speculator.py
  role: implementation
created_at: '2026-10-30T08:05:37Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T02:53:33Z'
---


# vLLM Ascend 测试证据选择：CPU、NPU、精准CI与文档用例

## Agent先按版本与问题选择证据入口

| 当前任务 | 阅读位置与适用源版本 | 需要产出的判断 |
| --- | --- | --- |
| 新模型/算子改动先选验证层 | 下节“先选证据层次，再选命令”，固定ceac | 区分CPU mock、NPU E2E、精度与性能；列出实际收集和skip，不能只给命令 |
| 文档说UT走A2，实际matrix却走CPU | “实际路由优先级与文档差异”，固定ceac实现 | 优先按test_config和selector解释当前路由，旧文档概述不能覆盖实现 |
| `/e2e`指定文件/nodeid、切换runner | “E2E评论路径”及“runner override与估时分桶”，固定ceac | 分开鉴权、路径选择、skip、runner分配和最终执行结果 |
| 精准CI未选中新改分支 | “精准推荐的实际数据职责与覆盖补录”，固定ceac | 历史coverage是否覆盖新行、回退选择是否生效，不以目录存在证明命中 |
| 使用3164或更新代码回归 | “固定3164的增量回归选择” | 先核迁移/删除/skip，再找新用例；不要复制ceac旧测试路径后称其已通过 |

本卡的源规则、源码内测试入口、实际运行证据分别陈述。某文件出现比较或mask相关语法，不代表它实际断言了数值精度或掩码正确性；模型HTTP用例与底层算子正确性应选择各自的断言入口。


## 适用范围与产物

本卡蒸馏Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的testing.md及中文testing.po。97条有效译文中96条msgid匹配，1条仅主线工作流表的附加触发器展示有变。主指南跨CPU/多类NPU和测试入口，没有证明每条测试都适用所有硬件/模型；保持draft/未定位平台。

适配Agent交付按改动范围保存测试选择理由、实际收集的用例、有效配置、执行/失败/skip和原始结果路径。下列是固定上游规则的知识，不自动对当前知识仓或任何其他项目创建提交、标签、CI或发布动作。

## 先选证据层次，再选命令

| 改动/问题 | 指南期待的证据 | 仍不能由此证明 |
|---|---|---|
| 新行为或边界 | 正常、失败、空/单项、长度/溢出等UT | mock的设备行为真实正确 |
| bug修复 | 能复现原失败且修复后通过的回归 | 未覆盖的其他模型/shape/并行 |
| 集成行为 | 受影响模型、配置、分布式路径E2E | 任意拓扑/功能组合均支持 |
| NPU性能路径 | 同硬件/环境/负载的基线与改动；吞吐/时延与受影响内存/碎片/同步 | CPU耗时或静态推理直接推出NPU收益 |
| 文档/元数据 | 结构/链接/配置解析等定向检查；影响runtime时再做对应运行检查 | 链接通过就代表文档全部可执行 |

本地不要求每次无差别全套重跑；共享行为、失败或审查证据需要扩大覆盖时再加。NPU特有行为在上游合并前要求真实设备验证，本地缺资源时可先准备已有检查及清楚的待验项。报告区分inspection/CPU/NPU/E2E，不为通过改阈值或把skip写成PASS。

## CPU环境与真实设备测试分开

指南本地CPU流程用CANN容器、VLLM_TARGET_DEVICE=empty和SOC_VERSION等安装，UT需mock设备函数并设置TORCH_DEVICE_BACKEND_AUTOLOAD=0等目标环境。这样的安装与导入不初始化目标NPU来证明数值或通信；本卡未执行其中apt/pip、卸载Triton或全局镜像配置。

主指南同时讨论CPU UT与tests/ut/<module>/a2等设备目录，不能只凭名称断言实际设备运行。所读当前selector将UT放CPU，是否mock/依赖设备仍按fixture和断言核验；这不构成真实NPU质量证据。普通UT路径与source模块对齐，以test_前缀，通过pytest运行unittest风格定义。

PR one_card/two_card与nightly singlecard_ops/multicard_ops_a3是不同集合。单节点nightly模型用CONFIG_BASE_PATH、CONFIG_YAML_PATH和common/single_node/test_single_node.py入口；多节点另按对应指南。存在目录或pytest退出不单独证明预期case全部被收集、未跳过、完成业务判据或通过真实精度/性能验收，继续保留结果合同。

## 精准选择、路由与上游标签的职责

固定指南描述test_selector.py基于历史coverage建立测试到source行映射，并按行→函数→文件回退推荐受影响用例；select_tests.py按路径约定路由和estimated_times负载分配，输出CI matrix。推荐集合与runner分配是两个阶段，新测试位于目录不意味着历史coverage已覆盖新分支。

主testing.md给普通UT→CPU、UT a2目录→A2及PR多类卡数→A3、_310p→310P的概述；它不是最终runner事实。已补读test_config.yaml和selector所列路由片段：one_card通则为A2，精确文件/accuracy规则可覆盖，详见后文。估时仍来自estimated_times.yaml但该文件完整知识尚未闭合；预览路由不证明实际收集、设备/依赖就绪或断言通过。本批没有运行selector、完整CI或NPU。

上游ready-precise为推荐子集，ready-all为全套，main2main为verified vLLM main和匹配release tag两路全套；它们是该仓CI标签语义，不是任意仓同名标签的保证。实际PR head、source/workflow修订、触发上下文与最终job产物一起留证，不从标签存在推导执行成功。

## 缩层与随机权重不代替真实模型质量

指南示例改num_hidden_layers=2并生成随机权重以降低CI资源。这可用于明确标注的构造/执行探针，不能宣称完整层数、原checkpoint加载、量化scale或任务准确率已验收。保留模型config/processor/tokenizer与完整模型的独立真实权重结果；跨模型不要直接复制DeepseekV3ForCausalLM生成脚本。

## 文档用例与定时工作流的边界

Doctest只抽取固定标记的Quick Start/Installation代码块，不是所有文档代码块。固定指南Quick Start包括A2和310P、按顺序离线/在线；Installation为A2的pip/uv/source后离线验证，两者覆盖Ubuntu/openEuler。入口不创建容器，安装会修改包，需要匹配环境与预备模型cache，worker启用HF离线；离线标志不会下载缺失权重。

Doc Test依main/releases-v分支相关改动选择用例，也可由外部automation调workflow_dispatch；空quickstart_devices或installation_methods输入跳过该类型。每个选中case的两个OS需要分别看结果，不把手动输入或workflow文件名当完整覆盖。

schedule_只代表周期CI族，部分工作流由外部automation通过workflow_dispatch触发，没有cron不自动视为缺陷。旧PO把schedule_main2main.yaml附加触发器写workflow_dispatch，当前表在“由外部workflow_dispatch调度”分组中用“-”，不能据这项展示差异说触发被删除。名称/表格属于固定版本说明，其他修订要看实际on配置；本批未读取/触发所有workflow。

Sphinx linkcheck产物output.txt/output.json是外部链接检查结果，不是NPU执行、所有代码正确或中文全站已构建的证明。Csrc缓存改动先看cache-engine/concurrency/snapshot-key测试与inner HIT/MISS/BYPASS，外层restore成功不证明编译复用，见[构建缓存指南](vllm_ascend_incremental_build_cache.md)。

本次仅静态读取指南和中文，不运行上游pytest/安装/模型/编译、链接检查、CI或NPU服务。按[精度验收](vllm_ascend_accuracy_evaluation_contract.md)、[性能基准](../optimization/vllm_ascend_benchmark_workflow.md)补任务层证据，再明确实际通过的硬件/模型/配置。


## E2E 评论路径与实际工作流

e2e_ci_test.po 的48条及contribution/index.po的28条均匹配当前英文，共76条。匹配只关闭译文源字符串对应，不消除文档与实现差异。本次补读贡献入口、E2E指南、两个工作流、完整路由元数据及select_tests.py所列片段；未运行选择器、测试、安装或任何评论/提交动作。

上游/e2e用于指定PR E2E文件/节点集合，支持空格分多个相对路径和pytest ::nodeid，不等于ready-all全套。实际链路中slash_command_dispatch.yml（Slash Command Dispatch）接收created issue_comment，对User类型及PR上下文处理e2e，再repository_dispatch(e2e-command)到pr_e2e_command.yml；前者permission:none是派发层配置，后者仍单独鉴权，不能解释为任何评论者可执行测试。

执行层允许PR作者，或GitHub API返回role_name恰好为triage/write/maintain/admin；当前指南只概述write/admin，不能漏掉实际枚举或把自定义角色名自动等同这些值。指南说synchronize会复用评论，但这两个已读工作流只有issue_comment created和repository_dispatch，完整自动重跑链未闭合；不保证只推提交就会触发，更不把该描述当本次推送授权。

执行层还要求非空参数及tests/e2e/pull_request/<subdir>/前缀；这比“任意仓库相对pytest路径”窄。前缀通过不证明文件/nodeid有效，selector会核文件/目录和映射，最终pytest收集、skip与业务断言仍独立。UT不能靠/e2e任意传入，即使通用selector的其他模式处理UT。

所读当前selector明确把所有UT放cpu-0，cpu-ut别名映射tests/ut；--skip-cpu-ut对各选择模式移除UT。不存在的目录在_scan_ut_test_dir中仍可作为目标交给后续阶段，不等于已收集成功。主指南的UT a2目录概述不能覆盖这条实际CPU选路；CPU mock检查不因此变成真实设备测试。

工作流checkout不可变PR head，跨cache/test任务携带head/base SHA，读验证main commit和release tag并校验格式。指定子集也在这两个vLLM目标上运行，不能以为只有main2main才有双目标；两者区别仍是子集/全套。ensure-csrc-cache成功不等于实际算子HIT或测试通过，见[构建缓存](vllm_ascend_incremental_build_cache.md)。最终Bot通知把selected job的success或skipped都记作completed，必须看实际测试任务、收集量、skip、原始结果和业务判据，不能只看评论。

## 实际路由优先级与文档差异

当前test_config.yaml按正则字符串长度降序匹配，先取最具体规则；::nodeid去掉后用于路径路由，_310p检查文件名，不是任意上级目录或节点名包含即可。没有匹配返回None并跳过，不是任意未知路径默认单卡。

| 路径条件 | 逻辑分区 | 需要保留的条件 |
| --- | --- | --- |
| one_card/test_kv_pool_accuracy.py | a3-2 | TP1用例仍可调度到两卡A3 runner，目录/TP不等于runner卡数。 |
| one_card/test_flash_attn_precision.py | a5-4 | 更具体950/A5规则覆盖one_card通则。 |
| 其他匹配one_card | a2-1；文件名_310p时310p-1 | A2 B1/B3混池，不能按旧概述一律A3。 |
| 匹配two_card | a3-2；文件名_310p时310p-2 | A3默认是generic mixed pool，不从旧800t标签推实际SKU。 |
| 匹配four_card | a3-4；文件名_310p时310p-4 | 实际SKU仍看accuracy重映射和job。 |

现存a3-800t标签不代表当前这些路径默认选它；旧E2E表的800t-2/4与实际partition不同。generic A3是560T/752T混池；全套或过滤后选中任一accuracy_tests文件时，将generic A3分区改到800i的560T专用label，分组数保持。节点名、标签字符和产品能力都不能替代实际分配设备记录。

partition.count是负载分组数量：a2-1为7组、a3-2/a3-4各5、310p-1为2，其余当前bucket为1；runner_label.json的npu_num才是对应runner设备数。两者相乘也不是某次任务实际占用，先看最终matrix。元数据目前19个runner记录、8个分区；CI image_tag为该快照构建环境，不与release矩阵/main模板自动合并成通用安装栈。

curated a5指定test_data_parallel_tp2、[MLA FP8 decode布局测试](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_mla_fp8_decode_layout_a5.py)及test_flash_attn_precision，kvpp指定two_card/test_kvpp；不是发现任意新模型就自动进950或KVPP套件。skip_tests在所有选择模式后移除整文件及其nodeid，当前8个文件覆盖KVPP+PP、graph_mode、310P classification、UVA、Qwen性能、Llama LoRA、capture/replay及MTP Step3p5。来源原因是该快照的排除理由，不泛化为所有该功能都不支持。

accuracy_tests有23个文件，其中3个同时在skip_tests；被过滤的文件不再单独构成accuracy重映射触发。显式case被文件级跳过、重复file/nodeid归并、未知路由或不存在路径，都可能改变实际集合。准确测试标签不是测试已通过，也不能从其名称推完整模型/硬件/图/并行覆盖。下节补齐runner override与估时分桶的静态机制；执行汇总及真实CI结果仍须独立核验。

## runner override与估时分桶：配置不等于实际耗时

2026-11-04补读固定ceac的[select_tests.py:504–653](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/select_tests.py#L504-L653)，覆盖`_apply_runner_label_override`、`_lookup_estimated_time`、`_partition_tests`、`_build_test_group`与`_resolve_to_runners`。这是路由与工作量分配代码阅读，不是一次CI执行记录。

`--runner-label-override`接受runners中存在的精确label；未知label或CPU label直接报错。已有CPU组保留原partition；其他组汇入目标NPU类型与卡数对应的临时partition，配置`count=1`。例如原有两个NPU分区各有多个桶，override后不是保留最大桶数，而是合并成一个目标runner组。它也不会自动把测试改造成适配该硬件的用例；设备能力仍需单独确认。

正常分桶先取测试文件路径估时，剥掉`::nodeid`；估时表缺项默认600秒。因此同文件两个nodeid各按整文件估时计入，不是各自精确测时。`_partition_tests`按估时从大到小处理，估时相同保持输入顺序，每次放入当前总估时最小的桶，并列时选编号最小的桶。

例如输入估时为900、600、600秒，分两桶时依次得到`[900]`和`[600,600]`。这是贪心近似，不保证真实运行最优，也不表示慢测试失败。实际resolver先对测试名排序再分桶，空桶不输出；`partition`仍采用原配置的`i-psize`标识，不因省略空桶改写分母。输出还携带runner的image_tag和csrc_cache_target（若配置）。排查“任务数量变少/负载不均”时同时检查override、文件级估时、去重/skip及最终matrix，不从一个分桶号推导执行覆盖。

## 贡献入口的环境与交付规则

贡献入口允许Linux/Windows/macOS做lint及基础开发，不表示torch_npu或NPU构建可跨这些系统。其本地CPU CI例读verified commit，使用VLLM_TARGET_DEVICE=empty；format.sh ci、pip或元数据通过不代替NPU质量/通信测试。非Linux示例按过滤requirements行安装也不是完整传递依赖解析证明。本批不执行其安装、格式化、克隆或shell示例。

本地原生缓存为忽略的csrc/build_cache，VLLM_ASCEND_BUILD_CACHE_DIR需绝对路径；与远程OBS快照不同。禁用custom kernel编译不验证该缓存，修改生成输入/命令/工具链要核缓存身份；清目录的冷构建说明不作为默认清理动作。

上游贡献规则要求DCO Signed-off-by，git commit -s只是生成该header的方式，不作本次创建提交或身份签署授权。PR分类为Attention、Communicator、ModelRunner、Platform、Worker、Core、Kernel、BugFix、Doc、Test、CI、Misc，跨分类保留相关前缀，不能用分类替代测试范围。

用户可感知的新模型/硬件/算子、功能/API/参数/默认行为、依赖/工具链、性能和重要bugfix应随同PR放release_notes/fragments/<PR number>.yaml。纯内部重构/测试/CI/工具、文档小修一般不要求，但完整新场景指南是文档例外；名为refactor但修复用户crash的PR仍按可感知行为判断，不能只看标题或改动量。

已读release_notes/README给一PR一YAML、多entries；确需第二文件用<PR>-<slug>。pr需与文件名匹配，entries非空，每项category/text必填；category为feature、hardware、performance、dependency、breaking、config、documentation、bugfix、other之一，text用用户视角一两句英文且不另加PR链接。highlight只是Highlights候选；model/hardware为矩阵元数据，不证明硬件测试通过。破坏现有用法用breaking，新增能力用feature，release manager可合并/改写原材料。

该规则由review落实，来源说明没有fragment CI gate，不从CI绿色推断已符合。归档到release_notes/archive/<version>，不删除历史原材料；文档所列聚合脚本默认fragments、其相邻archive目录和vllm-project/vllm-ascend仓库。忘记归档的审计提醒不是数据已自动清理。聚合器与TEMPLATE.yaml实现仍未闭合，本次没有调用--archive或生成release。这些是来源项目规则，不自动要求本知识仓提交/发布，也不扩大当前会话授权。

## CI截图只作结果入口索引

固定ci_log_summary截图展示Summary中的mode、失败文件/用例数、distinct issues、code bug与environment flakes分组，并列出具体测试路径及traceback。它帮助定位原始run的材料，不是本次复现、当前模型支持矩阵或跨版本根因证明。

截图所显示的allocator异常仍需对应代码/环境、原始日志和实际失败退出核对；摘要归类、左侧job图标或“环境抖动为0”都不能代替真实收集/skip、设备、精度与性能证据。本次只阅读图片，没有执行该CI。


## 上游适配Skill的两阶段证据与权限边界

上游.agents/README将dummy快速路径与真实权重阶段分开，两个阶段都要求/v1/models及至少一条chat请求，而不是只看进程启动。真实阶段另核FP8/量化、KV分片和稳定性；dummy不能替代真实checkpoint加载或质量结果。它给出的工作目录、端口、依赖固定和单提交交付是该上游Skill的流程约束，不自动授权当前Agent安装依赖、提交、发Issue或执行发布。本次没有调用该Skill或运行模型。


## Coverage marker、静态报告与真实运行是三层

e2e_coverage的固定taxonomy要求arch、feature、parallel、deploy、hardware、quantization、graph_mode七个key都存在，允许不适用维度为空；unknown key/value返回warning，是否硬失败由调用方决定。文档把多值维度限定为feature/parallel，但当前validate两个分支均调用split_multi，因此其他维度也按逗号拆token；不能把说明文字代替实际校验控制流。INVALID_COMBOS当前只有注释例子、实表为空，未来规则只影响report零覆盖组合枚举，不是运行时硬件支持证明。

HTML生成器仅AST读取test_函数上的字面量pytest.mark.e2e_model/e2e_coverage，动态表达式不被完整推导；SyntaxError文件可返回空记录。卡数由one_card/two_card/four_card/eight_card路径推断，其他路径默认1，这不是实际runner/NPU分配。未标记、marker合法、组合被列出、测试已收集和设备实际通过分别留证，不能把静态覆盖图当质量结果。仓内coverage.html也是这种静态报表快照，生成时间/颜色/列表不代表当前代码已运行。

upstream_test_plugin在pytest_configure中调用全局及普通adapt_patch，并桥接routed-experts capturer的get_forward_context到Ascend补丁。插件存在意味着收集/执行可改变进程全局导入与forward-context行为，不是Agent只读解析时应导入的资料模块；本次只按源码阅读，未调用pytest或上游插件。



## Doctest驱动与coverage数据的实际范围

run_doctests.sh恰收两个参数，quickstart只接受a2/310p，installation只接受pip/uv/source；不是任意SoC和安装方式的笛卡尔积。quickstart按marker抽取离线脚本、服务启动、models、completion和stop；common.sh对URL等待和进程退出有各自deadline，不把HTTP ready等同业务输出有效。安装驱动会改包/镜像/git配置、克隆或构建并执行抽取的文档shell块，属于有副作用的专用环境流程，本次仅阅读。HF_HUB_OFFLINE不自动补齐缺失权重。

tests/coveragerc采branch、thread/multiprocessing并行数据并保留绝对路径，include是vllm_ascend路径；警告被禁用不代表一定有采样数据。覆盖文件、推荐source line与真实NPU路径执行是不同证据；合并多个数据文件前保留对应源码/进程/测试身份，避免路径与修订串用。


## 精准推荐的实际数据职责与覆盖补录

test_selector按changed source与历史coverage做line/function/file粒度匹配，包含density/dedup及缺源/rename/deleted等分支；推荐为空、覆盖稀疏、Csrc变更或新测试不等同没有风险。新增/移动测试收集器按真实PR merge-base→head差异，把新文件/rename和原文件新增test node分开加入extra列表，去重保序。merge_extra按文件/nodeid层次判断已有coverage，整文件覆盖可包含子node，不能单凭同前缀目录认为已覆盖。

run_suite对本地suite做双向sanity：列出的文件存在、covered目录磁盘上的test文件都在suite或明确skipped；upstream配置文件另行处理，不能把Native测试清单当已读其源码。各pytest调用的START/PASSED/FAILED和timing产物分别记录，continue-on-error只改变是否继续，不应消除原失败。estimated_times与median更新用于分区负载估计，不是模型NPU性能基线。

assemble_coverage优先使用收集节点写出的EXPECTED sentinel，否则回退分组/文件key；缺covdata或含FAILED标记均不可用。backfill可从旧package替换当前缺失/失败coverage，故补录后的coverage不能冒称本轮实际执行；保留来源package、源码和目标key，不能仅以目录齐全宣布新分支验证。daily resolver的直接输入会绕过daily_config，精确名/SoC映射和无匹配结果也不是模型不支持。

模型/数据下载清单、PO生成/翻译、链接与覆盖检查属于环境/文档/选择工具，其登记与运行状态不提供模型数值/性能证据。本次读取所有所列配置和工具接口，没有运行选择器、下载、Git操作、安装、CI或测试。


## 上游代码质量工具只证明其静态规则

check_boolean_context_manager检查with/async-with的BoolOp，避免把a() and/or b()当多个上下文；它不是所有异常清理正确性的证明。check_symbolic_meta检查Meta中的numel等具体形状用法，可凭symbolic-meta-ok加理由豁免；豁免/静态通过不证明Meta与真实NPU的shape/dtype一致。forbidden-imports按该上游白名单/正则限制pickle/cloudpickle、直接re/Triton等导入；这些是源项目规则，不自动改写本知识仓治理。

长函数检查结合staged新增行和注释/docstring，缺staged diff时不把存量函数全部判新违规；package __init__检查优先Git tracked集合，避免生成目录误报。logger、mypy、shellcheck、actionlint与PNG检查分别消费各自输入；mypy.ini对torch_npu、FLA等多外部模块ignore_missing_imports，不能把类型检查绿色当依赖确已加载或Native接口兼容。format.sh/pre-commit可修改源码/启动工具，本次只读配置，不执行格式化或静态检查。


## 固定3164的增量回归选择

以下补充固定Main 3164adc8fe75892fbf7f99f524bb72fddf1e6efd相对ceac的测试/配置差异。读取完整diff结构，以新增/变更test入口、parametrize/skip/raises、断言和shape/config的AST投影蒸馏验证合同，配合必要选段；不声称逐字重读所有mock装配、外部callee或Device kernel。本节没有导入或运行任何上游测试、编译、模型、服务、通信或NPU，前文与各专题矩阵的ceac证据仍按其版本解释。

### 先处理迁移、删项与skip

Triton普通路径接收原v2模块，旧路径相关的测试改从ops.triton.sample、spec_decode、block_table等导入；仍属于MRv1的slot/spec/mamba接口移至v1。worker patch_v2相关引用也迁到普通worker补丁，MRv1保留patch_v1。test_triton_layout检查引用目标存在和旧v2目录无Python文件，这验证布局，不证明新ABI/数值成功。纯rename保留原blob语义；删除旧文件或断言只说明该快照证据入口变化，不推导对应功能全部不支持。

enable_dsa_cp在配置、coverage taxonomy和多条用例中移除，不能继续按旧开关搭建当前PCP/DCP测试；MRv1 CP compaction等删项也不等于已有新替代已通过。sleep/wake删除了若干多轮/泄漏/logprob探针，不能沿用旧卡把这些项目算作3164现存覆盖。warmup旧early/thread测试删除，改为registry窗口和kernel specialization合同。dependency测试由文档内容检查缩为requirements/pyproject核心版本一致性，不能据新UT通过推文档命令可执行。

skip必须保留：quantize_indexer_query在A5是模块级skip；SwiGLU MX E2E仍有指向旧post4缺swiglu_mode=2的全局skip，即使仓库依赖已升post7也没有自动解除。QLI adaptive/vector-repeat用例限定A2/A3、MXFP tail限定950、Qwen4 QSA单卡入口限定A3；LiLiCorr按Native symbol存在与否跳过，manual脚本也不自动进入普通CI。移除一个已知bug skip仅说明测试重新可收集，不是本次设备复测通过。

### Attention、稀疏复用与图回放

| 入口族 | 应保存的关键断言与边界 |
| --- | --- |
| SFA DCP单卡/多卡 | DCP2/4/8隔离启动，DCP8特定精度回归另有gate；图后改变输入、FP64 merge预算、全无效行零输出、原始bit保留、非连续/奇数singleton stride和大向量native回退分别验证，不能只用一个allclose |
| Copy-SFA/LIM | compaction排除graph padding，target/draft与物理MTP层history独立；覆盖-3/-2/-1状态转移、slot复用/失效、rollback与短行；draft metadata保存到对应step执行，普通decode不多造restore descriptor，Host持久地址与Device lengths权威、拒绝隐式D2H分别断言 |
| QLI/量化SparseFA | QLI topk边界1/63/65/1024/2048、candidate block合法/唯一；A5 sparse count127/128/129/257和非幂二page回退；rope=0路径与TND容量尾部清零独立，不从一个分支推广全部layout |
| QSA FIA/GBSA | 用显式prefill phase而非query/KV长度猜路由；空/重复/无效索引、逐query可见尾部、512条目内保留tail、ragged非连续block table；FIA mask workspace宽转窄复用、decode graph不建Host request plan和paged地址零copy分别检查 |
| MLA/FlashAttention | 192逻辑head可物理补256，但保留192^-0.5 scale；padding补零、页预算、原输出buffer和有效前缀分别断言；connector wait在cache访问前、普通投影可在wait前、失败load停止访问，profile无metadata不等待connector |
| PCP/DCP O投影 | prefill full weight、sharded decode交换token、普通local weight按batch选择单一mode；PCP先于TP、普通bias只加一次、量化bias独立；异常等待全部gather并恢复local view，不能只看最终shape |

DCP query-replication E2E检查真实组ranks与每层开关，另有dense MLA/SFA拒绝边界；empty local PCP rank仍应参与全局cache/collective，不能把num_actual_tokens=0当全部通信可跳过。metadata role tests区分query/cache/state构造，causal与noncausal不能共享错误buffer，PCP global/local namespace分开，group block table和slot地址不能跨group误复用。已有更广矩阵见[Attention与量化测试](vllm_ascend_attention_quant_test_matrix.md)。

### 混合状态、Qwen4和模型适配

GDN/KDA用dense与block-interleaved mutable state对照：selected gather/scatter、padding不改、卷积prefill/decode/spec、recurrent接受数和图回放分开；recoverSSM断言state/boundary commit之和、实际state dtype计入UB预算。Qwen4 QSA/GDN/PLE的共享池测试还核76输入spec对应source owners、group合并/lifetime、分离PLE dense bank、每region offset/stride/page范围、预算与实际allocation同口径，不以逻辑group数直接乘完整独占分配。高级索引输出必须只物化选中行，不能复制整池；无效slot写入提供独立NPU subprocess探针，不能仅用CPU mock替代。

QSA layerwise顺序为load→indexer/main KV更新→开启prefetch gate→attention→关闭gate→save。压缩page与manager block、kernel page/slot换算以及raw/压缩cache的对应关系分别断言，不能用一个contiguous判断所有共享视图。GLM KPool新增INT8 A3和FP8 capability门禁测试、key/scale同页但不重叠、static scale/padding零化边界、virtual engine cache tuple、量化在padding后以及empty/profile不作Host同步。

DeepSeek V4.1 replay覆盖PCP原owner尾部、prompt logprob行、idle DP rank、统一collective width与异常恢复is_padding/MC2 context；Vision dummy image按宽高比与compress padding做最坏预算，不用普通方图profile代替。Kimi K3 MRv2复用小型dummy smoke场景仅验证框架构造/执行，不能替代完整checkpoint GPQA或AISBench。MiniMax MSA的AscendC index score与A5 Triton decode分派由不同断言核对。详细模型/Worker旧矩阵见[模型与Worker](vllm_ascend_model_worker_test_matrix.md)。

### 缓存、存储与通信失败路径

AscendStore scheduler新增按unfinished顺序过滤、去重scheduled ID、空pending不扫描cached IDs与线性lookup工作量上限；worker租约刷新保留首个重复key索引、稀疏成功位置、partial retry与malformed metadata拒绝。它们约束算法工作量/映射，不是NPU端到端收益，CPU微基准另见[基准指南](../optimization/vllm_ascend_benchmark_workflow.md)。

layerwise tests区分backend能力、PP stage key、每rank/每组完整命中、private tail不可外传、MTP全局到本地layer映射；PLE与Attention可共享一次load但分别copy实际state owner。pending save失败、空末层、partial get错误、已分配/未排队remote prefill ack、完整replicated Mamba选择和metadata不匹配都要保留，不能只测一条store/get happy path。

Preempt offload覆盖DCP partial block、PCP/TP/PP expected worker数量与所有worker完成后事件清理；CPU/GPU null block、MTP tail和ring private block分别裁剪。HIXL消费事件按model/cycle/layer关联，只等前次buffer消费而不随意同步后续背景流；失败保留storage/registration且使session不可用。EPLB AllGather按source eligibility和SP/DP padding计数，token只执行/计数一次，路由表in-place更新、mapping改变才清heat、elastic active width单独验证。更多原测试入口见[分布式缓存矩阵](vllm_ascend_distributed_cache_test_matrix.md)。

### 量化加载、投机采样与生命周期

ModelSlim loader UT核真实owner绑定、reload元数据不强引用layer、bare fused key、packed expert全FLOAT与split/fused不一致拒绝；W4A8 INT线性核pack/alignment、row-parallel scale_bias、meta/空输入不执行算子和prepared输入不被matmul破坏。MXFP4 MoE核独立expert列表/NZ、E8M0原始字节和GMM/EPLB共用canonical视图，RL reload显式异常不能忽略。CEIL激活核每模型实例能力而非改共享class集合、scale算法缓存，以及fallback和GMM2 scale传递；这些是测试合同，不把mock算子视作真实量化质量。

DFlash/LiLiCorr覆盖quantized context KV的projection/norm/RoPE/value scale、mask embedding缺失与损坏区别、MRv1明确拒绝、eager/graph和LM-head TP门禁。概率candidate验证已实现条件分布缓存、旧cache清除、温度与输出频率，而非只看合法token。真实权重LiLiCorr E2E还查draft/accepted计数、逐位置计数和greedy差异的near-tie logprob界限；宽松统计容差不能拿来宣称逐token严格相同。

rejection tests覆盖draft vocab窄于target、placeholder拒绝/target恢复、ragged映射与bonus-only请求。entropy threshold/alpha每调用解析且非法值在launch前拒绝，synthetic与upstream block组合门禁分开；resample需保持未缩放residual分布与acceptance随机数独立。SamplingMask按request-major×rows_per_request表示，空batch、chunk cat、非连续vocab、graph后metadata改变不能退回旧“一请求一行”假设。

UVA prefix dirty范围与稀疏更新、uint64高位、空/失败slice、真实UVA无需tracking分别验证；模型加载后的profiler、hybrid encoder/Mamba state合并、connector defer-finalize在draft后save、失败传播和prompt_embeds拒绝也属于适配必查。310P共享expert早提交的数值/join与unsupported模式fallback、logits warmup去重小batch及父方法失败不能吞掉，各有独立UT，不能只据enable flag认定接线完成。

### 场景配置与报告口径

新Mooncake basic pooling YAML显式关闭本地prefix cache、DP4/TP4、非layerwise与dspark5，用于隔离pool路径；Kimi K3 MRv2四节点内部DP4/TP16、MiniMax M3三节点prefill PP4/TP4与decode DP8/TP4的配置属于不同场景。GLM PP/PD从TP16转TP1+PCP16，HCCL buffer与warmup/正式gate随之改变，不能只比较模型名称或沿旧拓扑复用成绩。

YAML里的baseline/threshold和warmup零baseline都是计划判据，不是本次实测。coverage.html从150变149及marker taxonomy删除dsa_cp仅是静态报告变化；测试数、参数数、skip、真实权重、硬件、有效argv和原始误差/统计仍须从实际run取证。按实现改动选择上述分支，最后统一执行目标检查；本节不提供任何虚构PASS、性能收益或已验证平台升级。
