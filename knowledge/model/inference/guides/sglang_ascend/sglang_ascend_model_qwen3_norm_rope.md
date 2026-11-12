---
type: Guide
title: SGLang 昇腾 Qwen3 Dense 与 MoE 的融合 QK 准备
description: 说明 Qwen3 的位置缓存、QK RMSNorm+bias 参数、空批次和 NPU MLP 缓存预取/流等待边界。
tags:
- task.implementation
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_moe.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 Qwen3 Dense 与 MoE 的融合 QK 准备

## Attention 准备合同

Qwen3 与 Qwen3MoE 在 NPU 调用 split_qkv_rmsnorm_rope，传入 QKV 逻辑 q_size/kv_size/head_dim、QK norm eps/weight，以及存在时的 bias。起始 attention layer 先按本轮 positions 刷新 position_sin/cos，后续层复用；不能把上轮同 shape 的 gathered cache 当本轮位置。

Dense 的 forward 在 NPU 选择专用 prepare；MoE 先对空 hidden states 返回空 inner state，再选择 NPU prepare/core 配对。GPU AITER 的 fused KV write 路径与这里不同，NPU 融合 split/norm/RoPE 不意味着已经完成 KV store。

## 层边界与图执行

Qwen3 的 attn/ffn boundary 按实际 quant_format 传入对应的量化读取；post_residual_addition 会关闭不包含该加法的 fused FP8 norm。NPU prefill TC_PIECEWISE 且 MLP 两组 weight 存在时给 ffn prepare 传 cache 权重列表；MLP 后若存在 CMO stream 必须 wait，再完成 boundary。

核对 norm bias 是否完整加载、positions 是否刷新、保存 KV 的责任和 stream wait。验证普通 Tensor/量化 tuple、post residual、空 rank 与 prefill/decode 的 logits；回退应保留 norm 与位置语义，仅恢复 native 准备及匹配边界。本卡不推断型号覆盖，也未运行图或模型测试。

## 相关机制

- [SGL QKV拆分、可选RMSNorm与两种RoPE配对](../../apis/sgl_kernel_npu/sgl_split_qkv_rmsnorm_rope.md)
