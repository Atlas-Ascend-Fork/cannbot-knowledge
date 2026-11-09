---
type: Guide
title: vLLM Ascend设备算子验证：golden、布局、有效行与容差矩阵
description: 为Ascend自有算子与Triton路径选择固定nightly数值测试，区分逐位copy、有限性、cosine、绝对/相对容差和多卡结果；保留设备skip、独立reference及未执行的性能/Operator边界。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/310p/single_node/ops/singlecard_ops/test_chunk_fwd_o_vllm_310.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_dispatch_ffn_combine.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_dispatch_ffn_combine_bf16.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_dispatch_ffn_combine_w4a8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_mtp_index_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/multicard_ops_a3/test_sfa_cache_store.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/benchmark_kda_state_copy_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_add_rms_norm_bias.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_attn_res_fwd.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_bgmv_expand.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_bgmv_shrink.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_causal_conv1d_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_chunk_gated_delta_rule_fwd_h_vllm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_compressor_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_copy_and_expand_eagle_inputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_copy_conv_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_copy_sfa_offload_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_dequant_swiglu_quant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_fused_lightning_indexer_manage.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_fused_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_fused_quant_lightning_indexer_manage.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_fused_scatter_copy_sparse_flash_attention.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_fused_sparse_attention_overlap.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_glm5next_state_gather_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_grouped_matmul_swiglu_quant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_grouped_matmul_swiglu_quant_weight_nz_tensor_list.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_inplace_partial_rotary_mul.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_kda_state_copy_integration.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_kda_state_copy_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_kv_quant_sparse_flash_attention_vllm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_lim_mtp_index_reuse.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_mla_dcp_dim0_stride.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_mla_preprocess.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_mla_strided_kv_writer_a5.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_moe_gating_top_k.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_moe_gating_top_k_hash.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_prepare_indexer_indices.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_qfa_c8_paged_layout.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_quant_lightning_indexer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_quantize_indexer_query.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_recurrent_gated_delta_rule_310.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_rms_norm_cast.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_scatter_nd_update_sk.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_sparse_flash_attention.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_sparse_flash_mla_band.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_sparse_kv_offload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_uva_view.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_apply_grammar_bitmask_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_apply_penalties_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_bad_words.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_batch_invariant_ops.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_batch_memcpy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_bincount.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_build_local_metadata_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_categorical_sample.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_chunk_gated_delta_rule.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_chunk_kda_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_clear_ssm_states.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping_fused.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping_v1.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_token_logprobs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_topk_logprobs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_copy_and_expand_dflash_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_dspark_swa_indices.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fill_logprob_token_ids_kernel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_eh_norm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_gdn_gating.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_qkvzba_split_reshape_cat.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_recurrent_kda_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_output_writeback.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_pool_key_indexer_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_tail_slot_mapping_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kda_recoverssm_npu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kimi_kda_fused_norm_gate.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_kv_block_zeroer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_l2norm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_layernorm_gated.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_lightning_attn.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_log_softmax.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_lora_linear.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_mamba_state_index.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_min_p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_mrope.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_msa_m3_index_postprocess.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_muls_add.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_mxfp_k_scale_scatter.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_num_nans.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_pcp_kv_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_penality.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_postprocess_mamba.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_postprocess_temporal_copy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_precopy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_dflash_inputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_inputs_padded.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rejection_sample.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rejection_sample_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rms_norm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_rope.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_sampling_mask.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_sparse_index_remap_triton.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_rmsnorm_mrope.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_rmsnorm_rope.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_rmsnorm_rope_vnorm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_tp_rmsnorm_rope.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_swiglu_quant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_swiglustep.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_temperature.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_trace_replay.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/test_mega_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/test_minimax_qknorm_rope_cache_performance.py
  role: evidence
created_at: '2026-11-03T05:00:51Z'
updated_at: '2026-11-04T02:58:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend设备算子验证：golden、布局、有效行与容差矩阵

## 数值验证要与算子合同配对

copy/slot/state回归多处使用atol=rtol=0以检查索引、边界和未写区域；量化、归一化与attention则使用各自的绝对/相对误差、cosine或相对RMSE，不能建立一个跨dtype/kernel的统一阈值。仅finite/非全零是更弱证据，不等于准确率通过。下表的predicate是源测试设定，未产生本次实测数值。

310P chunk_fwd_o测试将chunk=64下的常量输入解析结果、随机有限性、g=0的FP32参考以及相同chunk输出分开；常量前若干行允许相对误差0.10，而部分cosine要求>0.999。这些局部判据不能替换其他dtype/shape的合同或完整模型质量。

Attention/indexer/LIM需同时核topk集合、resident slot、LSE、layout和有效前缀。DSpark/KDA/Mamba的state copy还核未修改backing、sealed/错误布局拒绝、投机accepted前缀；Glm输出writeback检查目标storage和外围哨兵，不能只看返回Tensor。

量化/融合检查output及scale、rounding后dtype、稀疏或grouped输入的真实有效行；RMSNorm Cast测试对FP32额外输出明确比较actual.float，而不是未舍入的高精度参考。MoE/MC2多卡测试聚合all(results)，仍需各rank真实退出与通信原始结果，不能从源码聚合表达式推已成功。

Triton采样/惩罚/logprobs、grammar mask、batch invariant、RoPE、KV zeroing和状态后处理保留各自参数矩阵、skip条件及reference。源中的shape/dtype检查或benchmark入口不能证明kernel性能优于基线；性能测试需要固定环境/负载与同步测量。

这些是验证选择知识，不是完整Operator提取；Device模板/平台CANN闭包及NPU数值/性能执行仍未完成，见[测试证据层次](vllm_ascend_test_evidence_selection.md)。

## 按断言职责选择源测试

下表是静态语法定位材料：从固定源码的AST遍历函数、assert与assert*/raises调用，保留test*函数计数和摘选谓词，未逐行完成fixture、callee与每条断言的语义复核。原自动聚类的“数值比较”“掩码/有效行”等宽标签不再作为覆盖结论列出；一般相等断言、mock调用或helper名称不能独立证明对应设备语义。摘选谓词帮助回源，不是完整用例正文。名称计数不是pytest实际收集量，fixture命名与参数化实例须另核。参数fixture、mock、skip条件和设备前提仍需打开对应固定来源核实；没有执行或证明任何用例通过。文件无断言时列其fixture/工具接口，不冒充独立数值检查。

| 固定测试文件 | AST test*函数数（非收集量） | 可定位的谓词或失败约束 |
| --- | --- | --- |
| e2e/nightly/310p/single_node/ops/singlecard_ops/test_chunk_fwd_o_vllm_310.py | 4 | torch.isnan(oc).sum() == 0 |
| e2e/nightly/single_node/ops/multicard_ops_a3/test_dispatch_ffn_combine.py | 1 | all(results) |
| e2e/nightly/single_node/ops/multicard_ops_a3/test_dispatch_ffn_combine_bf16.py | 1 | all(results) |
| e2e/nightly/single_node/ops/multicard_ops_a3/test_dispatch_ffn_combine_w4a8.py | 1 | all(results) |
| e2e/nightly/single_node/ops/multicard_ops_a3/test_mtp_index_cache.py | 1 | all((process.exitcode == 0 for process in processes)) |
| e2e/nightly/single_node/ops/multicard_ops_a3/test_sfa_cache_store.py | 4 | cache.data_ptr() == ptr; torch.testing.assert_close(cache.cpu(), reference, rtol=0, atol=0); pytest.raises(RuntimeError) |
| e2e/nightly/single_node/ops/singlecard_ops/benchmark_kda_state_copy_triton.py | 0 | torch.testing.assert_close(actual, torch.full_like(actual, expected), rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/test_add_rms_norm_bias.py | 4 | torch.count_nonzero((unbiased_y.float() + beta.float()).to(dtype)) == 0; pytest.raises(RuntimeError) |
| e2e/nightly/single_node/ops/singlecard_ops/test_attn_res_fwd.py | 1 | torch.testing.assert_close(raw.cpu(), expected_raw, rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/test_bgmv_expand.py | 1 | torch.testing.assert_close(y_out_npu.cpu(), y_out.cpu(), atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL) |
| e2e/nightly/single_node/ops/singlecard_ops/test_bgmv_shrink.py | 1 | torch.testing.assert_close(y_npu.cpu(), y.cpu(), atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL) |
| e2e/nightly/single_node/ops/singlecard_ops/test_causal_conv1d_310.py | 2 | torch.testing.assert_close(y_ref, y_cal, rtol=0.003, atol=0.01, equal_nan=True) |
| e2e/nightly/single_node/ops/singlecard_ops/test_chunk_gated_delta_rule_fwd_h_vllm.py | 2 | final_state is None; len(reference) == len(actual) == len(FWD_H_OUTPUT_NAMES) |
| e2e/nightly/single_node/ops/singlecard_ops/test_compressor_metadata.py | 2 | case.num_rows is not None |
| e2e/nightly/single_node/ops/singlecard_ops/test_copy_and_expand_eagle_inputs.py | 5 | torch.testing.assert_close(n_ids, g_ids_t, atol=0, rtol=0, msg='out_input_ids mismatch') |
| e2e/nightly/single_node/ops/singlecard_ops/test_copy_conv_state.py | 4 | torch.testing.assert_close(backing.cpu(), expected_storage, atol=0, rtol=0); torch.count_nonzero(packed[1:4]).item() == 0 |
| e2e/nightly/single_node/ops/singlecard_ops/test_copy_sfa_offload_metadata.py | 22 | metadata.fused_copy_sfa_enabled is False; metadata.copy_sfa_prefill_pool_slots.cpu().tolist() == [1]; pytest.raises(RuntimeError, match='must be CPU tensors') |
| e2e/nightly/single_node/ops/singlecard_ops/test_dequant_swiglu_quant.py | 1 | torch.testing.assert_close(output.cpu(), output_golden.cpu(), atol=1, rtol=0.1) |
| e2e/nightly/single_node/ops/singlecard_ops/test_fused_lightning_indexer_manage.py | 13 | result is None; len(q_values) == len(states); pytest.raises(RuntimeError, match='dequant scales must be fp32'); pytest.raises(RuntimeError, match='miss outputs must be'); pytest.raises(RuntimeError, match='must be contiguous'); pytest.raises(RuntimeError) |
| e2e/nightly/single_node/ops/singlecard_ops/test_fused_moe.py | 2 | combined_output.shape == (m, k); torch.testing.assert_close(combined_output, torch_output, atol=0.04, rtol=1) |
| e2e/nightly/single_node/ops/singlecard_ops/test_fused_quant_lightning_indexer_manage.py | 13 | result is None; len(q_values) == len(states); pytest.raises(RuntimeError, match='dequant scales must be fp16'); pytest.raises(RuntimeError, match='miss outputs must be'); pytest.raises(RuntimeError, match='must be contiguous'); pytest.raises(RuntimeError, match='B <= T <= 14B') |
| e2e/nightly/single_node/ops/singlecard_ops/test_fused_scatter_copy_sparse_flash_attention.py | 5 | torch.testing.assert_close(hbm_kpe.cpu().view_as(expected_hbm_kpe_cpu), expected_hbm_kpe_cpu, rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/test_fused_sparse_attention_overlap.py | 1 | actual.shape == case.reference_output.shape; actual.dtype == case.reference_output.dtype |
| e2e/nightly/single_node/ops/singlecard_ops/test_glm5next_state_gather_npu.py | 2 | actual.dtype == dtype and actual.device == state.device; torch.testing.assert_close(actual.cpu(), expected, rtol=0, atol=0, equal_nan=True) |
| e2e/nightly/single_node/ops/singlecard_ops/test_grouped_matmul_swiglu_quant.py | 1 | torch.testing.assert_close(output_golden, output.cpu(), atol=1, rtol=0.005) |
| e2e/nightly/single_node/ops/singlecard_ops/test_grouped_matmul_swiglu_quant_weight_nz_tensor_list.py | 1 | torch.testing.assert_close(output_npu_valid.cpu(), output_cpu, atol=1, rtol=2 ** (-13)) |
| e2e/nightly/single_node/ops/singlecard_ops/test_inplace_partial_rotary_mul.py | 1 | torch.testing.assert_close(out_neg.cpu(), ref_neg.to(dtype), atol=atol, rtol=rtol) |
| e2e/nightly/single_node/ops/singlecard_ops/test_kda_state_copy_integration.py | 17 | all((plan._compiled is plans[0]._compiled for plan in plans)); len(plan._compiled) == 4; pytest.raises(RuntimeError, match='sealed'); pytest.raises(RuntimeError, match='bound'); pytest.raises(RuntimeError, match='scheduler'); pytest.raises(RuntimeError, match='layout'); pytest.raises(RuntimeError, match='flags'); pytest.raises(RuntimeError, match='prepared worker layer') |
| e2e/nightly/single_node/ops/singlecard_ops/test_kda_state_copy_triton.py | 6 | state.stride(0) * state.element_size() > 2 ** 32; torch.all(backing[0::3] == -23) and torch.all(backing[2::3] == -23); pytest.raises(RuntimeError, match='dense inner') |
| e2e/nightly/single_node/ops/singlecard_ops/test_kv_quant_sparse_flash_attention_vllm.py | 7 | output.shape == (1, 1, 64, 512); tuple((tensor.data_ptr() for tensor in actual)) == pointers; output.dtype == torch.bfloat16; pytest.raises(RuntimeError) |
| e2e/nightly/single_node/ops/singlecard_ops/test_lim_mtp_index_reuse.py | 4 | impl.lim_reuse_topk_misses.count_nonzero().item() == 0 |
| e2e/nightly/single_node/ops/singlecard_ops/test_mla_dcp_dim0_stride.py | 2 | output.shape == (tokens, heads, head_dim); key.storage_offset() > 0 and key_rope.storage_offset() > 0; lse.shape == (tokens, heads, 1) and lse.dtype == torch.float32 |
| e2e/nightly/single_node/ops/singlecard_ops/test_mla_preprocess.py | 6 | _assert_dim0_holes_untouched(noncontiguous[4], stride_factor, ctkv_fill); (holes == fill_value).all() |
| e2e/nightly/single_node/ops/singlecard_ops/test_mla_strided_kv_writer_a5.py | 2 | writer.supports_strided_mla_writer(); tuple((tensor.data_ptr() for tensor in workspace)) == addresses |
| e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py | 5 | y.shape == (*batch_shape, shape[-1]); post.shape == (*batch_shape, HC_MULT) |
| e2e/nightly/single_node/ops/singlecard_ops/test_npu_moe_gating_top_k.py | 1 | numpy.allclose(y.cpu().numpy(), y_npu.cpu().numpy(), rtol=RTOL_TOLERANCE, atol=ATOL_TOLERANCE) |
| e2e/nightly/single_node/ops/singlecard_ops/test_npu_moe_gating_top_k_hash.py | 1 | torch.testing.assert_close(actual_ids.cpu(), expected_ids, rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/test_prepare_indexer_indices.py | 6 | actual.data_ptr() == output.data_ptr(); torch.testing.assert_close(actual.cpu(), reference(selected.cpu(), positions.cpu(), compress_ratio), rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/test_qfa_c8_paged_layout.py | 1 | (backing[:128] == 91).all() and (backing[-256:] == 91).all() |
| e2e/nightly/single_node/ops/singlecard_ops/test_quant_lightning_indexer.py | 3 | contiguous_indices.shape == (1, num_heads_k, topk); not key_strided.is_contiguous(); key_strided.stride(0) == 2 * block_size * num_heads_k * head_dim |
| e2e/nightly/single_node/ops/singlecard_ops/test_quantize_indexer_query.py | 4 | tuple((output.data_ptr() for output in actual)) == pointers; torch.testing.assert_close(scale.cpu(), expected_scale.cpu(), rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/test_recurrent_gated_delta_rule_310.py | 1 | torch.testing.assert_close(out.to(torch.float32).cpu(), out_golden.to(torch.float32).cpu(), rtol=0.003, atol=0.01, equal_nan=True) |
| e2e/nightly/single_node/ops/singlecard_ops/test_rms_norm_cast.py | 2 | torch.testing.assert_close(actual, expected, rtol=rtol, atol=atol) |
| e2e/nightly/single_node/ops/singlecard_ops/test_scatter_nd_update_sk.py | 5 | DeviceOperator.scatter_cache(cache.view(-1, key.shape[-1]), slots.view(-1, 1), key) is None; cache.data_ptr() == pointer; cache.is_contiguous() == (not row_gap) |
| e2e/nightly/single_node/ops/singlecard_ops/test_sparse_flash_attention.py | 1 | torch.count_nonzero(output) == 0 |
| e2e/nightly/single_node/ops/singlecard_ops/test_sparse_flash_mla_band.py | 2 | output.shape == query.shape; torch.testing.assert_close(output, torch.full_like(output, 0.5)); pytest.raises(RuntimeError, match='TND band ori_topk_length shape must be'); pytest.raises(RuntimeError, match='(?is)ori_?topk_?length.*shape') |
| e2e/nightly/single_node/ops/singlecard_ops/test_sparse_kv_offload.py | 7 | bf16_view.dtype == torch.bfloat16; bf16_view.data_ptr() == bf16.data_ptr(); sparse_kv_ops.sparse_kv_warmup_lru_resident_threads(1) == 1 |
| e2e/nightly/single_node/ops/singlecard_ops/test_uva_view.py | 11 | view.shape == cpu.shape; view is not None; view.device.type == 'npu'; pytest.raises(RuntimeError, match='CPU tensor') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_apply_grammar_bitmask_triton.py | 1 | torch.equal(actual.cpu(), expected); pytest.mark.skipif(get_ascend_device_type() not in (AscendDeviceType.A2, AscendDeviceType.A3, AscendDeviceType.A5), reason='Requires Ascend A2/A3/A5') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_apply_penalties_triton.py | 1 | torch.allclose(logits_ascend.float(), logits_v1.float(), atol=atol, rtol=rtol) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_bad_words.py | 4 | not torch.allclose(logits_before, logits_after) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_batch_invariant_ops.py | 13 | actual.shape == expected.shape; result is out; actual.dtype == expected.dtype |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_batch_memcpy.py | 1 | torch.testing.assert_close(src_tensors_list[i], dst_tensors_list[i], rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_bincount.py | 1 | torch.equal(prompt_bin_mask, ref_prompt_bin_mask); torch.equal(output_bin_counts, ref_output_bin_counts) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_build_local_metadata_triton.py | 2 | trt_sp is not None and ref_sp is not None; ref_sl[17].item() == 0 |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_categorical_sample.py | 13 | sampled.dtype == torch.int64; sampled.shape == (num_tokens,); pytest.raises(NotImplementedError, match='FP64 categorical sampling is not supported on NPU') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_chunk_gated_delta_rule.py | 2 | core_attn_out_non_spec.shape == (1, 17, 8, 128); final_state is not None; chunk_metadata.cu_seqlens_host == (0, 1, 9, 17) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_chunk_kda_npu.py | 1 | assert_close('o', ref_o, tri_o, NPU_RMSE_RATIO_O) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_clear_ssm_states.py | 1 | torch.testing.assert_close(ssm_states, ssm_states_ref) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping.py | 2 | result.data_ptr() == out.data_ptr(); torch.testing.assert_close(slot_mappings.cpu(), ref_slot_mappings) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping_fused.py | 2 | len(compile_events) == first_count |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_slot_mapping_v1.py | 2 | torch.testing.assert_close(slot_mapping.cpu(), torch.tensor(expected, dtype=torch.int32)) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_token_logprobs.py | 5 | token_ids.stride(0) == 0; torch.allclose(logprobs_triton, logprobs_ref, atol=0.0001, rtol=1e-05) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_compute_topk_logprobs.py | 1 | torch.allclose(triton_output.logprobs, ref_logprobs, rtol=0.0001, atol=0.0001) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_copy_and_expand_dflash_dspark.py | 2 | out_query_positions.cpu().tolist() == expected_positions |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_dspark_swa_indices.py | 11 | out_slots.shape[0] == T_active; sliced_table.stride(0) == max_num_blocks + 16 != sliced_table.shape[1]; torch.testing.assert_close(out_slots, ref_slots) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_fill_logprob_token_ids_kernel.py | 2 | torch.testing.assert_close(out_token_ids.cpu(), expected_ids, rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_eh_norm.py | 1 | actual.shape == (num_tokens, 2 * hidden_size); actual.dtype == dtype |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_gdn_gating.py | 1 | torch.testing.assert_close(triton_g.to(torch.float32).cpu(), ref_g.to(torch.float32).cpu(), rtol=0.01, atol=0.01, equal_nan=True) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_qkvzba_split_reshape_cat.py | 1 | torch.testing.assert_close(y_ref, y_cal, rtol=0, atol=0, equal_nan=True) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_fused_recurrent_kda_npu.py | 3 | torch.all(state_buf_tri[0] == 0) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_output_writeback.py | 2 | torch.testing.assert_close(storage[:17].cpu(), torch.full((17,), -7, dtype=dtype), rtol=0, atol=0); torch.testing.assert_close(output.cpu(), expected, rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_pool_key_indexer_triton.py | 2 | result.shape == (0, 1, OUTPUT_WIDTH); result.data_ptr() == output_buffer.data_ptr(); result.dtype == torch.int32 |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_glm5next_tail_slot_mapping_triton.py | 2 | obj.slot_mapping.gpu.cpu().tolist() == [-1] * 5 |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_kda_recoverssm_npu.py | 12 | actual.shape == expected.shape; context.conv_dim_stride is None; output.shape == q.shape; pytest.raises(AssertionError, match='fewer than 99%'); pytest.raises(AssertionError, match='maximum absolute error'); pytest.raises(ValueError, match='at least one layer') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_kimi_kda_fused_norm_gate.py | 5 | residual_out.dtype == expected_residual_dtype; actual is out; torch.testing.assert_close(actual, expected.to(dtype), rtol=0.002, atol=0.002) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_kv_block_zeroer.py | 1 | pytest.mark.skipif(get_ascend_device_type() not in (AscendDeviceType.A2, AscendDeviceType.A3, AscendDeviceType.A5), reason='Requires Ascend A2/A3/A5'); torch.equal(cache, expected) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_l2norm.py | 1 | torch.allclose(tri, ref, rtol=rtol, atol=atol) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_layernorm_gated.py | 2 | actual.shape == x.shape; actual.data_ptr() == out.data_ptr(); actual.dtype == dtype; pytest.raises(AssertionError) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_lightning_attn.py | 13 | output.shape[0] == 1; kv_triton.shape == (b, h, (n + BLOCK_SIZE - 1) // BLOCK_SIZE + 1, d, e) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_log_softmax.py | 1 | torch.allclose(triton_output, ref_output, rtol=0.001, atol=0.001) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_lora_linear.py | 1 | torch.testing.assert_close(y[inactive], y_initial[inactive], rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_mamba_state_index.py | 3 | torch.testing.assert_close(state[state_idx], source[source_idx].to(state.dtype), rtol=0, atol=0); torch.testing.assert_close(storage_cpu[padding_start:padding_end], torch.full((padding,), -1.0), rtol=0, atol=0); torch.testing.assert_close(gathered, expected_gather, rtol=0, atol=0); pytest.raises(ValueError, match='at least one row'); pytest.raises(ValueError, match='stride\\(0\\)') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_min_p.py | 1 | torch.allclose(valid_triton_logits, valid_ref_logits, rtol=0.0001, atol=0.0001) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_mrope.py | 1 | torch.testing.assert_close(q_trt.view(q_gold.size()), q_gold, atol=atol, rtol=rtol) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_msa_m3_index_postprocess.py | 5 | indices.shape == (*shape[:2], 16); counts.shape == shape[:2]; pytest.raises(ValueError, match=message) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_muls_add.py | 1 | out_triton.shape == out_ref.shape; out_triton.dtype == out_ref.dtype |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_mxfp_k_scale_scatter.py | 11 | torch.testing.assert_close(raw.cpu(), expected, rtol=0, atol=0); len(compile_events) == first_count; pytest.raises(ValueError, match=message) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_num_nans.py | 2 | expected.tolist() == [0, num_injected] |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_pcp_kv_cache.py | 4 | packed.dtype == torch.int8; slots.data_ptr() == slot_storage.data_ptr() + offset * slots.element_size(); torch.all(key == 3).item() |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_penality.py | 2 | torch.allclose(logits_triton, logits_pytorch_result, atol=atol, rtol=rtol) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_postprocess_mamba.py | 1 | input_batch.mamba_state_idx_cpu is not None; torch.testing.assert_close(gpu_ctx.num_accepted_tokens_out[:len(req_ids)], expected_accepted) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_postprocess_temporal_copy.py | 4 | pytest.mark.skipif(not torch.npu.is_available(), reason='NPU required'); torch.equal(destination.cpu(), expected) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_precopy.py | 1 | torch.testing.assert_close(convs[layer], conv_ref[layer], rtol=0, atol=0) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_dflash_inputs.py | 3 | len(position_starts) == num_reqs |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_prepare_inputs_padded.py | 1 | torch.testing.assert_close(out_tri, out_ref) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_rejection_sample.py | 9 | output_triton[0].tolist() == [5, 6, 7, 21] |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_rejection_sample_v2.py | 9 | (num_sampled == 2).float().mean().item() > 0.9 |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_rms_norm.py | 2 | actual.shape == expected.shape; actual.dtype == expected.dtype; pytest.raises(NotImplementedError, match='dim > 2048 not supported') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_rope.py | 4 | actual_query.dtype == torch.float8_e4m3fn; key is not None; actual_key.dtype == torch.float8_e4m3fn |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_sampling_mask.py | 3 | logits.shape == (num_reqs, vocab_size); logits.stride(1) == 2; result == expected |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_sparse_index_remap_triton.py | 2 | torch.testing.assert_close(got, _torch_reference(indices, dcp_size, rank, interleave_size), rtol=0, atol=0, msg=f'mismatch for dcp_size={dcp_size}, interleave_size={interleave_size}, topk={topk}, rank={rank}') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_rmsnorm_mrope.py | 1 | torch.testing.assert_close(real_q.cpu(), golden_q.cpu(), atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_rmsnorm_rope.py | 2 | torch.testing.assert_close(q.to(torch.float32).cpu(), q_gold, atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_rmsnorm_rope_vnorm.py | 2 | torch.testing.assert_close(q.to(torch.float32).cpu(), q_gold, atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_split_qkv_tp_rmsnorm_rope.py | 1 | torch.testing.assert_close(q_fused.to(torch.float32), q_ref.to(torch.float32), atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_swiglu_quant.py | 4 | actual.shape == swiglu_ref.shape; actual.dtype == torch.int8; pytest.raises(ValueError, match='group_list_type must be 0 or 1'); pytest.raises(ValueError, match='group_list dtype must be torch.int32 or torch.int64') |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_swiglustep.py | 3 | out_triton.shape == out_ref.shape; out_triton.dtype == out_ref.dtype |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_temperature.py | 1 | torch.allclose(logits_triton, logits_ref, atol=0.0001, rtol=1e-05) |
| e2e/nightly/single_node/ops/singlecard_ops/triton/test_trace_replay.py | 4 | upstream_trace_replay.apply_trace_tokens is apply_trace_tokens; sampled.numel() == 0 |
| e2e/nightly/single_node/ops/test_mega_moe.py | 0 | torch.testing.assert_close(captured[0], expected, rtol=0, atol=0) |
| e2e/nightly/single_node/ops/test_minimax_qknorm_rope_cache_performance.py | 1 | spec is not None and spec.loader is not None; next((p for p in runtime_kernel.params if p.name == 'NUM_SLOTS')).is_constexpr is False |

## 使用边界

AST结构、断言存在及配置参数不是运行记录。新模型变更应由真实调用链选择源测试及其参数，再分别留收集数量、skip、失败、真实退出和数值/性能原始结果。CPU mock只证明被断言的Host行为；涉及torch_npu、分布式、编译或外部权重的路径必须在目标依赖与设备上另验。本次未导入/运行上游、未编译、未调用NPU或Agent A/B；未摘选的精确参数与完整Device语义不由本矩阵补造。
