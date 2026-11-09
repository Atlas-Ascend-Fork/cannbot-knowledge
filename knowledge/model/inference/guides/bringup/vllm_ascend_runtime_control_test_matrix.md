---
type: Guide
title: vLLM Ascend运行控制回归：平台门禁、调度、图、诊断与构建工具矩阵
description: 为平台能力、scheduler、图编译、runtime config/guard、CPU绑定、构建缓存与性能工具选择固定UT；定位异常、状态恢复、缓冲身份和产物完整性，保留CPU
  mock及工具自测与NPU/业务证据之间的边界。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_platform.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/build_cache_test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_ai_qos_tool.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_build_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_build_cache_concurrency.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_doctest_helper.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_generate_zh_docs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_prepare_csrc_l1_restore.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/base.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/compilation/test_acl_graph.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/compilation/test_mm_reduce_scatter_fusion_pass.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/compilation/test_npugraph_ex_utils_check.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/compilation/test_qknorm_rope_fusion_pass.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_circular_buffer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_dyntra_lb_recompute_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_dyntra_lb_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_kv_cache_interface.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_recompute_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_recompute_scheduler_short_request_first.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_scheduler_connector_block_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_score_encoder_cache_manager.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_score_encoder_cache_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_short_request_first_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_short_request_first_scheduler_install.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device/test_device_op.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device/test_paged_mla_cache_read.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device_allocator/test_cpu_binding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device_allocator/test_find_loaded_library.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/helpers/golden_copy_and_expand.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_deepseek_v4_thinking.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_initial_expert_layout.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_packed_kv_cache_compat.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_dyntra_lb_core.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_engine_core.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_fused_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_glm53_reasoning.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_kv_cache_coordinator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_mamba_block_aligned_split.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_mamba_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_multiproc_executor.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_pp_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_speculative_config_dflash.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_speculative_config_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_prefix_cache_cp_patches.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/patch_common/test_hccl_pg_registry.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/patch_common/test_patch_distributed.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_deepseek_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_eagle3_pp_aux.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_kimi_k25.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_mamba_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_mamba_utils_uniform_groups.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_mm_input_norm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_qwen3_5_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_routed_experts_capture.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_uva_zeros.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/profiler/test_torch_npu_profiler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/proxy/test_load_balance_proxy_scheduler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/proxy/test_load_balance_proxy_server.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_config/test_detector_catalog.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_config/test_dist.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_config/test_from_additional.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_config/test_runtime_config_core.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/_helpers.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_action_executor.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_bus_worker.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_detectors_and_kv.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_hooks.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_hot_path_overhead.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_io.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_manual_dump_detail.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_manual_rows.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_report_sanitize.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_review_regressions.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_unified_wiring.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/test_wave_and_actions.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_ascend_forward_context.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_batch_invariant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_compressed_prefix_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_cpu_binding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_dependency_documentation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_envs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_kv_cache_dtype_validation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_logger.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_meta_registration.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_minimax_m3_kv_block_size.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_profiling_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_rlhf_server_logging.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_sleep_mode_tensor_ownership.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_v2_sparse_offload_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_auto_bisect.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_build_manager.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_coordinator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_git_ops.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_report.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_runner.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_verdict.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/bisect/test_version_compat.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/profiling/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/profiling/test_aisbench_capture.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/profiling/test_artifacts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/profiling/test_capture.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/profiling/test_parse.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/profiling/test_request_marker.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/test_aisbench.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/tools/test_spec_decode_metrics.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/runtime_guard/TEST_MATRIX.md
  role: supporting
created_at: '2026-11-03T04:58:08Z'
updated_at: '2026-11-04T02:58:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend运行控制回归：平台门禁、调度、图、诊断与构建工具矩阵

## 从变更面选择控制层证据

平台与dtype回归检查硬件/runner能力、PCP×DCP可行值、图模式fallback、KV cache dtype、MiniMax物理block尺寸及forward context；不能仅凭类名注册或测试目录推所有模型/平台组合支持。调度器覆盖preempt/recompute、等待remote KV、输出可交付状态、short-request aging与FCFS安装前提；queue顺序、状态机和完整最终输出分开验。

Runtime config测试核字段schema、默认值、热加载digest、manual trigger消费、额外配置seed与跨rank同步/对齐失败。Runtime guard另核action队列深度、timeout、bus合并、注入异常后hook还原、fully-off热路径、snapshot有效行及report脱敏。诊断记录存在不能证明底层数值或模型质量正确；dump失败和业务失败也不是同一结论。

图/Pass测试检查graph wrapper捕获与调用身份、range applicability、fusion元数据和硬件能力条件。patch回归覆盖HCCL group acquire/release、初始化失败清理、PP/MTP辅助量、Mamba对齐和prefix-cache patch的安装/回退；源测试结构检查不是目标Native所有版本均可用。

CPU binding测试核线程/核mask、topology与poll-window分配；library定位和C API错误路径不能由一次导入成功代替。睡眠所有权另核参数/embedding buffer的data_ptr、state_dict与remap生命周期，不推导真实设备allocator已释放。

工具层测试将build-cache发布失败/并发BYPASS与可恢复状态、文档代码块/宏替换和未知宏拒绝、AOP二分端点/重建策略/兼容规则，以及profiling manifest完整性/分片/磁盘失败分开。它们说明工具应如何判定与留存证据，不提供实际CI、下载、编译或性能通过结论。

原测试层次与执行边界见[测试证据选择](vllm_ascend_test_evidence_selection.md)，profiling/AOP仍按相应实现合同和实际run确认。

## 按断言职责选择源测试

下表是静态语法定位材料：从固定源码的AST遍历函数、assert与assert*/raises调用，保留test*函数计数和摘选谓词，未逐行完成fixture、callee与每条断言的语义复核。原自动聚类的“数值比较”“掩码/有效行”等宽标签不再作为覆盖结论列出；一般相等断言、mock调用或helper名称不能独立证明对应设备语义。摘选谓词帮助回源，不是完整用例正文。名称计数不是pytest实际收集量，fixture命名与参数化实例须另核。参数fixture、mock、skip条件和设备前提仍需打开对应固定来源核实；没有执行或证明任何用例通过。文件无断言时列其fixture/工具接口，不冒充独立数值检查。

| 固定测试文件 | AST test*函数数（非收集量） | 可定位的谓词或失败约束 |
| --- | --- | --- |
| ut/test_platform.py | 115 | config.use_sequence_parallel_moe is expected; config.decode_context_parallel_size == dcp_size; ops.get_physical_device_id.assert_called_once_with(0); pytest.raises(ValueError, match=f'PCP\\+DCP.*PCP={pcp_size}, DCP={dcp_size}'); pytest.raises(ValueError, match='valid DCP sizes'); pytest.raises(ValueError, match='to equal decode_context_parallel_size'); self.assertRaisesRegex(ValueError, 'torch_gloo'); self.assertRaisesRegex(ValueError, 'elastic EP'); self.assertRaisesRegex(ValueError, "got 'nixl'"); self.assertRaisesRegex(ValueError, 'only supported by Model Runner V2'); pytest.raises(AssertionError, match='PreemptOffloadConnector'); pytest.raises(NotImplementedError); pytest.raises(ValueError, match='recompute_scheduler_enable.*PD-disaggregated.*PD-mixed'); pytest.raises(AssertionError, match='Hybrid models do not support recompute mode kv load failure policy'); pytest.raises(ValueError, match='DyntraLB only supports decoder instances.*single node'); pytest.raises(ValueError, match='enable_balance_scheduling.*PD-mixed.*PD-disaggregated'); pytest.raises(ValueError, match='Prefill Context Parallel'); pytest.raises(ValueError, match='V4 Pro supports at most TP16'); self.assertRaisesRegex(NotImplementedError, 'PCP does not support attention backend'); self.assertRaises(RuntimeError); pytest.raises(AssertionError, match='DCP for SFA'); self.assertRaisesRegex(ValueError, 'incompatible with weight offload/prefetch'); pytest.raises(ValueError, match=message); pytest.raises(ValueError, match='DyntraLB is only supported on PD-disaggregated D nodes'); pytest.raises(ValueError, match='V4\\.1 supports at most TP8'); pytest.raises(ValueError, match=f'{variant} supports at most TP{max_tp_size}') |
| ut/_tools/build_cache_test_utils.py | 0 | build_cache_command; run_command |
| ut/_tools/test_ai_qos_tool.py | 19 | mod._load_first_apply_baseline(p) is None; e.value.code == 1; pytest.raises(SystemExit) |
| ut/_tools/test_build_cache.py | 49 | spec is not None and spec.loader is not None; proc.returncode == 0; pytest.raises(OSError, match='injected cache-entry publish failure'); pytest.raises(ValueError, match='invalid cache path component'); pytest.raises(FileNotFoundError, match='compiler environment metadata') |
| ut/_tools/test_build_cache_concurrency.py | 3 | first.returncode == 0; any((e['event'] == 'cache_result' and e['status'] == 'BYPASS' for e in events)) |
| ut/_tools/test_doctest_helper.py | 13 | spec is not None and spec.loader is not None; helper.extract_doctest_block(text, 'demo') == expected; pytest.raises(helper.DoctestError, match=message); pytest.raises(helper.DoctestError, match='Unknown mkdocs.yml macro'); pytest.raises(helper.DoctestError, match='Invalid Quick Start device: a5'); pytest.raises(HTTPError) |
| ut/_tools/test_generate_zh_docs.py | 7 | result == '当前的流程如下：\n\n1. `BlockScanner` 解析 ``model-code`` 围栏，仅接受 `MODEL_CODE_OPTION_NAMES` 中列出的选项。\n2. `YamlLoader` 加载 `test_case_path`。\n' |
| ut/_tools/test_prepare_csrc_l1_restore.py | 8 | spec is not None and spec.loader is not None; values == {'supported': 'true', 'primary_key': 'primary', 'csrc_hash': 'caller-hash', 'same_csrc_prefix': 'same-csrc-', 'compat_prefix': 'compat-'} |
| ut/base.py | 0 | __init__; setup |
| ut/compilation/test_acl_graph.py | 28 | all((actual is wanted for actual, wanted in zip(call.args, (query, key, key)))); op.call_count == len(expected); impl_cls.update_graph_params.assert_called_once_with(update_stream, forward_context, 8, vllm_config, speculative_config, draft_attn_metadatas=draft_attn_metadatas); self.assertRaises(AssertionError); self.assertRaises(AttributeError) |
| ut/compilation/test_mm_reduce_scatter_fusion_pass.py | 7 | self.assertEqual(_targets(graph_module).count(FUSED_OP), 1); self.assertNotIn(GEMM_OP, _targets(graph_module)) |
| ut/compilation/test_npugraph_ex_utils_check.py | 1 | extra_stream_scope_check(MockMatch([MockNode(None), MockNode(None)])) is True |
| ut/compilation/test_qknorm_rope_fusion_pass.py | 4 | len(keys) == 2 |
| ut/conftest.py | 0 | _clear_enable_sp_before_test; _reset_stream_globals_before_test; _mock_ascend_store_deps; __init__; record_event |
| ut/core/test_circular_buffer.py | 4 | manager.get_num_blocks_to_allocate('a', 129, [], 0, 0, 129) == 1 |
| ut/core/test_dyntra_lb_recompute_scheduler.py | 6 | DyntraLBRecomputeScheduler.schedule is RecomputeScheduler.schedule; len(summaries) == 1; scheduler._apply_load_balance_modifications.assert_called_once_with() |
| ut/core/test_dyntra_lb_scheduler.py | 46 | preempt_calls[0][0] is request; summaries == []; ordered == [middle_priority, highest_priority, lowest_priority]; pytest.raises(RuntimeError, match='Invalid DyntraLB block size') |
| ut/core/test_kv_cache_interface.py | 23 | get_storage_block_size(spec) == expected; AscendMLAAttentionSpec.merge([spec, spec]) == spec; pytest.raises(AssertionError, match='replay policy'); pytest.raises(AssertionError, match='retained token count') |
| ut/core/test_recompute_scheduler.py | 14 | RecomputeScheduler.schedule is not Scheduler.schedule; sync_config.scheduler_cls == 'vllm_ascend.core.recompute_scheduler.RecomputeScheduler'; scheduler.kv_cache_manager.get_block_ids.assert_called_once_with('req-1') |
| ut/core/test_recompute_scheduler_short_request_first.py | 1 | self.assertNotIsInstance(scheduler.waiting, ShortRequestFirstRequestQueue) |
| ut/core/test_scheduler_connector_block_state.py | 2 | first_output.kv_connector_block_state is None; drain.call_count == 2; get_blocks.assert_called_once_with('boundary') |
| ut/core/test_score_encoder_cache_manager.py | 17 | config.get_encoder_cache_manager_obj() is ScoreEncoderCacheManager; manager.cpu_cache_size == 12; pytest.raises(ValueError, match=field); pytest.raises(ValueError, match='manager_config must be a dict'); pytest.raises(ValueError, match='manager_config.cpu_cache_slots') |
| ut/core/test_score_encoder_cache_scheduler.py | 5 | scheduler_output.total_num_scheduled_tokens == 0 |
| ut/core/test_short_request_first_scheduler.py | 9 | q._select_schedulable_queue() is q._short_queue; q.num_short_requests == 1; mock_warning_once.assert_called_once() |
| ut/core/test_short_request_first_scheduler_install.py | 6 | scheduler.waiting is queue; queue.num_immediate_requests == 1; pytest.raises(ValueError, match='requires FCFS'); pytest.raises(RuntimeError, match='before request admission') |
| ut/device/test_device_op.py | 13 | call_kwargs['key_cache'].shape == (4, 128, 8, 64); result is x; work.ndim == 4; mock_fia.assert_called_once(); pytest.raises(ValueError, match='requires Model Runner V2') |
| ut/device/test_paged_mla_cache_read.py | 3 | actual_slots.ndim == 1 and actual_slots.dtype == torch.int64; torch.equal(slot_storage, slots_before); torch.testing.assert_close(packed, expected, rtol=0, atol=0) |
| ut/device_allocator/test_cpu_binding.py | 83 | mock_popen.assert_called_once(); self.assertRaises(RuntimeError) |
| ut/device_allocator/test_find_loaded_library.py | 1 | path is not None |
| ut/helpers/golden_copy_and_expand.py | 0 | golden_copy_and_expand_eagle_inputs; npu_copy_and_expand_eagle_inputs_stub |
| ut/patch/platform/test_deepseek_v4_thinking.py | 3 | params.chat_template_kwargs['enable_thinking'] is True; request.reasoning_effort == reasoning_effort |
| ut/patch/platform/test_initial_expert_layout.py | 3 | layout == [0, 1, 2, 3, 2, 3, 4, 0]; pytest.raises(ValueError, match='divisible') |
| ut/patch/platform/test_packed_kv_cache_compat.py | 2 | use_trailing_layer_fallback is use_fallback; annotator.call_args.args == (config, specs, groups); predicate.assert_called_once_with(config) |
| ut/patch/platform/test_patch_dyntra_lb_core.py | 22 | request_module.RequestStatus is NativeRequestStatus; output.count('step_counter: 7') == 1; events == [('global_unfinished', False), ('balance_load', 8)] |
| ut/patch/platform/test_patch_engine_core.py | 10 | _engine_core_patch._PATCHED is True; calls == [(('engine-arg',), 1, 2, {'vllm_config': vllm_config})]; print_mock.assert_called_once_with('Enable DyntraLB DP load balancing.', 2, True) |
| ut/patch/platform/test_patch_eplb.py | 24 | EPLBConfig().communicator is None; vllm_config.parallel_config.eplb_config.communicator == 'torch_gloo'; call_order == ['move', 'refresh', 'ack']; pytest.raises(ValueError, match="Input should be 'default' or 'stair'"); pytest.raises(ValueError, match='torch_nccl communicator is incompatible'); pytest.raises(RuntimeError, match='group_coordinator'); pytest.raises(StopIteration); pytest.raises(RuntimeError, match=message); pytest.raises(SystemExit, match='worker must terminate'); pytest.raises(RuntimeError, match='refresh failed'); pytest.raises(RuntimeError, match='HIXL EPLB session is closed or failed') |
| ut/patch/platform/test_patch_fused_moe.py | 6 | result is runner; original_factory.call_args.kwargs['num_redundant_experts'] == 2; mapping_op.assert_called_once_with(topk_ids, router.eplb_state.expert_replica_routing_table) |
| ut/patch/platform/test_patch_glm53_reasoning.py | 10 | spec is not None and spec.loader is not None; parser.kwargs['chat_template_kwargs'] == {**before, 'thinking': None, 'enable_thinking': None}; logger.warning_once.assert_called_once() |
| ut/patch/platform/test_patch_kv_cache_coordinator.py | 15 | coordinator.single_type_managers[0].use_eagle is True; coordinator.eagle_group_ids == {0} |
| ut/patch/platform/test_patch_mamba_block_aligned_split.py | 17 | registered is _mamba_block_aligned_split; result == 8; pytest.raises(RuntimeError, match='boom') |
| ut/patch/platform/test_patch_mamba_config.py | 14 | _get_sparse_index_kpool(model_config) is None; _get_sparse_index_kpool(model_config) == 4; upstream.assert_called_once_with(config); pytest.raises(ValueError, match='integer greater than 1'); pytest.raises(AssertionError, match="only support 'align'") |
| ut/patch/platform/test_patch_multiproc_executor.py | 3 | serve.MultiprocExecutor is patched['AscendMultiprocExecutor']; handle.ready_pipe.recv() == (False, {'expert_map': None}) |
| ut/patch/platform/test_patch_pp_mtp.py | 14 | _use_pp_ipc_runtime_patch(vllm_config, use_pp) is expected; parallel_config.pipeline_parallel_size == 2; pytest.raises(NotImplementedError) |
| ut/patch/platform/test_patch_speculative_config_dflash.py | 10 | normalized is config; normalized.architectures == ['DFlashDraftModel'] |
| ut/patch/platform/test_patch_speculative_config_dspark.py | 11 | normalized is config; normalized.architectures == ['Qwen3DSparkModel']; registry.inspect_model_cls.assert_called_once_with(['DSparkDraftModel'], draft_model_config); pytest.raises(ValueError, match='some other speculative config error'); pytest.raises(ValueError, match='other upstream validation failed') |
| ut/patch/platform/test_prefix_cache_cp_patches.py | 34 | tail_mgr.req_to_blocks['old'][0].block_hash is None; coordinator.block_pool.get_num_free_blocks() == free_blocks - group_count; planner.assert_called_once_with(vllm_config, kv_cache_config.kv_cache_groups, 1 << 30) |
| ut/patch/worker/patch_common/test_hccl_pg_registry.py | 15 | key_a is not None; key_a == key_b; destroy_fn.assert_called_once_with(pg) |
| ut/patch/worker/patch_common/test_patch_distributed.py | 17 | module_env.parallel_state_module.GroupCoordinator is module_env.module.GroupCoordinatorPatch; coordinator.torch_distributed_backend == 'hccl'; destroy_order == ['communicator', shared_device_group, cpu_group]; pytest.raises(RuntimeError, match='gloo failed'); pytest.raises(RuntimeError, match='communicator failed') |
| ut/patch/worker/test_patch_deepseek_v2.py | 13 | receive_buffers[0].shape == (3, 2); wrapper.call_args.kwargs['non_causal_multi_token_decode'] is (non_causal is True); len(actual_aux) == len(expected_aux) == len(aux_layers); wrap_factory.assert_called_once_with(model, factory, expected_data_types) |
| ut/patch/worker/test_patch_eagle3_pp_aux.py | 9 | result['aux_layer_0'].shape == (3, 2); eagle3_pp_aux.patch_eagle3_pp_aux_propagation(model) is True; len(aux_states) == 2 |
| ut/patch/worker/test_patch_kimi_k25.py | 2 | vision_tower.quantized_weight.dtype == torch.float32; Learnable2DInterpPosEmbDivided_fixed.forward is patch_kimi_k25.AscendLearnable2DInterpPosEmbDivided_fixed.forward; torch.testing.assert_close(output, expected) |
| ut/patch/worker/test_patch_mamba_utils.py | 3 | torch.testing.assert_close(actual, torch.tensor([value], dtype=actual.dtype)); bufs._layer_copy_staged is True; input_batch.num_accepted_tokens_cpu.tolist() == [1]; state_copy.assert_called_once() |
| ut/patch/worker/test_patch_mamba_utils_uniform_groups.py | 1 | copy_bufs.src_ptrs.dtype == torch.int64; uniform_spec is not None; mamba_utils.get_mamba_groups.__module__ == 'vllm.v1.worker.mamba_utils' |
| ut/patch/worker/test_patch_mm_input_norm.py | 3 | FusedMMInputNorm.__init__ is patched_init; set(model.state_dict()) == set(legacy_state); pytest.raises(ValueError, match='Missing keys.*visual.other.weight') |
| ut/patch/worker/test_patch_qwen3_5_mtp.py | 5 | packed.shape == (4, 6); packed.dtype == torch.bfloat16; predictor.embed_input_ids.assert_called_once() |
| ut/patch/worker/test_patch_routed_experts_capture.py | 8 | actual.shape[0] == 5; torch.all(capturer.device_buffer == 0); pytest.raises(AssertionError, match='unexpected topk_ids batch') |
| ut/patch/worker/test_patch_uva_zeros.py | 3 | viewed['zeros'] == ((cpu.shape,), {'dtype': torch.int64, 'device': 'npu'}); _int64_storage(torch.zeros(2, dtype=torch.int32)).dtype == torch.int32; _zeros_on_npu(cpu) == 'uint64-view' |
| ut/profiler/test_torch_npu_profiler.py | 11 | mock_create.assert_called_once_with(profiler_config, 'dp0_pp0_tp0_dcp0_ep0_rank0'); self.assertRaises(RuntimeError) |
| ut/proxy/test_load_balance_proxy_scheduler.py | 1 | decoder_state.active_tokens == 0.0; pytest.raises(type(failure)) |
| ut/proxy/test_load_balance_proxy_server.py | 14 | st == 200 |
| ut/runtime_config/test_detector_catalog.py | 2 | tr['enabled'] is True; tuple((s.section_key for s in DETECTOR_SCHEMAS)) == DETECTOR_SECTIONS |
| ut/runtime_config/test_dist.py | 20 | dist._runtime_config_sync_group_or_none() is None; sync_due_bits(None, [False, True, False]) == [False, True, False]; pytest.raises(RuntimeError, match='cannot resolve group rank'); pytest.raises(RuntimeError, match='misalignment') |
| ut/runtime_config/test_from_additional.py | 6 | boot.hot_reload is False; boot.path == str(cfg_path); pytest.raises(ValueError, match='runtime_config_path must be a string'); pytest.raises(ValueError, match='runtime_config_hot_reload must be a bool'); pytest.raises(ValueError, match='runtime_config must be a dict') |
| ut/runtime_config/test_runtime_config_core.py | 27 | cfg.hot_reload_enabled is False; cfg.dump_max_times() == 0; pytest.raises(ValueError, match='unknown key'); pytest.raises(ValueError, match='detector.token_repeat.window'); pytest.raises(ValueError, match='must be an integer'); pytest.raises(ValueError, match='save_sensitive_info'); pytest.raises(ValueError, match='unknown top-level key'); pytest.raises(ValueError, match='must be a dict'); pytest.raises(ValueError, match=needle) |
| ut/runtime_guard/_helpers.py | 0 | bare_processor; capture_logger_text; attach_bus_worker |
| ut/runtime_guard/test_action_executor.py | 7 | has_nonempty_sampled_row(['a'], [[1, 2]]) is True; order_incident_actions(['dump_kv', 'report']) == ['report', 'dump_kv']; order_incident_actions(['report']) == ['report'] |
| ut/runtime_guard/test_bus_worker.py | 6 | result is not None; seen_thread == ['ut-bus']; cfg.apply_config_sync_payload.assert_called_once(); pytest.raises(RuntimeError, match='not started'); pytest.raises(RuntimeError, match='queue depth is 1'); pytest.raises(TimeoutError) |
| ut/runtime_guard/test_detectors_and_kv.py | 23 | out.shape == (2, 8); hit[0].is_ill is True; push_token_repeat(st, 1, window=8, ignore=ignore) == 1; guard.queue_kv_dump.assert_called_once() |
| ut/runtime_guard/test_hooks.py | 18 | runner.seen_inference_mode is True; len(fns) == 1; runner.order == ['body', 'postprocess']; pytest.raises(RuntimeError); pytest.raises(RuntimeError, match='boom') |
| ut/runtime_guard/test_hot_path_overhead.py | 13 | cfg.hot_reload_enabled is False; calls == ['sample']; eow.assert_called_once_with(allow_manual_dump=True) |
| ut/runtime_guard/test_io.py | 3 | snap2 is not snap1; normalize_token_ids(t) == [3, 4, 5] |
| ut/runtime_guard/test_manual_dump_detail.py | 1 | cfg.consume_calls == 1 |
| ut/runtime_guard/test_manual_rows.py | 1 | iter_local_request_rows(runner, scheduler_output) == expected |
| ut/runtime_guard/test_report_sanitize.py | 7 | out['prompt_token_ids_truncated'] is True; out['prompt_token_count'] == 3 |
| ut/runtime_guard/test_review_regressions.py | 83 | AscendAsyncOutput(inner, runner).get_output() is out; parsed['incident_type'] == 'token_repeat'; ar.assert_called_once(); pytest.raises(ValueError, match='unknown top-level key'); pytest.raises(ValueError, match='item_sync'); pytest.raises(ValueError, match='unknown key'); pytest.raises(RuntimeError, match='boom'); pytest.raises(RuntimeError, match='hccl down'); pytest.raises(RuntimeError, match='bus down') |
| ut/runtime_guard/test_unified_wiring.py | 14 | not hasattr(model, '__dict__') or 'compute_logits' not in model.__dict__ or model.__dict__['compute_logits'] is original; model.calls == 2 |
| ut/runtime_guard/test_wave_and_actions.py | 5 | wt.take_sample_wave('a') is None; wt.take_sample_wave('a') == 1 |
| ut/test_ascend_forward_context.py | 30 | layer.call_args.kwargs['input_ids'] is input_ids; afc.get_mc2_tokens_capacity() == 600 |
| ut/test_batch_invariant.py | 10 | result is expected; mock_config.weight_nz_mode == 0; mock_reduce.assert_called_once_with(x, -1, True) |
| ut/test_compressed_prefix_cache.py | 6 | get_storage_block_size(spec) == physical_block_size; spec.block_size == logical_block_size |
| ut/test_cpu_binding.py | 1 | test_cpu_binding_placeholder |
| ut/test_dependency_documentation.py | 3 | self.assertTrue(_mkdocs_stable_version()); self.assertIn('config.extra.stable_vllm_ascend_version', main_html) |
| ut/test_envs.py | 2 | self.assertEqual(sorted(envs_ascend.__dir__()), sorted(self.env_vars)); self.assertEqual(getattr(envs_ascend, var_name), var_handler()) |
| ut/test_kv_cache_dtype_validation.py | 20 | AscendDSABackend.supports_kv_cache_dtype(None) is True; _get_backend_cls(backend_cls=_UndeclaredBackend, selector=SimpleNamespace()) == _BACKEND_PATH; pytest.raises(ValueError, match='kv_cache_dtype not supported'); pytest.raises(ValueError); pytest.raises(ValueError, match='Supported kv_cache_dtype values: auto, bfloat16, fp8.'); pytest.raises(ValueError, match='Supported kv_cache_dtype values: auto, bfloat16, int8, turboquant_4bit_nc.') |
| ut/test_logger.py | 12 | self.assertTrue(_is_ascend_module('/path/to/vllm_ascend/platform.py')); self.assertTrue(_is_ascend_module('\\path\\to\\vllm_ascend\\compilation\\acl_graph.py')) |
| ut/test_meta_registration.py | 1 | test_meta_registration_placeholder |
| ut/test_minimax_m3_kv_block_size.py | 9 | original_attention.attn_backend is expected; config.cache_config.block_size == 128 |
| ut/test_profiling_config.py | 6 | result is None; len(entries) == 75; mock_exception.assert_called_once() |
| ut/test_rlhf_server_logging.py | 1 | len(capfd.readouterr().err) >= 2 * 1024 * 1024; ready.exists() |
| ut/test_sleep_mode_tensor_ownership.py | 9 | indexer.q_hadamard is None; rope_dsv4._ROPE_STATE.layer_info[second_layer][0] == config_key; layer._buffers['_dcp_sfa_remap_order'] is impl._remap_order |
| ut/test_utils.py | 55 | utils.is_pd_decode_recompute_scheduler_enabled() is False; json.loads(utils.os.environ['ASCEND_LOCAL_COMM_RES']) == expected; physical_device_lookup.assert_called_once_with(user_device_id); pytest.raises(RuntimeError, match='aclrtGetPhyDevIdByUserDevId failed'); self.assertRaises(ValueError, utils.find_hccl_library); self.assertRaises(ValueError); self.assertRaisesRegex(ValueError, 'multiple of 512') |
| ut/test_v2_sparse_offload_config.py | 13 | config.topk_buffer_size == (1 + mtp) * 2048; pytest.raises(ValueError); pytest.raises(AssertionError); pytest.raises(ValueError, match='hot budget'); pytest.raises(ValueError, match='query rows'); pytest.raises(ValueError, match='V2 remote prompt-context initialization') |
| ut/tools/bisect/conftest.py | 0 |  |
| ut/tools/bisect/test_auto_bisect.py | 10 | Bisector._pick_mid(0, 3, skipped={0, 1, 2}) is None; Bisector._pick_mid(0, 8, skipped=set()) == 4; pytest.raises(SystemExit); pytest.raises(SystemExit, match='No successful good-table row'); pytest.raises(SystemExit, match='Could not determine --num-nodes') |
| ut/tools/bisect/test_build_manager.py | 5 | decision.rebuild is True; decision.reason == 'already built this exact commit' |
| ut/tools/bisect/test_coordinator.py | 6 | command is not None; command == {'round': 1, 'commit': 'abcdef1234567890', 'rebuild': True, 'action': 'RUN'}; pytest.raises(RuntimeError, match='expected abcdef123456') |
| ut/tools/bisect/test_git_ops.py | 4 | candidates[1].pr_number is None; [candidate.commit for candidate in candidates] == [sha_with_pr, sha_without_pr]; pytest.raises(git_ops.GitError, match='shallow clone'); pytest.raises(git_ops.GitError, match='is not an ancestor') |
| ut/tools/bisect/test_report.py | 1 | payload['case_key'] == 'single_node::case.yaml' |
| ut/tools/bisect/test_runner.py | 4 | _safe_name('configs/my case.yaml') == 'configs_my_case.yaml' |
| ut/tools/bisect/test_state.py | 3 | BisectState.load(path, good='new-good', bad='new-bad') is None; BisectState.load(path, good='a' * 40, bad='b' * 40) == state |
| ut/tools/bisect/test_verdict.py | 5 | verdict == 'FAIL' |
| ut/tools/bisect/test_version_compat.py | 9 | VersionPolicy.between(versions, versions).enabled is False; expected_versions(tmp_path) == PackageVersions(vllm='v0.25.1', torch_npu='2.10.0.post2') |
| ut/tools/profiling/conftest.py | 0 | profile_environment |
| ut/tools/profiling/test_aisbench_capture.py | 5 | environment is None and 'type=GenInferencer' in dataset; benchmark.factory.call_args.args[0].start_after_requests == 100; benchmark.controller.finish.assert_called_once(); pytest.raises(FileNotFoundError); pytest.raises(capture.ArtifactError, match='incomplete'); pytest.raises(RuntimeError, match='request failed') |
| ut/tools/profiling/test_artifacts.py | 3 | ('FAILURES' in summary) is failure; saved['status'] == ('partial' if failure else 'success'); pytest.raises(FileExistsError); pytest.raises(capture.ArtifactError, match='disk full') |
| ut/tools/profiling/test_capture.py | 6 | options['torch_profiler_with_memory'] is options['torch_profiler_with_stack'] is True; capture.ProfileSpec.from_env() == capture.ProfileSpec.from_options(spec.options()) == spec; client.stop_profile.assert_called_once(); pytest.raises(ValueError) |
| ut/tools/profiling/test_parse.py | 4 | ('rank1_ascend_pt.tar.gz' in links) is not bool(failure); parse.plan_artifact_shards(manifest_path) == [0]; pytest.raises(ArtifactError, match='incomplete'); pytest.raises(ArtifactError) |
| ut/tools/profiling/test_request_marker.py | 4 | spec is not None and spec.loader is not None; marker.read_text() == '100'; pytest.raises(OSError) |
| ut/tools/test_aisbench.py | 1 | 'chat_template_kwargs={"thinking": True}' in content; 'reasoning_effort=' not in content |
| ut/tools/test_spec_decode_metrics.py | 2 | pytest.raises(AssertionError, match=expected_error) |

## 使用边界

AST结构、断言存在及配置参数不是运行记录。新模型变更应由真实调用链选择源测试及其参数，再分别留收集数量、skip、失败、真实退出和数值/性能原始结果。CPU mock只证明被断言的Host行为；涉及torch_npu、分布式、编译或外部权重的路径必须在目标依赖与设备上另验。本次未导入/运行上游、未编译、未调用NPU或Agent A/B；未摘选的精确参数与完整Device语义不由本矩阵补造。


## Runtime guard验证计划的强度

TEST_MATRIX同时列文档期望、UT对应文件与集成/现场验证：默认off应与baseline tokens一致、TPS在噪声范围，坏JSON/类型热加载应保留旧配置且服务存活，队列/merged bus失败要退款并不apply。文档中的Yes或编号映射是计划/关联说明，不是本次实际执行；soft-fail也需核实际hook、copy线程、sampler与业务输出未被异常破坏。
