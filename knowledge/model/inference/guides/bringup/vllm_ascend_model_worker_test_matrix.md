---
type: Guide
title: vLLM Ascend模型与Worker回归：加载、投机、缓存和310P测试矩阵
description: 为模型加载、MRv1/MRv2、投机采样、LoRA与310P变更选择固定UT；核对checkpoint身份、CPU计数、共享cache/参数所有权、图模式与异常恢复，区分mock合同和真实权重/NPU验证。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/fused_moe/test_moe_mlp_310.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/fused_moe/test_shared_fused_moe_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_conv_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_layernorm_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_mm_encoder_attention_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_qwen3vl_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_rotary_embedding_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/quantization/test_modelslim_config_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/quantization/test_w8a8_dynamic_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/quantization/test_w8a8_dynamic_moe_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/quantization/test_w8a8_static_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/quantization/test_w8a8s_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/quantization/test_w8a8sc_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/sample/test_sampler_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/spec_decode/test_llm_base_proposer_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_block_table_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_kv_block_zeroer_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_kv_cache_sharing.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_mamba_align_fallback_310p_source.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_model_runner_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_sharded_state_loader_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/lora/test_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/lora/test_lora_ops.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/lora/test_punica_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/lora/test_quant_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/lora/test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/netloader/test_netloader.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/netloader/test_netloader_elastic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/netloader/test_netloader_load.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/netloader/test_netloader_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_identity_validation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_rfork_loader.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_transfer_backend.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_compile.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_decoder_replay.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_hyper_connection.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_layer_plan.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_operator_contracts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v41_release_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_vision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_vision_preprocess.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_gemma4_mm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5_next_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kda_pcp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_kda_state_dtype.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm_moe_dsa.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_dense_sp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_sequence_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/sample/test_penalties.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/sample/test_rejection_sampler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/sample/test_sampler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_autoregressive_draft_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dflash2_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dflash_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_graph_contract.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dynamic_sd.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_eagle_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_extract_hidden_states_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_gemma4_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_mla_capture_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_mla_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_multi_kv_cache_group_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_step3p5_source_regression.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_adaptive_verification.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_block_table.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_dcp_manager.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_dcp_speculator_metadata_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_disable_compilation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_dsv4_compressed_positions.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_extract_hidden_states_speculator_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_full_sliding_kv_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_fused_mla_cache_lifecycle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_idle_dummy_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_indexer_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_kv_block_zeroer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_kv_cache_allocation_scope.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_kv_cache_block_copy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_layerwise_kv_allocation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_minimax_m3_kv_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_mla_dcp_metadata_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v1_nan_detection.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2_kv_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2_layerwise_reuse.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2_mamba.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_npu_input_batch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_replay_slot_padding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_routing_replay.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_sleep_parameter_retention.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_spec_decode_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_spec_pp_cpu_counts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_worker_multi_instance.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_worker_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_aclgraph.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_pcp_multimodal_embedding_padding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_sparse_kv_offload_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_speculator.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_v2_utils.py
  role: evidence
created_at: '2026-11-03T04:55:52Z'
updated_at: '2026-11-04T02:58:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend模型与Worker回归：加载、投机、缓存和310P测试矩阵

## 模型适配的分层验证

模型加载回归先区分RFork/Netloader身份、transferable tensors、初始化及失败回退。所读断言覆盖RPC端口/注册项目、JSON身份与已有global model state基线保护；“构造抛错后回退成功”还要核内存与原对象身份，不只看返回model非空。真实权重、传输后数值和ABI仍需另验。

MRv2关注请求/批次/slot坐标及CPU/NPU计数：block table逻辑/物理规格、kernel block可整除、slot mapping类型、capture padding与actual请求数分开；DCP、Mamba/attention共享backing、layerwise复用及KV zeroer分段均有独立回归。sleep保留的参数/缓冲要核data_ptr和清理/同步；不存在参数匹配应显式失败，不从mock休眠推真实设备释放。

投机路径分别覆盖Eagle/DFlash/DSpark/MTP和hidden-state提取、draft共享元数据、多个KV组、capture失败及恢复。所读hidden提取断言要求runner引用；MRv2版本仅支持greedy draft_sample_method且需aux_hidden_states。MTP共享topk引用、valid sampled前缀和PP CPU计数不可由单一输出shape替代。

310P是独立实现证据：静态/动态/SC量化、采样generator缓存、rotrary draft开关、Mamba对齐fallback、共享KV布局与sharded loader都按其源测试选择。测试包含明确NotImplementedError/RuntimeError/D2H类型拒绝，不把310P目录覆盖推到所有Ascend平台。

LoRA需核索引交换/分拆/对齐与EP路由，Punica图模式和S/ BGMV路径单独覆盖；量化MoE的未注册/不支持激活、动态EPLB等拒绝都保留。模型族用例另外校验GLM KDA状态dtype、PCP切分、DeepSeek视觉sentinel/层计划与HyperConnection、Gemma多模态dtype；源断言存在不保证真实checkpoint兼容。

实现入口与证据强度分别见[模型适配起步](vllm_ascend_new_model_onboarding.md)和[测试证据选择](vllm_ascend_test_evidence_selection.md)。

## 按断言职责选择源测试

下表是静态语法定位材料：从固定源码的AST遍历函数、assert与assert*/raises调用，保留test*函数计数和摘选谓词，未逐行完成fixture、callee与每条断言的语义复核。原自动聚类的“数值比较”“掩码/有效行”等宽标签不再作为覆盖结论列出；一般相等断言、mock调用或helper名称不能独立证明对应设备语义。摘选谓词帮助回源，不是完整用例正文。名称计数不是pytest实际收集量，fixture命名与参数化实例须另核。参数fixture、mock、skip条件和设备前提仍需打开对应固定来源核实；没有执行或证明任何用例通过。文件无断言时列其fixture/工具接口，不冒充独立数值检查。

| 固定测试文件 | AST test*函数数（非收集量） | 可定位的谓词或失败约束 |
| --- | --- | --- |
| ut/_310p/fused_moe/test_moe_mlp_310.py | 16 | quant_method.apply_gmm1_act_quant.assert_called_once_with(mlp_compute_input); self.assertRaises(NotImplementedError) |
| ut/_310p/fused_moe/test_shared_fused_moe_310.py | 7 | routed_experts.quant_method is specialized_method; init_kwargs['tid2eid'] == 'tid2eid'; specialized_method_factory.assert_called_once_with(moe_config) |
| ut/_310p/ops/test_conv_310.py | 1 | out is expected; mock_forward_native.assert_called_once_with(layer, x) |
| ut/_310p/ops/test_layernorm_310.py | 3 | rms_norm_args[0] is x; rms_norm_args[2] == layer.eps; mock_rms_norm.assert_called_once() |
| ut/_310p/ops/test_mm_encoder_attention_310.py | 2 | out.shape == query.shape; utils.REGISTERED_ASCEND_OPS['MMEncoderAttention'] is AscendMMEncoderAttention310; capture['query_shape'] == (bsz * q_len, layer.num_heads, 128) |
| ut/_310p/ops/test_qwen3vl_310.py | 2 | callable(rot_pos_emb_310); isinstance(is_rc_device(), bool) |
| ut/_310p/ops/test_rotary_embedding_310.py | 3 | rotary_310._mrope_cos_slice.shape[1] == positions.shape[-1]; rotary_310._mrope_cos_slice is not None; first_ptr == second_ptr |
| ut/_310p/quantization/test_modelslim_config_310.py | 3 | mock_create_scheme.assert_called_once_with('INT8', 'language_model.lm_head', 'linear') |
| ut/_310p/quantization/test_w8a8_dynamic_310.py | 6 | mock_npu_dynamic_quantize.assert_called_with(x.contiguous()) |
| ut/_310p/quantization/test_w8a8_dynamic_moe_310.py | 1 | output is expected_output; fused_experts_input.activation == 'silu' |
| ut/_310p/quantization/test_w8a8_static_310.py | 6 | mock_quantize.assert_called_with(x, layer.aclnn_input_scale, layer.aclnn_input_scale_reciprocal, layer.aclnn_input_offset) |
| ut/_310p/quantization/test_w8a8s_310.py | 5 | mock_quantize.assert_called_with(x, layer.aclnn_input_scale, layer.aclnn_input_scale_reciprocal, layer.aclnn_input_offset) |
| ut/_310p/quantization/test_w8a8sc_310.py | 6 | mock_quantize.assert_called_with(x, layer.aclnn_input_scale, layer.aclnn_input_scale_reciprocal, layer.aclnn_input_offset) |
| ut/_310p/sample/test_sampler_310.py | 5 | current_npu_stream.wait_stream.assert_called_once_with(global_npu_stream) |
| ut/_310p/spec_decode/test_llm_base_proposer_310.py | 2 | self.assertRaises(RuntimeError) |
| ut/_310p/test_block_table_310p.py | 5 | self.assertRaisesRegex(TypeError, 'D2H') |
| ut/_310p/test_kv_block_zeroer_310p.py | 3 | self.assertTrue(torch.all(kv == 1)); self.assertTrue(torch.all(kv[:2] == 1)) |
| ut/_310p/test_kv_cache_sharing.py | 6 | attention.page_size_bytes == mamba.page_size_bytes |
| ut/_310p/test_mamba_align_fallback_310p_source.py | 2 | '_tensor_view_from_data_ptr(state, copy_spec.start_addr, copy_spec.num_elements)' in src; 'if src_block_idx == dest_block_idx:' in src |
| ut/_310p/test_model_runner_310p.py | 6 | NPUModelRunner310.supports_standardized_shared_kv_backing is False; calls == ['update', 'model']; runner.attn_backend.get_kv_cache_shape.assert_called_once_with(4 * physical_block_size // kernel_size, kernel_size, 2, head_size) |
| ut/_310p/test_sharded_state_loader_310p.py | 4 | mock_save_file.assert_called_once() |
| ut/lora/test_lora.py | 27 | context.exchanged_lora_indices.dtype == torch.int32; wrapper._lora_stream is None; wrapper.n_slices == 256 * 3; wrapper._events is None; pytest.raises(AssertionError, match='exchanged_lora_indices'); pytest.raises(AssertionError, match='misaligned'); pytest.raises(AssertionError, match='dynamic EPLB'); pytest.raises(AssertionError, match='FusedMC2') |
| ut/lora/test_lora_ops.py | 4 | expand.call_args_list[0].args == (inputs, b_weights, indices, seq_len, expand_out, 0, 32); shrink.assert_called_once_with(inputs, weights, indices, output, 0.5) |
| ut/lora/test_punica_npu.py | 19 | passed_x.dtype == torch.float32; wrapper._use_sgmv() is expected; wrapper._apply_shrink.call_count == 2; refresh.assert_called_once(); pytest.raises(AssertionError, match='top_k_num=1') |
| ut/lora/test_quant_moe.py | 14 | gelu_out.shape == (2, 2); output is down_out; dynamic_quant.call_count == 2; apply_w13.assert_called_once_with(mlp_input.lora_context, gate_up_out=gate_up_out, hidden_states=mlp_input.hidden_states, lora_routing=routing); pytest.raises(NotImplementedError, match='unquantized activations'); pytest.raises(NotImplementedError, match='no implementation registered'); pytest.raises(ValueError, match='already registered'); pytest.raises(NotImplementedError, match=message); pytest.raises(AssertionError, match='BF16/FP16'); pytest.raises(AssertionError, match='expanded_row_idx'); pytest.raises((NotImplementedError, AssertionError), match=message); pytest.raises(NotImplementedError, match='AllGather TP') |
| ut/lora/test_utils.py | 1 | classes[-1] is sentinel; classes[:len(expected_prefix)] == expected_prefix |
| ut/model_loader/netloader/test_netloader.py | 16 | loader.model_path is None; loader.model_path == 'foo-model'; calls == expected_order; pytest.raises(RuntimeError, match='NetLoader elastic loads model fails'); pytest.raises(RuntimeError, match='boom') |
| ut/model_loader/netloader/test_netloader_elastic.py | 24 | sent_tensors[0].shape == (2, 2); payloads[0] is model.params['weight']; len(payloads) == 1; mock_cast_nz.assert_called_once_with(recv_buffer); pytest.raises(RuntimeError, match='registered transfer items'); pytest.raises(RuntimeError) |
| ut/model_loader/netloader/test_netloader_load.py | 4 | result is None; mock_client.assert_called_once_with(['127.0.0.1:15000'], 0, model_path, 1, 1, group_name=group_name, int8_cache=int8_cache) |
| ut/model_loader/netloader/test_netloader_utils.py | 11 | kept == {'enable_multithread_load': True, 'num_threads': 8, 'enable_weights_track': False} |
| ut/model_loader/rfork/test_identity_validation.py | 49 | identity_module._get_model_revision(config) is None; identity_module._canonicalize_fingerprint_value(first) == identity_module._canonicalize_fingerprint_value(second); build(base) == build(reordered); pytest.raises(RuntimeError, match='JSON object'); pytest.raises(ValueError, match='rfork_seed_port_base must be a JSON integer in range'); pytest.raises(RuntimeError, match='model_url'); pytest.raises(RuntimeError, match='model_deploy_strategy_name'); pytest.raises(RuntimeError, match='compatibility fingerprint'); pytest.raises(RuntimeError, match='structural digest'); pytest.raises(ValueError, match='conflicts'); pytest.raises(RuntimeError, match='requires a bound structural digest'); pytest.raises(RuntimeError, match='changed after binding'); pytest.raises(ValueError, match='recursive reference') |
| ut/model_loader/rfork/test_rfork_loader.py | 33 | _get_ep_rank(config) is None; loader.rfork_config.seed_timeout_sec == expected; events.index('eval') < events.index('start_seed_service'); pytest.raises(RuntimeError, match='EP group is not initialized'); pytest.raises(RuntimeError, match='PP group is not initialized'); pytest.raises(RuntimeError, match='boom') |
| ut/model_loader/rfork/test_transfer_backend.py | 32 | tuple(tensor.shape) == (1, 2, 3); backend.register_memory_region(object(), False) is (gap == 0); _select_weight_blocks(snapshot, [(100, 200), (110, 120)]) == [(180, 20)]; pytest.raises(ImportError, match='MemoryRegistration'); pytest.raises(RuntimeError, match='invalid RPC port'); pytest.raises(RuntimeError, match='get_rpc_port'); pytest.raises(RuntimeError, match='native rpc port query failed'); pytest.raises(RuntimeError, match='mock initialize error') |
| ut/models/test_deepseek_v41_compile.py | 1 | tensor._dynamo_dynamic_indices == {0}; pytest.raises(ReadyToCompile) |
| ut/models/test_deepseek_v41_decoder_replay.py | 6 | hidden.shape[0] == 2; replay is not None; model.decoder_replay_start == 1 |
| ut/models/test_deepseek_v41_hyper_connection.py | 10 | y.shape == (2, 5120); actual is expected; y.dtype == torch.bfloat16; op.assert_called_once_with(x, hc_fn, hc_scale, hc_base, pre_mix, hc_mult=4, hc_sinkhorn_iters=3, norm_eps=1e-06, hc_eps=1e-06) |
| ut/models/test_deepseek_v41_layer_plan.py | 4 | topology.layer(0).kv_source_layer is None; topology.kv_consumers(2) == tuple(range(2, 8)) |
| ut/models/test_deepseek_v41_operator_contracts.py | 2 | len(calls) == 2 |
| ut/models/test_deepseek_v41_release_config.py | 5 | config.model_type == 'deepseek_v41' |
| ut/models/test_deepseek_v4_moe.py | 5 | tid2eid.dtype == torch.int32; kwargs['hash_indices_table'] is moe.gate.tid2eid; tid2eid.shape == (config.vocab_size, config.num_experts_per_tok); pytest.raises(ValueError, match='hash MoE routing requires input_ids') |
| ut/models/test_deepseek_v4_vision.py | 4 | table.dtype == torch.bfloat16; table is not None; table.shape == (5, 8); language_model.set_aux_hidden_state_layers.assert_called_once_with((41, 42, 43)) |
| ut/models/test_deepseek_v4_vision_preprocess.py | 3 | output['patches'].dtype == torch.bfloat16; placeholder.is_embed is not None; output['patches'].shape[1:] == (3, 14, 14) |
| ut/models/test_gemma4_mm.py | 4 | parameters['weight'].shape == (64, 48); patch_embedder._ascend_activation_dtype is torch.bfloat16; parameters['weight_scale'].shape == (64, 3) |
| ut/models/test_glm5_next_mtp.py | 4 | get_spec_layer_idx_from_weight_name(config, 'model.layers.44.mlp.weight') is None; get_spec_layer_idx_from_weight_name(config, 'model.layers.45.enorm.weight') == 45 |
| ut/models/test_glm5next_kda_pcp.py | 5 | layer.in_proj_qkvbfg_a.weight.shape[0] == 3 * 1024 // size + 8 // size + 2 * 128; layer.pcp_group is parallel_groups; layer.tp_size == layer.weight.tp_size == 4; pytest.raises(AssertionError) |
| ut/models/test_glm5next_kda_state_dtype.py | 2 | spec.dtypes == want; layer.get_state_dtype() == want; pytest.raises(ValueError, match='KDA recurrent state supports only') |
| ut/models/test_glm_moe_dsa.py | 1 | vllm_config is config; model.num_moe_layers == expected |
| ut/models/test_kimi_k3_dense_sp.py | 1 | kwargs['reduce_results'] is (not sequence_parallel); calls == (['gather', 'tp_mlp', 'reduce_scatter'] if sequence_parallel else ['tp_mlp']) |
| ut/models/test_sequence_parallel.py | 1 | torch.testing.assert_close(result, expected[:expected.shape[0] // tp_size]); value is x; len(inputs) == 1; custom.assert_called_once() |
| ut/sample/test_penalties.py | 1 | out is logits; output_tokens[0, 1].item() == 8 |
| ut/sample/test_rejection_sampler.py | 17 | processed.shape == logits.shape; AscendRejectionSampler.apply_penalties(logits, SimpleNamespace(no_penalties=True), None, None, []) is logits; output.logprobs_tensors == 'lp'; min_tokens.apply_with_spec_decode.assert_called_once(); pytest.raises(ValueError, match='synthetic_mode') |
| ut/sample/test_sampler.py | 3 | partial.shape == full.shape == empty.shape == (2,); AscendSampler.apply_penalties(logits, SimpleNamespace(), []) is fallback_logits; greedy.tolist() == [1, 2]; fallback.assert_called_once() |
| ut/spec_decode/conftest.py | 0 | _stub_ascend_config |
| ut/spec_decode/test_autoregressive_draft_metadata.py | 1 | steps[0]['draft_layer'].block_tables.shape == (num_reqs_padded, max_blocks) |
| ut/spec_decode/test_dflash2_proposer.py | 8 | args[2].shape == (num_reqs, num_steps); DFlash2Qwen3Model.decoder_layer_cls is DFlash2Qwen3DecoderLayer; args[3] == num_reqs; launched.__getitem__.assert_called_once_with((min(num_reqs, 8),)) |
| ut/spec_decode/test_dflash_proposer.py | 2 | input_ids.shape == (num_input_tokens,); proposer._get_positions(num_input_tokens).shape == input_ids.shape; proposer._runnable.assert_called_once() |
| ut/spec_decode/test_dspark_graph_contract.py | 10 | speculator._context_slot_mappings.dtype == torch.int32; manager.run_fullgraph(desc) is replay.return_value; list(speculator.attn_backends) == ['draft.2', 'draft.0']; replay.assert_called_once_with(desc); pytest.raises(AssertionError) |
| ut/spec_decode/test_dynamic_sd.py | 6 | lookup[batch_size] == expected_num_spec_tokens; pytest.raises(ValueError, match=error); pytest.raises(ValueError, match='3-item sequence'); pytest.raises(ValueError, match='is required'); pytest.raises(IndexError) |
| ut/spec_decode/test_eagle_proposer.py | 47 | all((slot_mapping.shape == torch.Size([expected_capacity]) for slot_mapping in proposer.slot_mapping_group)); mock_update_graph.call_args.args[0] is main_group.backend; proposer._draft_attn_layer_names == {draft_name, indexer_name}; self.proposer.build_model_inputs_first_pass.assert_called_once_with(12, self.proposer._context_slot_mapping_buffers); pytest.raises(ValueError, match='no executable attention backend') |
| ut/spec_decode/test_extract_hidden_states_proposer.py | 8 | next_token_ids.dtype == torch.int32; num_tokens_across_dp is None; num_tokens_padded == 8; runner._sync_metadata_across_dp.assert_called_once_with(num_tokens=8, is_draft_model=True, cudagraph_mode=local_mode); pytest.raises(AssertionError, match='requires a runner reference') |
| ut/spec_decode/test_gemma4_proposer.py | 4 | result is expected; impl.kv_sharing_target_layer_name == 'target.attn'; proposer_cls.assert_called_once() |
| ut/spec_decode/test_mla_capture_metadata.py | 2 | captured.is_prefilling.dtype == torch.bool; captured is not common; captured.attn_state == (AscendAttentionState.ChunkedPrefill if state is None else state); builder.build.assert_called_once_with(0, captured); pytest.raises(AssertionError) |
| ut/spec_decode/test_mla_dspark.py | 14 | spec._context_slot_mappings.dtype == torch.int32; type(spec) is AscendDSparkSpeculator; spec.propose(batch, *[None for _ in range(10)], **{dp_sync_kwarg: target_sync}) == 'draft'; events == ['enter communicator', 'enter model', 'capture', 'exit model', 'exit communicator']; pytest.raises(ValueError, match=message); pytest.raises(ValueError, match='incompatible'); pytest.raises(RuntimeError, match='capture failed'); pytest.raises(RuntimeError, match='build failed'); pytest.raises(RuntimeError, match='query failed') |
| ut/spec_decode/test_mtp.py | 3 | model.topk_indices_buffer is original_buffer; torch.testing.assert_close(original_buffer[:count], expected_rows[start:start + count]); model.compact_topk_indices.assert_called_once_with(indices) |
| ut/spec_decode/test_multi_kv_cache_group_proposer.py | 16 | len({t.data_ptr() for t in tables}) == 2 and all((t.shape == (2, 2) for t in tables)); result is expected; AscendMultiKVCacheGroupMTPProposer.__bases__ == (AscendEagleProposer,); parent_update.assert_called_once_with(*args, **optional_args); pytest.raises(AssertionError) |
| ut/spec_decode/test_step3p5_source_regression.py | 3 | finder.call is not None; [arg.arg for arg in step_run.args.args] == [arg.arg for arg in base_run.args.args] |
| ut/spec_decode/test_utils.py | 1 | torch.testing.assert_close(metadata.seq_lens, expected) |
| ut/worker/conftest.py | 0 | _stub_ascend_config |
| ut/worker/test_adaptive_verification.py | 8 | torch.testing.assert_close(result, torch.tensor([0, 2, 0, 2, 0], dtype=result.dtype)); builder_cls.get_cudagraph_support(config, Mock()) is expected; observed == [expected]; model.compute_confidence.assert_called_once_with(hidden, markov) |
| ut/worker/test_block_table.py | 14 | self.assertRaisesRegex(ValueError, 'None of the kernel sizes \\[100, 160\\] can divide physical block size 384'); self.assertRaisesRegex(ValueError, 'kernel_sizes length \\(3\\) must match block_sizes length \\(2\\)'); self.assertRaisesRegex(ValueError, 'max_num_blocks length \\(1\\) must match block_sizes length \\(2\\)') |
| ut/worker/test_dcp_manager.py | 10 | metadata is not None; metadata.seq_len == expected_seq_len; manager.query_lens_full.copy_to_gpu.assert_called_once_with(); pytest.raises(AssertionError, match='must be classified as decode') |
| ut/worker/test_dcp_speculator_metadata_v2.py | 7 | common.causal is False; common.seq_lens_cpu.tolist() == expected |
| ut/worker/test_disable_compilation.py | 2 | model.do_not_compile is (not initial); pytest.raises(RuntimeError, match='warmup failed') |
| ut/worker/test_dsv4_compressed_positions.py | 1 | np.testing.assert_array_equal(optimistic_positions[0], np.array([], dtype=np.int64)); np.testing.assert_array_equal(optimistic_lengths[0], np.array([0])) |
| ut/worker/test_extract_hidden_states_speculator_v2.py | 4 | kwargs['num_tokens_across_dp'] is None; init_speculator(vllm_config, device) == (vllm_config, device); pytest.raises(ValueError, match="only supports draft_sample_method='greedy'"); pytest.raises(ValueError, match='aux_hidden_states are required') |
| ut/worker/test_full_sliding_kv_cache.py | 7 | reshaped['shared_layer'] is reshaped[groups[0].layer_names[0]]; full.page_size_bytes == sliding.page_size_bytes; allocate.assert_called_once_with(cache.kv_cache_tensors[0].size); pytest.raises(ValueError, match='Shared attention\|Invalid shared attention') |
| ut/worker/test_fused_mla_cache_lifecycle.py | 4 | zeroer._meta is not None; len(seg_addrs) == 1 |
| ut/worker/test_idle_dummy_config.py | 1 | get_current_vllm_config() is config; num_tokens == 2; pytest.raises(RuntimeError, match='dummy failed') |
| ut/worker/test_indexer_cache.py | 1 | bf_view.data_ptr() == data.data_ptr(); allocations == [3 * bf16.page_size_bytes] |
| ut/worker/test_kv_block_zeroer.py | 9 | zeroer._meta is not None; seg_page_sizes.tolist() == [16384, 4096] |
| ut/worker/test_kv_cache_allocation_scope.py | 5 | result is reshaped; runner.recovery_calls == 0; mock_synchronize.assert_called_once_with() |
| ut/worker/test_kv_cache_block_copy.py | 9 | torch.testing.assert_close(raw_storage, expected, rtol=0, atol=0); torch.testing.assert_close(conv_state[3], conv_before[1]) |
| ut/worker/test_layerwise_kv_allocation.py | 1 | raw[main_names[0]][0].data_ptr() != raw[main_names[1]][0].data_ptr(); set(raw) == set(specs) |
| ut/worker/test_minimax_m3_kv_cache.py | 1 | cache[0].shape == (expected_pages, 128, 128); cache[0].data_ptr() == key.data_ptr(); torch.testing.assert_close(cache[0].flatten(), key) |
| ut/worker/test_mla_dcp_metadata_v2.py | 5 | common0.dcp_local_seq_lens is device_local; partition.call_count == int(use_dcp); partition.assert_called_once(); pytest.raises(AssertionError, match='DCP metadata requires') |
| ut/worker/test_model_runner_v1_nan_detection.py | 5 | torch.testing.assert_close(result[1], torch.tensor([2, 0, 3], dtype=result[1].dtype)) |
| ut/worker/test_model_runner_v2_kv_cache.py | 3 | runner.kv_connector is upstream.NO_OP_KV_CONNECTOR; [id(tensor) for tensor in runner.kv_caches] == [id(tensor) for tensor in (k, v, conv, ssm, single)]; runner._register_sparse_kv_caches.assert_called_once_with(caches) |
| ut/worker/test_model_runner_v2_layerwise_reuse.py | 1 | (raw[names[0]] is raw[names[1]]) == shares; len(allocations) == (1 if shares else 2) |
| ut/worker/test_model_runner_v2_mamba.py | 27 | len(state_tensors) == len(spec.shapes); wrapped is not None; normalized.kv_cache_groups[0].kv_cache_spec == spec; mock_decision_kernel.__getitem__.assert_called_once(); pytest.raises(RuntimeError, match='linear_attn'); pytest.raises(ValueError, match='matching K/V size ratios'); pytest.raises(ValueError, match='Cannot align hybrid attention K/V pages for small_attn') |
| ut/worker/test_npu_input_batch.py | 1 | block_table_cls.assert_called_once_with(max_num_reqs=2, max_model_len=1024, max_num_batched_tokens=64, pin_memory=False, device=torch.device('cpu'), block_sizes=block_sizes, max_num_blocks=max_num_blocks, num_speculative_tokens=3, kernel_sizes=expected_kernel_sizes, cp_kv_cache_interleave_size=2, kv_cache_groups=None) |
| ut/worker/test_replay_slot_padding.py | 24 | table._replay_slot_mapping_addrs.dtype == torch.uint64; table.is_prefix_cacheable is cacheable; table._replay_cacheable_groups.tolist() == [] |
| ut/worker/test_routing_replay.py | 1 | bind_routed_experts_capturer is not None; capturer.capture.assert_called_once_with(3, topk_ids) |
| ut/worker/test_sleep_parameter_retention.py | 9 | worker._sleep_saved_parameters['weight'].data_ptr() != model.weight.data_ptr(); set(worker._sleep_saved_parameters) == {'weight'}; parameters['weight'].detach.return_value.to.assert_called_once_with('cpu'); pytest.raises(ValueError, match='No parameter matches sleep retention: missing') |
| ut/worker/test_spec_decode_utils.py | 7 | id(optimistic) == pre_id |
| ut/worker/test_spec_pp_cpu_counts.py | 2 | runner.last_idx_mapping is idx_mapping; runner.sync_spec_pp_cpu_counts == (enabled and use_pp and (steps > 0)); runner.events == expected_events |
| ut/worker/test_worker_multi_instance.py | 6 | worker.model_runner.profile_run.assert_called_once(); self.assertRaises(AssertionError) |
| ut/worker/test_worker_v2.py | 11 | torch_cuda_wrapper.assert_called_once_with(); self.assertRaisesRegex(RuntimeError, 'dummy failure') |
| ut/worker/v2/test_aclgraph.py | 8 | manager.is_draft_model_prefill is True; manager.capture_sizes == [4, 8]; set_prefill.assert_called_once_with([4, 8]) |
| ut/worker/v2/test_pcp_multimodal_embedding_padding.py | 5 | passed_mask.shape == (actual_tokens,); passed_mm_embeds is mm_embeds; output.shape == (padded_tokens, 4); events == ['gather', 'scatter'] |
| ut/worker/v2/test_sparse_kv_offload_metadata.py | 7 | kwargs['req_ids_tensor'].shape == (2,); metadata.build_kwargs(object(), object(), 2, object(), object(), 1) is None; metadata.req_ids_buffers == metadata.token_to_req_buffers == []; pin_memory.assert_called_once_with() |
| ut/worker/v2/test_speculator.py | 40 | result[0]['block_table'].shape == (4, 3); result is out; result == {'draft': metadata}; parent_load_model.assert_called_once_with(target_model) |
| ut/worker/v2/test_v2_utils.py | 1 | fake_cuda.is_current_stream_capturing is fake_npu.is_current_stream_capturing; weak_ref.call_count == 2 |

## 使用边界

AST结构、断言存在及配置参数不是运行记录。新模型变更应由真实调用链选择源测试及其参数，再分别留收集数量、skip、失败、真实退出和数值/性能原始结果。CPU mock只证明被断言的Host行为；涉及torch_npu、分布式、编译或外部权重的路径必须在目标依赖与设备上另验。本次未导入/运行上游、未编译、未调用NPU或Agent A/B；未摘选的精确参数与完整Device语义不由本矩阵补造。
