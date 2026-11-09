---
type: Guide
title: vLLM Ascend Attention与量化回归：数值、布局和调用分支测试矩阵
description: 为Attention、MoE、量化和kernel warmup变更选择固定UT，定位shape/dtype、缓存别名、PCP/DCP元数据、注册分派及异常门禁；只记录断言合同，不将mock或测试存在提升为NPU结果。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_fa3.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_attention_v1.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_decoder_replay_swa_indices.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_v1.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_v41.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsa_v41_request_counts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsv4_block_geometry.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_dsv4_compressor_metadata_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_fia_non_pa_inputs.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_flash_attn.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_flashmla_prolog_v3_cpu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_gqa_dcp_split.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_cp_mask_slice.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_cp_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_cp_workspace_owner.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_fp8_decode_layout.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_nope_chunked_gather.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_output_gate.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_pcp_dcp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_prefill_merge.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_prolog_v3_route.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_prolog_v3_tile_size_cpu.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_mla_v1.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_contract.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_cp_precision.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_nope_forward.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_nope_metadata.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sfa_v1.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_sparse_flash_mla.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/test_deepseek_v4.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/test_offloader.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/helpers.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_early_kernel_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_indexer_triton_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_kernel_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_nz_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_penalties_triton_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_rejection_sampler_triton_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/warmup/test_rms_triton_warmup.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_activation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_aurora_tiling_keys.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_comm_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_eplb_v2_recording.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_fla_lazy_imports.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_force_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_fused_mc2_sleep_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_fused_moe.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gate_linear.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_kda_gate.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_kimi_kda.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_layernorm.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_linear.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_mla.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_mla_weight_processing.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_moe_comm_method.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_moe_runtime_args.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_moe_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_packaged_attention.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_pcp_kv_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_prepare_finalize.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_register_custom_ops.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_rms_block_sizing.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_rope_tile_sizing.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_routed_experts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_shared_mxfp_activation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_token_dispatcher.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_vocab_parallel_embedding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/configs/test_fp8_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/configs/test_modelslim_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/conftest_quantization.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/kv_cache/turboquant/conftest.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/test_moe_logical_experts.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/test_registry.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w8a8/test_fp8_block.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w8a8/test_w8a8_dynamic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w8a8/test_w8a8_mxfp8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w8a8/test_w8a8_static.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/test_quant_parser.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/test_utils.py
  role: evidence
created_at: '2026-11-03T04:54:55Z'
updated_at: '2026-11-04T02:58:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Attention与量化回归：数值、布局和调用分支测试矩阵

## 适配与优化应覆盖什么

Attention变更同时核请求计数、逻辑/物理KV几何、有效行和持久workspace。所读断言明确区分CPU seq_lens镜像与NPU视图、CrossAttention和部分DSpark模型的分支；共享buffer只构造一次且不进入state_dict。PCP写缓存使用gather后的key/value/slots，并在成功及注入异常后恢复元数据；不能以单条最终output比较替代该生命周期。

DSA/QLI/压缩缓存需核按cache group和substep复用、固定地址、capture bucket与actual请求数。测试覆盖超capacity、超过vision token上限及不允许的并发选项等显式拒绝。V4.1请求数测试分开MRv2的真实行与MRv1 legacy padding；DCP的CURRENT/HISTORY/FULL域、LSE合并、mask切片及O-proj所有权也分别检查。

FIA/FlashMLA路径不能只比数值：非PA输入的contiguity/stride、FP8 decode的token-major view、Prolog的cache writer和profile workspace、SFA零拷贝block规格与prepared缓存都有独立断言。FA3依赖不存在会skip；所读reference比较不代表本次已获得FA3数值结果。

MoE测试核routing IDs/weights、shared-expert overlap顺序、typed量化/activation参数、输入释放、EPLB专家数量及通信状态的sleep/refresh边界；不要用单一gmm结果代表完整dispatch/combine。量化配置覆盖recipe和前缀匹配、逻辑/物理专家、INT8/FP8/MXFP尺度及可重入处理，alias/storage/dtype不可只靠shape替代。

Warmup测试检查开关、一次性后台线程、join timeout、token-count/block选择和本地vocab；Mock调用一次或未调用是Host控制流证据，不是kernel编译成功或性能提升。

相关实现合同见[FlashMLA](../integration/vllm_ascend_flashmla_dcp_execution_contract.md)、[MoE GMM](../integration/vllm_ascend_gmm_situ_quant_host_contract.md)、[KV格式](../integration/vllm_ascend_kv_quant_format_contract.md)。

## 按断言职责选择源测试

下表是静态语法定位材料：从固定源码的AST遍历函数、assert与assert*/raises调用，保留test*函数计数和摘选谓词，未逐行完成fixture、callee与每条断言的语义复核。原自动聚类的“数值比较”“掩码/有效行”等宽标签不再作为覆盖结论列出；一般相等断言、mock调用或helper名称不能独立证明对应设备语义。摘选谓词帮助回源，不是完整用例正文。名称计数不是pytest实际收集量，fixture命名与参数化实例须另核。参数fixture、mock、skip条件和设备前提仍需打开对应固定来源核实；没有执行或证明任何用例通过。文件无断言时列其fixture/工具接口，不冒充独立数值检查。

| 固定测试文件 | AST test*函数数（非收集量） | 可定位的谓词或失败约束 |
| --- | --- | --- |
| ut/attention/test_attention_fa3.py | 1 | torch.testing.assert_close(out_out.cpu(), ref_out.cpu(), rtol=rtol, atol=atol) |
| ut/attention/test_attention_utils.py | 11 | get_flashmla_ops() is None; get_flashmla_ops() == (attention_op, metadata_op); import_module.assert_called_once_with('cann_ops_transformer.ops'); pytest.raises(ModuleNotFoundError, match='internal_dependency') |
| ut/attention/test_attention_v1.py | 41 | output.shape == (10, 8 * 64); metadata.slot_mapping is expanded_slot_mapping; metadata.pcp_local_num_input_tokens == 4; reshape_and_cache.assert_called_once(); self.assertRaisesRegex(ValueError, 'corresponding quantized weights are required'); pytest.raises(RuntimeError, match='cache write failed') |
| ut/attention/test_decoder_replay_swa_indices.py | 1 | torch.testing.assert_close(lengths, torch.tensor(expected_lengths, dtype=torch.int32).reshape(-1, 1)) |
| ut/attention/test_dsa_cp.py | 6 | prepared.hidden_restore_idx.shape[0] == expected_num_tokens; layer_metadata.swa is swa_metadata; events[-1] == 'local'; 'save' not in events; pytest.raises(RuntimeError, match='failed') |
| ut/attention/test_dsa_v1.py | 61 | indices.shape == (8, 1, 6); builder.dspark_swa_indices_buffer is not None; lengths.tolist() == [1, 2, 5, 4, 4, 4, 2, 2]; events == ['wait', 'record', 'attention']; pytest.raises(ValueError, match='exceeds vision_max_n_token'); pytest.raises(ValueError, match='active=17, capacity=16'); pytest.raises(RuntimeError, match='Prepared DSA caches require single-stream attention'); pytest.raises(RuntimeError, match='injected failure'); pytest.raises(ValueError, match=f'capacity \\({decode_capacity}\\) must cover local tokens \\({oversized_tokens}\\)'); pytest.raises(ValueError, match='cannot be enabled at the same time') |
| ut/attention/test_dsa_v41.py | 7 | result.shape == hidden_states.shape; impl.forward(attn, None, torch.empty(5, 2), output) is output; len(calls) == int(should_project) |
| ut/attention/test_dsa_v41_request_counts.py | 4 | _request_counts(common, num_reqs=2) == (0, 0, 1, 24) |
| ut/attention/test_dsv4_block_geometry.py | 1 | result is expected; args[5] == 128 |
| ut/attention/test_dsv4_compressor_metadata_cache.py | 1 | first is reused; metadata_op.call_count == 4 |
| ut/attention/test_fia_non_pa_inputs.py | 7 | torch.testing.assert_close(actual.reshape(original.shape), original); block_table is None; seq_lens == ([5] if cross_attention else [3]); selected_fia.assert_called_once() |
| ut/attention/test_flash_attn.py | 13 | metadata.block_tables.shape == (2, 8); result.seq_lens_gpu.data_ptr() == common.seq_lens.data_ptr(); AscendAttentionBackend.get_supported_kernel_block_sizes() == [128]; pytest.raises(AssertionError) |
| ut/attention/test_flashmla_prolog_v3_cpu.py | 4 | consumed.ql_nope.shape == (tokens, heads * (8 if dcp else 1), 512); impl.forward('mla', torch.zeros(tokens, 16), history, metadata, output) is output; consumed.q_pe.shape == (tokens, heads * (8 if dcp else 1), 64); impl._run_prolog_v3.assert_called_once(); pytest.raises(RuntimeError, match='scheduled token rows') |
| ut/attention/test_gqa_dcp_split.py | 13 | lse.shape == (num_reqs, 8, 1); seen['key'] is key and seen['value'] is value; decode.cp_history_seq_len == expected; events == [CPKVScope.HISTORY, ('wait', 'history_ready'), CPKVScope.CURRENT, 'a2a', ('wait', 'current_done'), 'merge'] |
| ut/attention/test_mla_cp.py | 12 | gathered_nope.shape == (1, 4, 3); AscendMlaDCPMetadataBuilder.decode_metadata_cls is AscendMLADCPDecodeMetadata; impl.need_to_return_lse_for_decode == (dcp_size > 1); events == [CPKVScope.HISTORY, 'history_ready', ('attn_wait', 'ready'), CPKVScope.CURRENT, 'attn_done', 'history_collective', ('main_wait', 'done'), 'merge'] |
| ut/attention/test_mla_cp_mask_slice.py | 1 | result.dcp_mtp_attn_mask is None; result.cp_seq_len == [12 if dcp_rank == 0 else 8] |
| ut/attention/test_mla_cp_precision.py | 1 | torch.testing.assert_close(output, reference, rtol=1e-10, atol=1e-10) |
| ut/attention/test_mla_cp_workspace_owner.py | 1 | selected.workspaces[12] is workspace; allocate.call_count == 1 |
| ut/attention/test_mla_fp8_decode_layout.py | 3 | params[14].shape == shape; weight is impl.W_UV; projection_op.call_args.kwargs == expected_kwargs; projection_op.assert_called_once() |
| ut/attention/test_mla_nope_chunked_gather.py | 2 | captured['key'].shape == (CHUNK_TOKS, 1, LATENT_KV_DIM); captured['pe_cache'] is cache_k_pe; captured['value'].shape == (CHUNK_TOKS, 1, 64) |
| ut/attention/test_mla_output_gate.py | 1 | result is output; torch.testing.assert_close(result, expected); impl.g_proj.assert_called_once() |
| ut/attention/test_mla_pcp_dcp.py | 13 | actual_nope.shape[1] == num_heads; args[0] is out and args[1] is lse; args[2:] == (tp_size, 1, 'tp', 'pcp'); impl.tp_group.all_gather.assert_called_once(); pytest.raises(ValueError, match='workspace_size=32768, num_prefills_with_context=32, block_size=2048, minimum_workspace_size=65536') |
| ut/attention/test_mla_prefill_merge.py | 6 | torch.testing.assert_close(actual.double().reshape(15, 8), expected, atol=2e-05, rtol=0.0001) |
| ut/attention/test_mla_prolog_v3_route.py | 41 | prepared['weight_dq'].shape == (4, 4); prepared is not None; prepared['weight_dkv_kr'].shape == (4, 6); impl._prepare_prolog_v3_weights.assert_called_once(); pytest.raises(RuntimeError, match='prepared before KV cache sizing'); pytest.raises(RuntimeError, match='exceeds the profiled workspace') |
| ut/attention/test_mla_prolog_v3_tile_size_cpu.py | 1 | cache[0].shape == (1, page_size, 1, 512); run(impl, hidden_states, object(), object(), cache, slots, quantize_query=True) is outputs; passed['tile_size'] == 128; operator.assert_called_once() |
| ut/attention/test_mla_v1.py | 102 | result.dtype == impl.W_UV.dtype; (x.stride(), x.storage_offset(), x.data_ptr()) == (original_stride, original_offset, original_ptr); fused.call_count == int(use_fused); impl.layerwise_kv_cache_hook.wait_for_layer.assert_called_once_with('target'); self.assertRaises(NotImplementedError) |
| ut/attention/test_sfa_contract.py | 5 | len(matches) == 1; pytest.raises(ValueError, match='hot budget'); pytest.raises(ValueError, match='TopK=2048') |
| ut/attention/test_sfa_cp_precision.py | 7 | merged.shape == expected; actual is expected; torch.testing.assert_close(rank0, torch.tensor([[0, 1, 2, 3, -1, -1, -1, -1]], dtype=torch.int32)); fused_a2a.assert_called_once_with(output, lse, 2, 1, 'dcp:0') |
| ut/attention/test_sfa_nope_forward.py | 6 | indices.dtype == slot_dtype; scatter.call_args.args[0].data_ptr() == cache.data_ptr(); result == (None, None); scatter.assert_called_once(); pytest.raises(RuntimeError, match='view size is not compatible') |
| ut/attention/test_sfa_nope_metadata.py | 19 | builder.nope_states[4].block_table_buffer.shape[0] == 32; local is not None; metadata.num_actual_tokens == 3 and local.num_actual_tokens == 1; rotary.assert_called_once(); pytest.raises(ValueError, match='384 is not divisible by operator block size 256'); pytest.raises(ValueError, match='must support a zero-copy operator-page view'); pytest.raises(ValueError, match='int32 values'); pytest.raises(RuntimeError, match='persistent sinks') |
| ut/attention/test_sfa_v1.py | 69 | metadata.slot_mapping.shape == (100, 4, 1024); builder.use_pcp is False; builder.device == device; mock_prolog.assert_called_once(); self.assertRaises(RuntimeError); self.assertRaisesRegex(RuntimeError, 'NoPE SFA requires one latent KV cache tensor') |
| ut/attention/test_sparse_flash_mla.py | 4 | kwargs['sinks'] is sinks; metadata_op.call_args.kwargs['layout_kv'] == 'PA_BBND'; pytest.raises(ValueError, match='caller-owned per-head sinks') |
| ut/attention/utils.py | 0 | len(self.seq_lens) == len(self.query_lens) |
| ut/model_executor/test_deepseek_v4.py | 1 | fused_moe_kwargs['swiglu_limit'] == config.swiglu_limit |
| ut/model_executor/test_offloader.py | 3 | isinstance(offloader, NoopOffloader); not _is_using_nz_weight(param) |
| ut/model_executor/warmup/helpers.py | 0 | make_mock_worker |
| ut/model_executor/warmup/test_early_kernel_warmup.py | 12 | config.enable_early_kernel_warmup is False; device_index == 0; preimport.assert_called_once() |
| ut/model_executor/warmup/test_indexer_triton_warmup.py | 3 | query.shape == (1, 64, 128); warmup.collect_indexer_warmup_token_counts(topk, cores, max_tokens) == expected |
| ut/model_executor/warmup/test_kernel_warmup.py | 1 | mock_rej.assert_called_once_with(worker) |
| ut/model_executor/warmup/test_nz_warmup.py | 8 | nz_warmup._NZ_WARMED is True; mock_trans.call_count == first_calls; thread.join.assert_called_once_with(timeout=nz_warmup._NZ_JOIN_TIMEOUT_S) |
| ut/model_executor/warmup/test_penalties_triton_warmup.py | 3 | tokens.shape == (3, 8); torch.all(tokens[:, -1] == vocab_size); mock_apply.assert_called_once() |
| ut/model_executor/warmup/test_rejection_sampler_triton_warmup.py | 2 | sizes[0] == 1; mock_prepare.assert_called_once() |
| ut/model_executor/warmup/test_rms_triton_warmup.py | 4 | q.shape == (1 * num_vectorcore, 1, 128); mock_triton_q_rms.call_count == len(rw.collect_triton_rms_warmup_block_m_values()); mock_join.assert_called_once_with('rms') |
| ut/ops/test_activation.py | 3 | torch.allclose(out, expected_out); mock_gelu.assert_called_once() |
| ut/ops/test_aurora_tiling_keys.py | 8 | self.assertTrue(all((key[4] == 0 and key[7] == 0 for key in a2a3))); self.assertTrue(all((key[5] == 0 for key in a5))) |
| ut/ops/test_comm_utils.py | 3 | result.shape == expected; handle is not None; a2a_out.shape == input_tensor.shape |
| ut/ops/test_eplb.py | 3 | rank0_routing_table.shape == (EXPERT_REPLICA_ROUTING_TABLE_NUM_ROWS, 3); rank0_routing_table.dtype == torch.int32 |
| ut/ops/test_eplb_v2_recording.py | 3 | record_op.assert_called_once_with(counts, router.eplb_state.expert_load_view, router.eplb_state.should_record_tensor, 1, 4); pytest.raises(RuntimeError, match='operator-provided expert counts'); pytest.raises(RuntimeError, match='does not match local EPLB experts') |
| ut/ops/test_fla_lazy_imports.py | 7 | self.kernel.assert_called_once_with(x, gate, layer.weight, layer.bias, 'sigmoid', residual=residual, eps=1e-06, prenorm=True, residual_in_fp32=True, out=out); self.assertRaises(AttributeError) |
| ut/ops/test_force_eplb.py | 6 | first is second; len(moe_comm_method._force_eplb_topk_cache) == 1; pytest.raises(ValueError, match=message); pytest.raises(AssertionError, match='Forward context is not set') |
| ut/ops/test_fused_mc2_sleep_state.py | 5 | comm_impl.mega_moe_symm_buffer is symm_buffer; inference_modes == [True]; new_group._get_backend.assert_called_once_with(torch.device('npu')); pytest.raises(RuntimeError, match='update_group') |
| ut/ops/test_fused_moe.py | 74 | fused_input.topk_weights.dtype == torch.float32; use_multistage_eplb_load(dynamic_eplb, policy_type, collection_interval) is expected; placement_config.num_redundant_experts == 8; operation_order == ['wait_shared_input', 'prequantize_gate_up', 'wait_router', 'gate_up', 'wait_activation_overlap', 'activation', 'prequantize_down', 'wait_combine', 'down']; pytest.raises(RuntimeError, match='stop after parent init'); pytest.raises(ValueError, match='hash MoE routing requires input_ids'); pytest.raises(RuntimeError, match='router_output_ready'); pytest.raises(RuntimeError, match='shared_activation_overlap_start') |
| ut/ops/test_gate_linear.py | 5 | mm.assert_called_once() |
| ut/ops/test_kda_gate.py | 3 | torch.testing.assert_close(out, expected.to(torch.float32), rtol=1e-05, atol=1e-05); self.assertRaisesRegex(ValueError, 'head dim mismatch') |
| ut/ops/test_kimi_kda.py | 15 | beta.dtype == torch.float32; projected_bfg is fused_output; attention.o_norm.eps == config.rms_norm_eps; adapter.apply.assert_called_once_with(attention.in_proj_qkvgfab, qkv_input, bias=None) |
| ut/ops/test_layernorm.py | 9 | layer.bias is None; quant_description.scans == 1; fused_norm_gate.assert_called_once_with(x, gate, layer.weight, layer.bias, 'sigmoid', residual=residual, eps=1e-06, prenorm=True, residual_in_fp32=True, out=None) |
| ut/ops/test_linear.py | 23 | torch.testing.assert_close(self.layer.weight_fp32, weight.to(torch.float32)); mock_format_cast.assert_called_once() |
| ut/ops/test_mla.py | 20 | torch.testing.assert_close(out_k, k_li[:1]); indexer.forward_k.assert_called_once_with(k_hidden_states, indexer_metadata.cos, indexer_metadata.sin) |
| ut/ops/test_mla_weight_processing.py | 2 | inner.W_UV.shape == (2, 4, 4); (impl.fused_qkv_a_proj.weight is None) == is_kv_consumer; (impl.q_proj.weight is None) == is_kv_consumer; impl.process_weights_after_loading.assert_called_once_with(act_dtype) |
| ut/ops/test_moe_comm_method.py | 9 | torch.testing.assert_close(captured['x_active_mask'], torch.ones(2, dtype=torch.int8)); comm_impl.get_symm_buffer_for_mega_moe.assert_called_once() |
| ut/ops/test_moe_runtime_args.py | 7 | mlp_compute_input.quant.mxfp is not None; self.assertRaisesRegex(ValueError, 'primitive MXFP params are required') |
| ut/ops/test_moe_utils.py | 24 | comm.comm_context_op_builder.load.assert_called_once_with(); self.assertRaises(ValueError); self.assertRaises(ModuleNotFoundError); self.assertRaisesRegex(RuntimeError, 'does not expose SwiGLU-OAI'); self.assertRaisesRegex(RuntimeError, 'does not expose SiTU'); self.assertRaises(NotImplementedError) |
| ut/ops/test_packaged_attention.py | 3 | indices.shape == (7, 1, 512); indices.dtype == torch.int32 |
| ut/ops/test_pcp_kv_cache.py | 2 | proc.returncode == 0 and 'CHILD-OK' in proc.stdout |
| ut/ops/test_prepare_finalize.py | 7 | torch.testing.assert_close(gather.call_args_list[0].args[0], inputs); reduce.assert_called_once_with(gathered_inputs) |
| ut/ops/test_register_custom_ops.py | 8 | result.shape == (8, 4); custom_ops._get_ep_local_sizes(metadata, SimpleNamespace(world_size=8)) is None; result.shape == (3, 4) |
| ut/ops/test_rms_block_sizing.py | 6 | _row_block_size(dim, dtype) == row_block_size |
| ut/ops/test_rope_tile_sizing.py | 12 | actual == expected |
| ut/ops/test_routed_experts.py | 14 | [view.shape for view in views] == [torch.Size([2, 12]), torch.Size([2, 5])]; views[0].untyped_storage().data_ptr() == weights[0].untyped_storage().data_ptr(); len(views) == 1; pytest.raises(TypeError); pytest.raises(AssertionError, match='storage_offset=1'); pytest.raises(AssertionError, match='source=.*buffer='); pytest.raises(NotImplementedError, match='weight views are not defined'); pytest.raises(NotImplementedError, match='must implement get_eplb_weight_views'); pytest.raises(ValueError, match='first dimension'); pytest.raises(ValueError, match='must contain local_num_experts'); pytest.raises(ValueError, match='flattenable without a copy') |
| ut/ops/test_shared_mxfp_activation.py | 14 | self.torch.allclose.assert_called_once_with(7, 7); self.executor._prepare_linear_input_for_overlap.assert_called_once_with(self.executor.layer.gate_up_proj, 'input') |
| ut/ops/test_token_dispatcher.py | 30 | init_kwargs['scale'] is pertoken_scale; init_kwargs['quant_mode'] == -1; mock_dispatch.assert_called_once() |
| ut/ops/test_vocab_parallel_embedding.py | 17 | layer.parallel_mode is mode; events == ['gather', 'scatter'] + (['reduce'] if tp_size > 1 else []); layer.quant_method.embedding.assert_called_once_with(layer, input_.long()); pytest.raises(ValueError, match='must cover .* tokens and fit the static capacity'); self.assertRaisesRegex(ValueError, error) |
| ut/quantization/configs/test_fp8_config.py | 16 | mock_scheme_class.assert_called_once_with((128, 128)); self.assertRaises(NotImplementedError); self.assertRaisesRegex(NotImplementedError, 'weight_block_size'); self.assertRaisesRegex(NotImplementedError, 'activation_scheme') |
| ut/quantization/configs/test_modelslim_config.py | 70 | upstream_loader.assert_called_once_with(param=param, loaded_weight=loaded_weight, weight_name='model.layers.0.mlp.experts.w2_scale', shard_id='w2', expert_id=0, return_success=True); self.assertRaises(NotImplementedError); self.assertRaises(ValueError); self.assertRaises(KeyError) |
| ut/quantization/conftest_quantization.py | 0 | identity; create_mock_vllm_config; create_mock_ascend_config; create_moe_layer; create_mxfp_moe_layer |
| ut/quantization/methods/kv_cache/turboquant/conftest.py | 0 |  |
| ut/quantization/methods/test_moe_logical_experts.py | 5 | scheme_cls.supports_eplb is True; get_moe_num_logical_experts(layer, num_experts=130, global_redundant_expert_num=2) == 128 |
| ut/quantization/methods/test_registry.py | 7 | self.assertRaises(ValueError) |
| ut/quantization/methods/w8a8/test_fp8_block.py | 23 | mock_npu.npu_dynamic_mx_quant.assert_called_once(); self.assertRaisesRegex(ValueError, 'unpaired'); self.assertRaisesRegex(ValueError, '2D') |
| ut/quantization/methods/w8a8/test_w8a8_dynamic.py | 13 | mock_dyn_quant.assert_called_once(); self.assertRaisesRegex(RuntimeError, 'fused_w1_scale and fused_w2_scale to be present or absent together'); self.assertRaisesRegex(RuntimeError, 'fused_w1_scale_list and fused_w2_scale_list to be present or absent together') |
| ut/quantization/methods/w8a8/test_w8a8_mxfp8.py | 21 | torch.testing.assert_close(layer.weight[:16], torch.zeros(16, 2, dtype=torch.float8_e4m3fn)); mock_cast.assert_called_once() |
| ut/quantization/methods/w8a8/test_w8a8_static.py | 8 | torch.testing.assert_close(layer.weight_scale.data, torch.full((128,), 0.25)); mock_quantize.assert_called_once() |
| ut/quantization/test_quant_parser.py | 5 | self.assertEqual(result, 'W4A4_MXFP4'); self.assertEqual(result, 'W8A8_MXFP8') |
| ut/quantization/test_utils.py | 15 | mock_logger.info_once.assert_called_once() |

## 使用边界

AST结构、断言存在及配置参数不是运行记录。新模型变更应由真实调用链选择源测试及其参数，再分别留收集数量、skip、失败、真实退出和数值/性能原始结果。CPU mock只证明被断言的Host行为；涉及torch_npu、分布式、编译或外部权重的路径必须在目标依赖与设备上另验。本次未导入/运行上游、未编译、未调用NPU或Agent A/B；未摘选的精确参数与完整Device语义不由本矩阵补造。
