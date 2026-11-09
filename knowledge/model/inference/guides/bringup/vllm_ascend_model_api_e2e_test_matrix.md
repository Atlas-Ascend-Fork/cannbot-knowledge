---
type: Guide
title: vLLM Ascend模型与API端到端验证：输出、缓存命中、投机和状态切换矩阵
description: 按固定PR/E2E测试选择真实模型和API场景，区分响应结构、输出质量、投机指标、缓存命中、weight-update oracle与设备状态；保留输入、拓扑、skip和真实运行结果的边界。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/test_kvpp_dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/test_kvpp_mooncake_layerwise.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/test_kvpp_pool.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/kv_pool/test_qwen3_30b_acc.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_chat_template_kwargs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_content.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_context_length.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_frequency_penalty.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_logprobs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_max_completion_tokens.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_max_tokens.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_n.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_presence_penalty.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_repetition_penalty.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_request_id.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_role.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_stop.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_temperature.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_think_tag.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_tool_choice.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_top_k.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/tests/test_top_p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/utility/assertion.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/utility/completion_request.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/openai_api_compatibility/utility/http_client.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/cases/features/test_qwen3_grid_exceed_65536.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/kv_pool/config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/kvpp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/single_node/kv_pool_runtime.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/doctests/scripts/doctest_helper.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/model_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/test_asr_eval_correctness.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/test_kimi_fp8_eagle3_generation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/models/test_rm_eval_correctness.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/_310p/test_dense_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/_310p/test_moe_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/context_parallel/test_accuracy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/context_parallel/test_accuracy_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/context_parallel/test_deepseek_v4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/model_runner_v2/test_deepseek_v4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/model_runner_v2/test_kvpp_pp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/model_runner_v2/test_qwen35_pp_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/model_runner_v2/test_qwen38_pp_mtp_prefix_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/model_runner_v2/test_spec_decode_data_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/model_runner_v2/test_spec_pp_accuracy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/rlhf/consistency/test_batch_invariant_tp4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/spec_decode/test_mtp_qwen3_next.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/spec_decode/test_mtp_step3p5.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_data_parallel_tp2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_deepseek_v3_2_w8a8_pruning.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_deepseek_v4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_graph_mode.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_kimi_k3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_kvpp_pd.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_minimax_m3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_pipeline_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_qwen3_5.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_qwen3_mrv2_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_qwen3_next.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_qwen3_next_w8a8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/test_sequence_parallel_linear.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_classification_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_dense_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_embedding_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_lora_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_qwen35_dense_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_sampling_temp_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_scoring_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_spec_decode_mtp_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/_310p/test_vl_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/aclgraph/test_device_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/attention_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/compile/backend.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/compile/test_graphex_norm_quant_fusion.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/compile/test_graphex_qknorm_rope_fusion.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/compile/test_graphex_qkvnorm_rope_fusion.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/compile/test_norm_quant_fusion.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_ilama_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_llama32_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_lora_with_spec_decode.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_olmoe_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_qwen35_densemodel_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_qwen3_multi_loras.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_qwen3_reranker_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/lora/test_qwenvl_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_deepseek_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_deepseek_v2_lite_w8a8_basic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_llama3_1_8b_eagle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_0_6B_basic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_8B.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_dflash.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_draft_model.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/test_uva.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/model_runner_v2/utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/pooling/test_classification.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/pooling/test_embedding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/pooling/test_qwen3_embedding_mrv2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/pooling/test_scoring.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/consistency/test_attention_fa3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/consistency/test_fa3_mixed_batches.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/state_transitions/npu_stream_busy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/state_transitions/test_npu_device_synchronize.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/state_transitions/test_npu_ipc_weight_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/state_transitions/test_pause_resume.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/state_transitions/test_sleep_wake.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/rlhf/test_trace_replay.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_dflash.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_draft_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_eagle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_extract_hidden_states.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_mtp_eagle_correctness.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_ngram.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_ngram_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/test_suffix.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/spec_decode/utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_attention_v1_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_batch_job_aware_scheduler_e2e.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_completion_with_prompt_embeds.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_cpu_offloading.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_cpu_weight_offload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_ec_cpu_offload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_ec_mooncake_fallback.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_eplb_map_to_physical_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_fla_lazy_imports.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_flash_attn_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_gdn_layerwise_kv.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_gdn_stable_argsort.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_guided_decoding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_gumbel_sampling.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_kv_pool_accuracy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_linear_quantization.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_minicpm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_minimax_m3_sparse_attn.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_minimax_qknorm_rope_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_mla_fp8_decode_layout_a5.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_mla_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_model_runner_v1_with_device.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_multi_instance.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_multistream_overlap_shared_expert.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_qwen3_0_6b.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_qwen3_5_0_8b.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_qwen3_8b_w8a8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_qwen3_embedding_0_6b.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_sampler.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_sfa_v1_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_simple_cpu_offload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_thinking_budget.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_vlm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/rlhf/weight_transfer_test_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/_310p/test_dense_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/_310p/test_moe_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/_310p/test_vl_model_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/aclgraph/test_aclgraph_capture_replay.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/lora/test_ilama_lora_tp2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/lora/test_llama32_lora_tp2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/lora/test_qwen35_4b_multi_lora_mtp_aclgraph.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/lora/test_qwen35_densemodel_lora_tp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/lora/test_qwen3moe_lora.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_data_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_mamba_hybrid.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_qwen3_5_eagle3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_qwen3_6_dflash.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_qwen3_6_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_qwen3_6_mtp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/model_runner_v2/test_spec_decode_data_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/pooling/test_qwen3_embedding_mrv2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/rlhf/consistency/test_moe_routing_replay.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/rlhf/state_transitions/test_hccl_weight_transfer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/rlhf/state_transitions/test_pause_device_idle.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/spec_decode/test_spec_decode.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/spec_decode/test_spec_decode_heavy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_activation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_data_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_deepseek_multistream_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_disaggregated_encoder.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_ec_mooncake_encoder_output.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_gemma4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_gpt_oss_distributed.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_hixl_eplb_registration.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_kvpp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_pipeline_parallel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_prefix_caching.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_qwen3_30b_a3b.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_qwen3_5_35b_a3b_w8a8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_qwen3_6_27b_fia.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_qwen3_moe_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_qwen3_performance.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_qwen3_vl_30b_a3b_instruct.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_shared_expert_dp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_shared_expert_dp_graph.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/utils_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/pooling/template/qwen3_reranker.jinja
  role: evidence
created_at: '2026-11-03T05:05:23Z'
updated_at: '2026-11-04T02:56:11Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend模型与API端到端验证：输出、缓存命中、投机和状态切换矩阵

## 使用矩阵前先确定要证明的行为

先记录目标模型、API/任务、固定 Ascend revision、输入与参考结果，再区分参数/响应协议、真实输出质量、缓存命中、投机计数或状态切换。下表保留 ceac 测试文件、函数计数与谓词，供定位后继续读 fixture、参数化、skip 和被调用的 assertion helper；未逐行完成语义复核的行不作为覆盖证明。计数也不是 pytest 实际收集或通过数量。

已核的 `test_max_tokens.py` 是一个边界例：正整数、stream、非法值、宽松类型转换及 stop/sampling 组合分别调用响应 helper。`assert_chat_completion_success` 检查 HTTP 200、合法 finish_reason，以及 stream 的 `[DONE]` 和唯一 finish_reason；它不比较实际生成 token 数与预算，也不检查 Attention mask 或模型数值等价。非法值走 validation-error 检查；字符串和布尔值允许成功或规范拒绝。需要验证长度上限时，仍须另选具有相应 token/usage 断言的测试并核其输入。

原表自动聚类得到的“数值比较”“掩码/有效行”等宽标签已移除：它们不能仅由 helper 名称、一般相等断言或 AST 关键词推出。以下每行保留的谓词是可回源的定位材料，完整证明强度继续按实际断言判断。

## 选择能证明目标行为的端到端证据

API兼容测试分开stream/nonstream响应、token限制、n、stop、惩罚、logprobs、request-id、角色、tool-choice与thinking标签。200或response-shape只证明请求与协议层的一部分；验证错误响应也不等于模型语义正确。utility/assertion和request构造器提供共用判据，具体输入边界按源参数而不是API字段名称猜测。

普通文本、多模态、embedding/classification/scoring、ASR与reward评估各用其实际任务与reference。输出非空、答案前缀/固定样例一致、任务accuracy、embedding数值相近是不同强度；不能以单条chat非空或计数通过替代完整任务质量。E2E配置与模型身份见[配置证据矩阵](vllm_ascend_e2e_configuration_evidence_matrix.md)。

投机路径除输出匹配，还校验draft-token计数、每位置接受率、acceptance length、不同seed及窗口边界；counter/vector类型和零分母处理按共用helper。PP/DP/CP组合有独立多rank与prefix-cache比较，graph-mode测试另核token/logprob与capture/replay次数，不从单卡通过推整个组合有效。

KV offload/pool测试区分cold/warm输出一致与实际external-cache hit、loaded key或存储事件。相同回答不能独立证明走过远端/CPU路径；只有counter增长也不能独立证明完整输出正确。EC的mmap或bounce buffer、GDN逐层save、KVPP PD/PP场景按完整请求与生命周期分别验证。

RL状态切换测试区分NPU stream忙/idle、device synchronize、pause/resume、sleep/wake与参数更新。权重oracle明确要求dummy signature不同于reference，更新后及重新加载后都匹配reference，从而防止“请求成功但权重未更新”的伪通过；源码oracle不是本次真实参数已传输证据。内存释放阈值也只属于该测试条件，不作为平台通用收益。

LoRA及多LoRA/MTP、EPLB动态commit、shared-expert overlap、CPU weight offload和多实例均需实际命中的模型分支与参照。目录one/two/four_card、marker或模型名不是实际runner/设备分配；已登记测试是否收集/skip、调用共享helper是否施加对应判据要看真实run。

本卡只蒸馏源测试的验证职责与明确谓词，不执行网络请求、服务、权重加载、测试或NPU；空行、shape或pytest退出本身不能提升为适配与性能完成。

## 按断言职责选择源测试

下表从固定源码的AST遍历全部函数、assert与assert*/raises调用，保留函数计数和摘选谓词；这些帮助定位，不是完整用例正文或逐行语义覆盖认证。名称计数不是pytest实际收集量，fixture命名与参数化实例须另核。参数fixture、mock、skip条件和设备前提仍需打开对应固定来源核实；没有执行或证明任何用例通过。文件无断言时列其fixture/工具接口，不冒充独立数值检查。

| 固定测试文件 | AST test*函数数（非收集量） | 可定位的谓词或失败约束 |
| --- | --- | --- |
| e2e/cases/features/kv_pool/test_kvpp_dspark.py | 1 | sum((metric.value for metric in runner.model.get_metrics() if metric.name == 'vllm:spec_decode_num_draft_tokens')) > 0 |
| e2e/cases/features/kv_pool/test_kvpp_mooncake_layerwise.py | 1 | output_texts(complete(server.url_root, [prompt, prompt])) == expected * 2 |
| e2e/cases/features/kv_pool/test_kvpp_pool.py | 1 | output_texts(complete(server.url_root, [prompt, prompt])) == expected * 2 |
| e2e/cases/features/kv_pool/test_qwen3_30b_acc.py | 1 | choices[0].text |
| e2e/cases/features/openai_api_compatibility/conftest.py | 0 | api_client; pytest_addoption |
| e2e/cases/features/openai_api_compatibility/tests/test_chat_template_kwargs.py | 7 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_content.py | 4 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_context_length.py | 2 | assertion.assert_chat_completion_success(response, stream=stream); assertion.assert_validation_error_response(response) |
| e2e/cases/features/openai_api_compatibility/tests/test_frequency_penalty.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_logprobs.py | 4 | assertion.assert_status_code_200(response); assertion.assert_top_logprobs_count(response, top_logprobs) |
| e2e/cases/features/openai_api_compatibility/tests/test_max_completion_tokens.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_max_tokens.py | 5 | 已核：正整数 1/32/512、stream、非法 0/-1/1.5、字符串/布尔 coercion、stop+sampling；分别调用 assert_chat_completion_success、assert_validation_error_response、assert_success_or_validation_error；未断言实际生成 token 数不超过 max_tokens |
| e2e/cases/features/openai_api_compatibility/tests/test_n.py | 5 | len(response.json()['choices']) == expected |
| e2e/cases/features/openai_api_compatibility/tests/test_presence_penalty.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_repetition_penalty.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_request_id.py | 1 | assertion.assert_validation_error_response(response); assertion.assert_status_code_200(response) |
| e2e/cases/features/openai_api_compatibility/tests/test_role.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_stop.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_temperature.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_think_tag.py | 2 | assertion.assert_completion_response_shape(response, stream=stream); assertion.assert_no_think_tag(response.text) |
| e2e/cases/features/openai_api_compatibility/tests/test_tool_choice.py | 8 | assertion.assert_completion_response_shape(response); assertion.assert_completion_response_shape(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_top_k.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/tests/test_top_p.py | 5 | assertion.assert_chat_completion_success(response); assertion.assert_chat_completion_success(response, stream=True) |
| e2e/cases/features/openai_api_compatibility/utility/assertion.py | 0 | a == b |
| e2e/cases/features/openai_api_compatibility/utility/completion_request.py | 0 | chat_request_body; send_chat_request; send_completion_request; send_request |
| e2e/cases/features/openai_api_compatibility/utility/http_client.py | 0 | AssertionError(f'GET {url} failed: {str(e)}'); AssertionError(f'POST {url} failed: {str(e)}') |
| e2e/cases/features/test_qwen3_grid_exceed_65536.py | 1 | len(outputs) == 512 |
| e2e/common/kv_pool/config.py | 0 | parse_kv_pool_config; validate_kv_pool_config; type; type; type |
| e2e/common/kvpp.py | 0 | all((choice['finish_reason'] == 'length' for choice in result['choices'])) |
| e2e/common/single_node/kv_pool_runtime.py | 0 | _replace_localhost; create_single_node_kv_pool_manager; __init__; start; _write_config |
| e2e/doctests/scripts/doctest_helper.py | 0 | base_text is not None and head_text is not None |
| e2e/model_utils.py | 0 | len(outputs_0_lst) == len(outputs_1_lst) |
| e2e/models/test_asr_eval_correctness.py | 1 | success |
| e2e/models/test_kimi_fp8_eagle3_generation.py | 1 | case is not None; args[args.index('--kv-cache-dtype') + 1] == 'fp8' |
| e2e/models/test_rm_eval_correctness.py | 1 | success |
| e2e/pull_request/four_card/_310p/test_dense_model_310p.py | 1 | test_qwen3_dense_tp4_w8a8 |
| e2e/pull_request/four_card/_310p/test_moe_model_310p.py | 1 | test_qwen3_5_moe_tp4_fp16 |
| e2e/pull_request/four_card/context_parallel/test_accuracy.py | 3 | len(outputs_str) == len(goldens) |
| e2e/pull_request/four_card/context_parallel/test_accuracy_v2.py | 8 | len(outputs_str) == len(goldens) |
| e2e/pull_request/four_card/context_parallel/test_deepseek_v4.py | 2 | len(outputs) == len(PROMPTS_SHORT) |
| e2e/pull_request/four_card/model_runner_v2/test_deepseek_v4.py | 2 | match |
| e2e/pull_request/four_card/model_runner_v2/test_kvpp_pp.py | 1 | results[0] == results[1] |
| e2e/pull_request/four_card/model_runner_v2/test_qwen35_pp_mtp.py | 1 | response.usage.prompt_tokens > MAX_BATCHED_TOKENS; text.strip() and str(expected) in text |
| e2e/pull_request/four_card/model_runner_v2/test_qwen38_pp_mtp_prefix_cache.py | 1 | runner.cache_config.mamba_cache_mode == 'align' |
| e2e/pull_request/four_card/model_runner_v2/test_spec_decode_data_parallel.py | 1 | len(outputs) == len(PROMPTS) |
| e2e/pull_request/four_card/model_runner_v2/test_spec_pp_accuracy.py | 1 | len(outputs) == 1 |
| e2e/pull_request/four_card/rlhf/consistency/test_batch_invariant_tp4.py | 1 | len(outs_batched) == len(prompts) |
| e2e/pull_request/four_card/spec_decode/test_mtp_qwen3_next.py | 1 | match; isinstance(metric, Counter) |
| e2e/pull_request/four_card/spec_decode/test_mtp_step3p5.py | 1 | match; isinstance(metric, Counter) |
| e2e/pull_request/four_card/test_data_parallel_tp2.py | 1 | proc.returncode == 0 |
| e2e/pull_request/four_card/test_deepseek_v3_2_w8a8_pruning.py | 3 | len(outputs) == len(prompts) |
| e2e/pull_request/four_card/test_deepseek_v4.py | 2 | len(outputs) == len(example_prompts) |
| e2e/pull_request/four_card/test_graph_mode.py | 1 | comp_logprobs is not None; base_token_id == comp_token_id |
| e2e/pull_request/four_card/test_kimi_k3.py | 4 | transfer.get('remote_prefill_cached_tokens') is not None; len(outputs) == len(prompts) |
| e2e/pull_request/four_card/test_kvpp_pd.py | 1 | [generate(prompt) for prompt in PROMPTS] == expected |
| e2e/pull_request/four_card/test_minimax_m3.py | 1 | tokenizer.eos_token is not None; baseline_ids == replay_ids |
| e2e/pull_request/four_card/test_pipeline_parallel.py | 1 | test_models_pp2_dp2 |
| e2e/pull_request/four_card/test_qwen3_5.py | 2 | len(outputs) == len(example_prompts) |
| e2e/pull_request/four_card/test_qwen3_mrv2_eplb.py | 1 | committed_cycle is not None; len(outputs) == len(PROMPTS) == len(EXPECTED_ANSWER_PREFIXES) |
| e2e/pull_request/four_card/test_qwen3_next.py | 1 | test_qwen3_next_distributed_mp_graph_mode_tp4 |
| e2e/pull_request/four_card/test_qwen3_next_w8a8.py | 1 | test_qwen3_next_w8a8dynamic_distributed_mp_tp4 |
| e2e/pull_request/four_card/test_sequence_parallel_linear.py | 3 | len(outputs) == len(prompts) |
| e2e/pull_request/one_card/_310p/test_classification_310p.py | 1 | torch.allclose(hf_output, vllm_output, 0.01) |
| e2e/pull_request/one_card/_310p/test_dense_model_310p.py | 1 | test_qwen3_dense_tp1_w8a8_aclgraph |
| e2e/pull_request/one_card/_310p/test_embedding_310p.py | 3 | len(outputs) == len(queries) |
| e2e/pull_request/one_card/_310p/test_lora_310p.py | 1 | generated_texts == TEXT_EXPECTED_LORA_OUTPUT |
| e2e/pull_request/one_card/_310p/test_qwen35_dense_model_310p.py | 2 | len(prefix_cache_outputs) == len(no_prefix_cache_outputs) == len(QWEN3_5_PREFIX_MAMBA_PROMPTS) |
| e2e/pull_request/one_card/_310p/test_sampling_temp_310p.py | 1 | vllm_model.model.llm_engine.vllm_config.use_v2_model_runner |
| e2e/pull_request/one_card/_310p/test_scoring_310p.py | 3 | len(vllm_outputs) == 1 |
| e2e/pull_request/one_card/_310p/test_spec_decode_mtp_310p.py | 1 | vllm_model.model.llm_engine.vllm_config.use_v2_model_runner |
| e2e/pull_request/one_card/_310p/test_vl_model_310p.py | 1 | test_qwen3_vl_8b_tp1_fp16 |
| e2e/pull_request/one_card/aclgraph/test_device_metadata.py | 1 | calls == ['prepare', 0, 1, 2]; calls == ['prepare', *consumer_order, 2] |
| e2e/pull_request/one_card/attention_utils.py | 0 | len(self.seq_lens) == len(self.query_lens) |
| e2e/pull_request/one_card/compile/backend.py | 0 | example_inputs is not None; num_post == 0 |
| e2e/pull_request/one_card/compile/test_graphex_norm_quant_fusion.py | 1 | compiled_out.shape == (num_tokens, hidden_size); compiled_res.shape == (num_tokens, hidden_size) |
| e2e/pull_request/one_card/compile/test_graphex_qknorm_rope_fusion.py | 1 | assert_func(graph_after); found |
| e2e/pull_request/one_card/compile/test_graphex_qkvnorm_rope_fusion.py | 2 | model.rotary_emb.cos_sin_cache.dtype == dtype; torch.testing.assert_close(fused.float(), unfused.float(), atol=FUSED_VS_UNFUSED_ATOL, rtol=FUSED_VS_UNFUSED_RTOL, msg=lambda m, name=name: f'fused {name} differs from the unfused modules: {m}') |
| e2e/pull_request/one_card/compile/test_norm_quant_fusion.py | 1 | get_or_create_backend; test_rmsnorm_quant_fusion; __init__; forward; ops_in_model_before |
| e2e/pull_request/one_card/lora/test_ilama_lora.py | 1 | output1[i] == EXPECTED_LORA_OUTPUT[i] |
| e2e/pull_request/one_card/lora/test_llama32_lora.py | 1 | do_sample(llm, llama32_lora_files, tensorizer_config_dict=tensorizer_config_dict, lora_id=1) == EXPECTED_LORA_OUTPUT |
| e2e/pull_request/one_card/lora/test_lora_with_spec_decode.py | 1 | matches > int(0.9 * len(ref_outputs)) |
| e2e/pull_request/one_card/lora/test_olmoe_lora.py | 1 | _output_matches(generated_text, expected_output) |
| e2e/pull_request/one_card/lora/test_qwen35_densemodel_lora.py | 1 | generated_texts == expected_outputs |
| e2e/pull_request/one_card/lora/test_qwen3_multi_loras.py | 1 | set(llm.llm_engine.list_loras()) == set(expected) |
| e2e/pull_request/one_card/lora/test_qwen3_reranker_lora.py | 1 | get_llm; test_reranker_models_lora |
| e2e/pull_request/one_card/lora/test_qwenvl_lora.py | 3 | expected.startswith(generated); output_text.endswith(expected_text) |
| e2e/pull_request/one_card/model_runner_v2/test_deepseek_mtp.py | 1 | len(outputs) == len(prompts) |
| e2e/pull_request/one_card/model_runner_v2/test_deepseek_v2_lite_w8a8_basic.py | 2 | test_deepseek_v2_lite_eager_mode; test_deepseek_v2_lite_graph_mode |
| e2e/pull_request/one_card/model_runner_v2/test_llama3_1_8b_eagle.py | 1 | match |
| e2e/pull_request/one_card/model_runner_v2/test_qwen3_0_6B_basic.py | 2 | misses == 0 |
| e2e/pull_request/one_card/model_runner_v2/test_qwen3_8B.py | 1 | acceptance_length > 1.0 |
| e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_dflash.py | 1 | match |
| e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_draft_model.py | 1 | match |
| e2e/pull_request/one_card/model_runner_v2/test_qwen3_8b_dspark.py | 2 | len(request_ids) == max_tokens |
| e2e/pull_request/one_card/model_runner_v2/test_uva.py | 1 | test_qwen3_dense_eager_mode |
| e2e/pull_request/one_card/model_runner_v2/utils.py | 0 | isinstance(metric, counter_type); isinstance(metric, vector_type) |
| e2e/pull_request/one_card/pooling/test_classification.py | 1 | torch.allclose(hf_output, vllm_output, 0.01) |
| e2e/pull_request/one_card/pooling/test_embedding.py | 3 | test_embed_models_correctness; test_causal_embed_models_using_prefix_caching_correctness; test_bge_m3_correctness |
| e2e/pull_request/one_card/pooling/test_qwen3_embedding_mrv2.py | 1 | len(outputs) == len(queries) |
| e2e/pull_request/one_card/pooling/test_scoring.py | 6 | len(vllm_outputs) == 1 |
| e2e/pull_request/one_card/rlhf/conftest.py | 0 | server; poll_until; gen; gen_with_logprobs; ok |
| e2e/pull_request/one_card/rlhf/consistency/test_attention_fa3.py | 5 | fia_ids == fa3_ids |
| e2e/pull_request/one_card/rlhf/consistency/test_fa3_mixed_batches.py | 2 | actual_seq_lengths is offsets; len(calls) == 1 |
| e2e/pull_request/one_card/rlhf/state_transitions/npu_stream_busy.py | 0 | enqueue_npu_busy_work; npu_stream_idle |
| e2e/pull_request/one_card/rlhf/state_transitions/test_npu_device_synchronize.py | 2 | not npu_stream_idle(); npu_stream_idle() |
| e2e/pull_request/one_card/rlhf/state_transitions/test_npu_ipc_weight_transfer.py | 1 | pytest.mark.skipif(torch.npu.device_count() < 1, reason='NPU IPC weight transfer e2e test requires at least 1 NPU.'); assert_weight_update_matches_reference(dummy_signature, reference, updated_signature, reloaded_signature, case) |
| e2e/pull_request/one_card/rlhf/state_transitions/test_pause_resume.py | 2 | result.get('r') is not None; pause(url, mode='wait') == 200 |
| e2e/pull_request/one_card/rlhf/state_transitions/test_sleep_wake.py | 7 | before is not None; sleep(url, level=1) == 200 |
| e2e/pull_request/one_card/rlhf/test_trace_replay.py | 1 | output_logprobs is not None; output_ids == TRACE_TOKEN_IDS |
| e2e/pull_request/one_card/spec_decode/conftest.py | 1 | test_prompts; sampling_config; model_name; vl_model_name |
| e2e/pull_request/one_card/spec_decode/test_dflash.py | 1 | test_dflash_acceptance |
| e2e/pull_request/one_card/spec_decode/test_draft_parallel.py | 1 | match |
| e2e/pull_request/one_card/spec_decode/test_dspark.py | 2 | match |
| e2e/pull_request/one_card/spec_decode/test_eagle.py | 2 | len(acceptance_per_pos) == num_speculative_tokens |
| e2e/pull_request/one_card/spec_decode/test_extract_hidden_states.py | 1 | hidden_states.shape == expected_shape; output.kv_transfer_params is not None; list(output.prompt_token_ids) == token_prompt |
| e2e/pull_request/one_card/spec_decode/test_mtp_eagle_correctness.py | 1 | test_deepseek_mtp |
| e2e/pull_request/one_card/spec_decode/test_ngram.py | 1 | test_ngram |
| e2e/pull_request/one_card/spec_decode/test_ngram_npu.py | 3 | speculator.propose(**args, dummy_run=True).shape == (len(rows), k); speculator.propose(**args).cpu().tolist() == expected |
| e2e/pull_request/one_card/spec_decode/test_suffix.py | 1 | first_accept_tokens < last_accept_tokens; first_accept_rate < last_accept_rate |
| e2e/pull_request/one_card/spec_decode/utils.py | 0 | isinstance(metric, counter_type); isinstance(metric, vector_type) |
| e2e/pull_request/one_card/test_attention_v1_precision.py | 2 | backend_output.shape == sdpa_output.shape; backend_output.dtype == sdpa_output.dtype |
| e2e/pull_request/one_card/test_batch_job_aware_scheduler_e2e.py | 4 | test_batch_job_aware_scheduler_basic; test_batch_job_aware_scheduler_with_async_scheduling; test_batch_job_aware_scheduler_with_chunked_prefill; test_batch_job_aware_scheduler_with_custom_config |
| e2e/pull_request/one_card/test_completion_with_prompt_embeds.py | 1 | len(embeds_output) == 1 |
| e2e/pull_request/one_card/test_cpu_offloading.py | 1 | len(cold_output.prompt_token_ids) % cpu_block_size == 1; subscriber.get_new_cpu_stored_events() |
| e2e/pull_request/one_card/test_cpu_weight_offload.py | 3 | base_seq.logprobs is not None and offload_seq.logprobs is not None; len(base_seq.token_ids) == len(offload_seq.token_ids) == 3 |
| e2e/pull_request/one_card/test_ec_cpu_offload.py | 1 | loaded_output == cold_output |
| e2e/pull_request/one_card/test_ec_mooncake_fallback.py | 1 | bounce is not None; process.exitcode == 0 |
| e2e/pull_request/one_card/test_eplb_map_to_physical_npu.py | 1 | torch.testing.assert_close(physical_ids.cpu(), torch.tensor([[0, 3], [2, 1], [0, 3], [2, 1]], dtype=torch.int32)) |
| e2e/pull_request/one_card/test_fla_lazy_imports.py | 1 | result.returncode == 0 |
| e2e/pull_request/one_card/test_flash_attn_precision.py | 1 | torch.testing.assert_close(result[:12], reference, rtol=0.01, atol=0.001) |
| e2e/pull_request/one_card/test_gdn_layerwise_kv.py | 1 | attn_metadata is forward_context.attn_metadata; connector.save_kv_layer.call_count == 3 |
| e2e/pull_request/one_card/test_gdn_stable_argsort.py | 2 | actual.dtype == torch.int64; actual.device == device_mask.device |
| e2e/pull_request/one_card/test_guided_decoding.py | 7 | outputs is not None; pytest.raises(VLLMValidationError, match="already using 'xgrammar'.*'guidance'") |
| e2e/pull_request/one_card/test_gumbel_sampling.py | 23 | sampled.shape == (num_tokens,); DSparkSpeculator._sample_logits.__globals__['gumbel_sample'] is categorical_sample; torch.allclose(logits_triton.float(), logits_ref, atol=0.0001, rtol=1e-05); pytest.raises(AssertionError, match='is narrower') |
| e2e/pull_request/one_card/test_kv_pool_accuracy.py | 1 | response.json()['choices'][0]['text'] == expected |
| e2e/pull_request/one_card/test_linear_quantization.py | 5 | self.assertEqual(output.shape, (batch_size, self.output_size)); self.assertEqual(output.dtype, self.params_dtype) |
| e2e/pull_request/one_card/test_minicpm.py | 1 | test_minicpm |
| e2e/pull_request/one_card/test_minimax_m3_sparse_attn.py | 13 | actual.shape == expected.shape; topk_width == 16; _assert_topk_indices_equal_unordered(actual, expected) |
| e2e/pull_request/one_card/test_minimax_qknorm_rope_cache.py | 7 | q.shape == (0, 1024) and iq.shape == (0, 128); torch.count_nonzero(cache).item() == 0 |
| e2e/pull_request/one_card/test_mla_fp8_decode_layout_a5.py | 3 | mla_v1.get_graph_params() is params; len(params.attn_params[num_tokens]) == 1 |
| e2e/pull_request/one_card/test_mla_precision.py | 1 | backend_output.shape == sdpa_output.shape; backend_output.dtype == sdpa_output.dtype |
| e2e/pull_request/one_card/test_model_runner_v1_with_device.py | 2 | should_ubatch is False; mode == expected_mode |
| e2e/pull_request/one_card/test_multi_instance.py | 1 | outputs1; outputs2 |
| e2e/pull_request/one_card/test_multistream_overlap_shared_expert.py | 1 | test_models_with_multistream_overlap_shared_expert |
| e2e/pull_request/one_card/test_qwen3_0_6b.py | 1 | test_dense_default_full_and_piecewise_graph |
| e2e/pull_request/one_card/test_qwen3_5_0_8b.py | 2 | warm_outputs == cold_outputs |
| e2e/pull_request/one_card/test_qwen3_8b_w8a8.py | 1 | matches > int(threshold * len(ref_outputs)) |
| e2e/pull_request/one_card/test_qwen3_embedding_0_6b.py | 1 | test_embedding_full_decode_only |
| e2e/pull_request/one_card/test_sampler.py | 2 | test_qwen3_topk; test_qwen3_prompt_logprobs |
| e2e/pull_request/one_card/test_sfa_v1_precision.py | 1 | backend_output.shape == reference_output.shape; backend_output.dtype == reference_output.dtype |
| e2e/pull_request/one_card/test_simple_cpu_offload.py | 2 | success >= int(0.5 * attempts); outs and len(outs[0].outputs[0].token_ids) > 0 |
| e2e/pull_request/one_card/test_thinking_budget.py | 12 | out[0, END] == pytest.approx(1000000000.0) |
| e2e/pull_request/one_card/test_vlm.py | 4 | outputs is not None; len(outputs) == len(prompts) |
| e2e/pull_request/rlhf/weight_transfer_test_utils.py | 0 | updated_signature == reference_signature |
| e2e/pull_request/two_card/_310p/test_dense_model_310p.py | 1 | test_qwen3_dense_tp2_fp16 |
| e2e/pull_request/two_card/_310p/test_moe_model_310p.py | 1 | test_qwen3_moe_tp2_w8a8 |
| e2e/pull_request/two_card/_310p/test_vl_model_310p.py | 1 | test_qwen3_vl_8b_tp2_fp16 |
| e2e/pull_request/two_card/aclgraph/test_aclgraph_capture_replay.py | 1 | actual_capture == expected_capture |
| e2e/pull_request/two_card/lora/test_ilama_lora_tp2.py | 1 | output[i] == EXPECTED_LORA_OUTPUT[i] |
| e2e/pull_request/two_card/lora/test_llama32_lora_tp2.py | 1 | test_llama_lora_tp2 |
| e2e/pull_request/two_card/lora/test_qwen35_4b_multi_lora_mtp_aclgraph.py | 1 | content; 'mix-lora-a' in served and 'mix-lora-b' in served |
| e2e/pull_request/two_card/lora/test_qwen35_densemodel_lora_tp.py | 1 | assert_qwen35_text_lora(vllm_runner.model, qwen35_text_lora_files) |
| e2e/pull_request/two_card/lora/test_qwen3moe_lora.py | 3 | generated_texts[0].startswith(expected_lora_0); generated_texts[2].startswith(expected_lora_2) |
| e2e/pull_request/two_card/model_runner_v2/test_data_parallel.py | 2 | test_dsv2_w8a8_dp_eager_mode; test_dsv2_w8a8_dp_graph_mode |
| e2e/pull_request/two_card/model_runner_v2/test_mamba_hybrid.py | 2 | outputs[0][1] |
| e2e/pull_request/two_card/model_runner_v2/test_qwen3_5_eagle3.py | 1 | test_qwen35_9b_eagle3_acceptance_tp2 |
| e2e/pull_request/two_card/model_runner_v2/test_qwen3_6_dflash.py | 1 | test_qwen36_35b_dflash_acceptance_tp2 |
| e2e/pull_request/two_card/model_runner_v2/test_qwen3_6_dspark.py | 1 | test_qwen36_27b_dspark_acceptance_tp2 |
| e2e/pull_request/two_card/model_runner_v2/test_qwen3_6_mtp.py | 1 | relative_error <= ACCEPTANCE_LENGTH_RTOL; isinstance(metric, Counter) |
| e2e/pull_request/two_card/model_runner_v2/test_spec_decode_data_parallel.py | 1 | len(outputs) == len(PROMPTS) |
| e2e/pull_request/two_card/pooling/test_qwen3_embedding_mrv2.py | 1 | len(outputs) == len(queries) |
| e2e/pull_request/two_card/rlhf/consistency/test_moe_routing_replay.py | 1 | routed_experts.shape[0] == expected_rows; routed_experts is not None |
| e2e/pull_request/two_card/rlhf/state_transitions/test_hccl_weight_transfer.py | 1 | pytest.mark.skipif(torch.npu.device_count() < 2, reason='HCCL weight transfer e2e test requires at least 2 NPUs.'); assert_weight_update_matches_reference(dummy_signature, reference, updated_signature, reloaded_signature, case) |
| e2e/pull_request/two_card/rlhf/state_transitions/test_pause_device_idle.py | 1 | pytest.mark.skipif(not _has_pause_device_barrier(), reason='requires a vLLM with the #52914 pause device barrier (EngineCoreProc._finish_pause)'); all(await engine.engine_core.collective_rpc_async(inflate_dummy_batches)) |
| e2e/pull_request/two_card/spec_decode/test_spec_decode.py | 4 | match; isinstance(metric, Counter) |
| e2e/pull_request/two_card/spec_decode/test_spec_decode_heavy.py | 4 | len(outputs) == 1 |
| e2e/pull_request/two_card/test_activation.py | 15 | result.shape == (1, x.shape[-1] // 2); result.dtype == x.dtype; pytest.raises(ValueError, match='requires limit') |
| e2e/pull_request/two_card/test_data_parallel.py | 1 | proc.returncode == 0 |
| e2e/pull_request/two_card/test_deepseek_multistream_moe.py | 1 | test_deepseek_multistream_moe_tp2 |
| e2e/pull_request/two_card/test_disaggregated_encoder.py | 1 | test_models |
| e2e/pull_request/two_card/test_ec_mooncake_encoder_output.py | 2 | len(params) == 1 |
| e2e/pull_request/two_card/test_gemma4.py | 2 | len(outputs) == 1 |
| e2e/pull_request/two_card/test_gpt_oss_distributed.py | 1 | test_gpt_oss_distributed_tp2 |
| e2e/pull_request/two_card/test_hixl_eplb_registration.py | 5 | main_weight.untyped_storage().data_ptr() != draft_weight.untyped_storage().data_ptr(); torch.all(buffers[0][0].cpu() == 2 - rank); pytest.raises(ProcessExitedException) |
| e2e/pull_request/two_card/test_kvpp.py | 1 | [output.prompt_token_ids for output in results[0]] == [output.prompt_token_ids for output in results[1]] |
| e2e/pull_request/two_card/test_pipeline_parallel.py | 1 | test_models_pp2_tp2 |
| e2e/pull_request/two_card/test_prefix_caching.py | 1 | test_models_prefix_cache_tp2 |
| e2e/pull_request/two_card/test_qwen3_30b_a3b.py | 1 | output['choices'][0]['text'] |
| e2e/pull_request/two_card/test_qwen3_5_35b_a3b_w8a8.py | 1 | outputs[0][1] |
| e2e/pull_request/two_card/test_qwen3_6_27b_fia.py | 2 | all((stats is not None for stats in graph_stats_before + graph_stats_after)); len(outputs) == len(prompts) |
| e2e/pull_request/two_card/test_qwen3_moe_eplb.py | 1 | gt_choices[0].text == eplb_choices[0].text |
| e2e/pull_request/two_card/test_qwen3_performance.py | 1 | choices[0].text |
| e2e/pull_request/two_card/test_qwen3_vl_30b_a3b_instruct.py | 1 | len(outputs) == len(prompts) |
| e2e/pull_request/two_card/test_shared_expert_dp.py | 1 | test_deepseek_v2_lite_enable_shared_expert_dp_tp2_eager |
| e2e/pull_request/two_card/test_shared_expert_dp_graph.py | 1 | test_deepseek_v2_lite_enable_shared_expert_dp_tp2_graph |
| e2e/pull_request/utils_310p.py | 0 | get_test_image; get_test_prompts; run_vl_model_test |
| e2e/utils.py | 0 | len(embeddings_0_lst) == len(embeddings_1_lst) |

## 使用边界

AST结构、断言存在及配置参数不是运行记录。新模型变更应由真实调用链选择源测试及其参数，再分别留收集数量、skip、失败、真实退出和数值/性能原始结果。CPU mock只证明被断言的Host行为；涉及torch_npu、分布式、编译或外部权重的路径必须在目标依赖与设备上另验。本次未导入/运行上游、未编译、未调用NPU或Agent A/B；未摘选的精确参数与完整Device语义不由本矩阵补造。


## Reranker模板并非普通chat输入

固定qwen3_reranker.jinja把system作为Instruct（缺省检索说明）、query角色内容作Query、document角色内容作Document，并要求yes/no回答，末尾含assistant与空think边界。适配这条验证输入时核真实role映射、模板应用和评分接口；不能把query/document字段默认为任意OpenAI chat实现都接受，也不把该模板转授所有reranker。
