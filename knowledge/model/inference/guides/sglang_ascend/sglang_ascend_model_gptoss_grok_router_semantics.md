---
type: Guide
title: SGLang 昇腾 GPT-OSS 与 Grok 的激活和路由精度
description: 区分 GPT-OSS 的 NPU SwiGLU-OAI 与 KV 保存责任，以及 Grok FP32 router softcap/FP32
  RoPE。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/gpt_oss.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/grok.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/rotary_embedding/base.py
  role: implementation
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang 昇腾 GPT-OSS 与 Grok 的激活和路由精度

## GPT-OSS 的 NPU 入口

GPT-OSS 模型构造在 NPU 将 hidden_act 设为 npu_swiglu_oai，不能用普通 SiLU/SwiGLU 替代；QKV prepare 在 NPU 不传 GPU fused_set_kv_buffer_arg，NPU RoPE 只计算并返回旋转 Q/K，KV 由后续 attention 保存：enable_fused_set_kv_buffer 仅在 CUDA/HIP 条件成立，故此 NPU 路径 save_kv_cache=True。空输入返回空 inner state，core 必须遵守同一状态协议。

## Grok 的不同语义

Grok NPU 不使用 GPU custom_routing_function：先 flatten hidden，显式 gate 得 router logits，再应用 `30*tanh(logits/30)` 的 router softcap，TopK 后恢复原 shape。expert 激活为 GELU，与 GPT-OSS 的 OAI 互不等价。

Grok 的 RoPE cache 在 NPU 使用 FP32，q/k 转 FP32 旋转后再转回原 dtype；缩放 RoPE 与 partial rotary 范围仍来自各自配置。attention logit softcap 与 router softcap 是两处不同操作，不能只留下一个。

适配时分别核对模型架构、hidden_act、gate dtype、两处 cap 和 KV 写入次数；比较 TopK、expert 激活、长 positions 与最终 logits。用明确的 native 公式回退也须保留 OAI/GELU 和精度边界。两组模型入口均没有整卡产品证据或本次实测结果，保留 draft，不以通用 NPU 支持推断全部 checkpoint 可用。
