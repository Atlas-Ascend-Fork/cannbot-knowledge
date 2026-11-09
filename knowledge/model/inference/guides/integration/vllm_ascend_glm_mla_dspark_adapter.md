---
type: Guide
title: vLLM Ascend GLM MLA DSpark 适配：辅助特征、Context KV 与草稿词表
description: 复用DSpark采样和Markov协议时替换MLA骨干，核对Speculators架构恢复、独立量化、双向块、草稿RoPE、分层slot
  mapping及缩小词表加载。
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5_dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/qwen3_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_speculative_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_executor/test_glm_mla_dspark.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/qwen3_dspark.py
  role: implementation
created_at: '2026-10-29T13:13:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:55:50Z'
---

# vLLM Ascend GLM MLA DSpark 适配：辅助特征、Context KV 与草稿词表

## 复用哪些层，替换哪些层

Glm5DSparkForCausalLM继承AscendQwen3DSpark的采样/Markov接口，重建MLA模型和head，不能因此沿用Qwen GQA骨干。草稿层沿用DFlash decoder的residual/norm结构但替换成dense MLA Attention与DeepSeek MLP；构建时quant_config=None，刻意不继承target W4A8/SFA量化或offload。

构造要求draft配置存在、草稿层数正数，q_lora_rank/kv_lora_rank/qk_nope_head_dim/qk_rope_head_dim/v_head_dim均为正整数；GQA权重不能只改architecture后通过。该源码路径不是模型、PD或硬件已通过验证的保证。

## 架构转换后还要核对最终类型

固定Speculators转换可能把MLA架构归成Qwen DSpark。窄范围_normalize_glm_mla_dspark只在SpeculatorsConfig且原checkpoint声明Glm5DSparkForCausalLM时恢复该架构，检查MLA维度，update_arch_并将model_arch_config.is_deepseek_mla设True。该shim不是接受任意GQA权重的转换器，不能取消其维度拒绝。

## 辅助特征与Context KV

combine_hidden_states要求最后一维等于context_proj.input_size，按训练次序线性投影后context_norm；不是对多个tap做平均。维度正确也不证明tap顺序正确，需保留target layer id与checkpoint训练接口。

precompute_and_store_context_kv使用每个草稿层自己的fused QKV A投影、KV cache和草稿RoPE cos/sin，不能借target的全局RoPE缓存。context_positions数必须等于context行数；slot mapping可以各层共用Tensor，也可以每层一个list/tuple，列表长度等于草稿层数，参与写入的slot数与行数相同。context空、mapping=None或某层slot为空/None时不写该缓存；不能把dummy无写入解释成真实context已就绪。

get_draft_attn_causal对全部该草稿层返回False，完整draft block内双向可见；sliding_window_non_causal字段不把这些full-attention层改为因果。该mask必须与non_causal_multi_token_decode元数据和真实backend一致，不能根据target是causal就复用target mask。

## Loader、词表与输出映射

norm.weight映射model.final_norm.weight；其余非head/非d2t权重补model.前缀，t2d跳过，d2t转draft_id_to_target_id；gate/up与q_a/kv_a按堆叠映射交给AutoWeightsLoader。has_own_embed_tokens/has_own_lm_head按实际包含的key设置，不是按构造模块判断。

缩小输出词表要求同时有d2t和独立lm_head权重，扩展输入词表要求独立embedding；不能把缺失映射当恒等。继承协议中的d2t是加到草稿id上的偏移：示例buffer=[0,2,4]、id=[0,1,2]得到target=[0,3,6]，不是直接索引后返回[0,2,4]。具体采样/概率导出仍按Runner约束，不能仅凭词表映射推分布保持。

confidence_head只有checkpoint真的包含对应权重时才启用，返回sigmoid概率；启用字段但缺权重不会自动制造有效head。post_process对context_proj执行[QuaRot对齐](vllm_ascend_draft_quarot_alignment.md)，继承Qwen configure_target_aux_hidden_capture：找到target或其language model的setter时请求materialized=True，缺setter时不强行调用；不能复制Kimi的raw-prefix-sum约定。

## 验证、边界与停止

保存转换前后architecture、真实类、MLA维度、量化对象、tap次序、每层context位置/slot/rope与vocab映射；依次验证加载、context写入、双向mask、草稿logits及有无confidence head，再覆盖graph/并行/PD。维度/映射/缓存不完整或输出不对齐时停止，回匹配checkpoint或关闭草稿。

所引CPU/mock测试覆盖注册、投影、context映射、词表和转换拒绝，不声称PD推理覆盖；本次未运行它们。patched MLA父类、原生DSpark完整采样和NPU kernel仍需单独闭合，本卡不将继承和测试定义当作完整适配结果。


## 与Runner采样合同配对

缩表权重加载通过后还要检查[DSpark词表概率空间](../../runbooks/precision/vllm_ascend_dspark_vocab_probability_space.md)：MRv1带映射时不导出probabilistic draft_probs，MRv2可按target轴scatter；不能把模型侧map_draft_to_target实现当两Runner均已完成概率导出的证据。[块布局与Markov反馈](vllm_ascend_dspark_block_markov_contract.md)和[有效KV长度](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)分别约束query、前驱与缓存；本卡先前未关闭的采样任务现有这些接口知识可用，完整kernel/统计/PD验证仍未完成。
