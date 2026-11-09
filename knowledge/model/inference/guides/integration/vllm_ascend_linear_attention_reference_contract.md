---
type: Guide
title: vLLM Ascend线性Attention参考：Bailing状态、卷积接受数与输出有效区
description: 核对Bailing线性Attention的FP32 QKV、cache清理、prefill/decode和gate消费，并区分通用Torch causal_conv1d参考的PAD跳过、accepted截短与NPU/GDN resume协议，避免参考替换改变token布局或state。
aliases:
- AscendBailingMoELinearAttention
- causal_conv1d_ref
- causal_conv1d_fn
- causal_conv1d_update
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/bailing_moe_linear_attn.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/causal_conv1d.py
  role: primary
created_at: '2026-11-03T06:33:14Z'
updated_at: '2026-11-03T06:33:14Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend线性Attention参考：Bailing状态、卷积接受数与输出有效区

固定Main ceac1a2，完整技术代码阅读Bailing适配169行和Torch causal_conv参考297行。二者聚合“stateful参考接口不能凭shape替换”的任务，不宣称Bailing直接调用该卷积文件；Kimi使用外部fla_npu，310P另有专用Csrc，不能混为一条实现。未运行上游、NPU或数值，保持draft/空平台。

## Bailing先确定有效前缀和真实cache

metadata存在时按prefix取LinearAttentionMetadata，真实token数为prefill_tokens+decode_tokens；否则只做shape/profile路径。QKV仅投影有效前缀，整体转FP32，再可选SiLU；按Q与KV各自分片宽度拆开，可选q/k RMSNorm，随后可选RoPE和q缩放。新模型的GQA head数、TP slope、位置和投影轴必须同时匹配。

真实metadata下取kv_cache[0]和state_indices，并调用Native clear_linear_attention_cache_for_new_sequences清新序列。无prefill走linear_attention_decode，Q范围0..num_decode_tokens、slot范围0..num_decodes、block32；有prefill走Native prefill/mix helper并提供Ascend prefix kernel和decode回调。它不是本文件自行实现全部recurrent数学，chunk混合布局仍由callee决定。

无metadata时hidden为empty用于profile，不是有意义Attention输出。随后真实/shape路径都经g_proj、g_norm与sigmoid gate，转回原dtype，再dense写output有效前缀；本覆盖没有通用清零容量尾部。不能以profile执行成功或返回shape正确判断cache值、gate或padding都有效。

## Torch卷积参考的layout与状态语义

causal_conv1d_ref要求activation为None/silu/swish，先把x转weight dtype，以每channel分组F.conv1d计算；有initial_states先拼历史并不padding，否则padding width-1，输出截回当前seqlen。返回final state时用F.pad的正padding或负crop取得末width-1历史并转输入dtype，可copy到final_states_out。输出经可选SiLU再转输入dtype，不等于所有步骤FP32的Golden。

varlen causal_conv1d_fn强制query_start_loc/cache_indices/has_initial_state/conv_states均存在。输入只接受若干leading singleton 3D变体归一到[feature,tokens]，weight可按feature轴转置，state可按最后两维转置；要求历史长度至少width-1。通过.tolist和.item逐请求在Host循环，不是捕获安全的无同步NPU替代。

prefill reference遇cache_idx==pad_slot_id直接跳过整段，不为该段补等长零输出；最后cat仅保留处理过请求的token，全部skip则返回[feature,0]。因此有PAD请求时输出token布局可缩短，不能直接填入要求原槽顺序/固定长度的consumer。其它负索引没有统一过滤，可能进入Python负索引语义，caller需先验证。

update则以x.clone初始化输出，被PAD或accepted<=0跳过的部分保留输入值而不是清零；处理部分才覆盖卷积结果。无query_start_loc时按batch/单token或多token请求循环；有边界时按每个[start,end)请求运行。接受数对当前seq_tokens做[:accepted]截短，再写相应前缀和最终历史；未处理后缀继续保留输入。

这与[GDN参考](vllm_ascend_310p_primitive_fallback_contract.md)中accepted仅选择resume state、不截短当前query的协议不同，也不证明外部fla_npu update与这里完全相同。更换参考实现前明确接受数是否含target步、是恢复上一轮还是裁当前query，逐一保存输出有效区与state前后；不能统一把同名num_accepted_tokens解释成一个数量。

新模型需校验query长度和输入总量、weight/state轴、width-1历史、PAD/非法索引、空/部分接受、重复state slot以及多步连续输出。先分别建立参考与真实Csrc/外部API的数值比较，再判断能否替换/捕获；本次没有执行这些验证。
