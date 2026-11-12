---
type: Guide
title: SGLang 昇腾 Qwen3-Next 与 Qwen3.5 的混合注意力准备
description: 区分 GDN 输入投影、full-attention gate、prefill M-RoPE 和 decode Gemma RMSNorm
  融合。
tags:
- task.implementation
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_5.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/qwen3_next.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 Qwen3-Next 与 Qwen3.5 的混合注意力准备

## Linear attention 与 full attention 分开处理

Qwen3-Next/3.5 的 GDN input projection 在 NPU 将 DUAL_STREAM_TOKEN_THRESHOLD 设为 0，禁用原 GPU 小批量双流分支，分别计算 qkvz 与 ba；不能把其他模型的 NPU multi-stream 开关泛化到这段投影。

full attention 的 NPU decode gate 路径调用 split_qkvgate_gemma_rmsnorm_rope，保留 partial rotary width、QK norm 与 gate。Qwen3-Next 在第一个 full-attention layer 刷新位置表；extend/draft_extend/mixed 或没有 gate 时走 native。

Qwen3.5 为 prefill 单设 M-RoPE 路径：不存在 mrope_section 则 native；一维 positions 展开为三轴，按 positions gather cache，再调用 triton_split_qkv_rmsnorm_mrope，传 gemma_weight、mrope_section/interleaved 和 has_gate。其 decode 位置刷新使用 refreshes_rope_cos_sin 标记，不能按所有层统一刷新。

## 输出 gate 与验证

Qwen3.5 普通 NPU 输出 gate 先 reshape 为二维 contiguous，再调用 npu_fused_sigmoid_mul；预量化 FP8 tuple 路径另有条件。Qwen3-Next 当前普通路径则显式 sigmoid 后乘，不能因共用混合架构而认定两者融合相同。

验证 linear/full-attention 交替、M-RoPE 三轴位置、partial rotary、gate shape 和多步 decode，比较 unfused 数值。回退保持各模型原 gate/Norm 公式和正确位置刷新。本卡不把模型准备分支当 GDN Device kernel 的完整分析，也没有实测收益。

## 相关机制

- [SGL Gemma Q/gate解交错与部分RoPE接口](../../apis/sgl_kernel_npu/sgl_qkvgate_gemma_rope.md)
- [Qwen3.5-397B 在 A3 的混合状态缓存与长输入配方](../models/sglang_ascend/sglang_ascend_doc_qwen3_5_397b.md)
