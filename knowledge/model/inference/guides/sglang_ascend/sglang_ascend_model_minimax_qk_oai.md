---
type: Guide
title: SGLang 昇腾 MiniMax M2/M3 的 QK 与 SwiGLU-OAI 适配
description: 区分 M2 TP QK Norm、M3 Gemma Norm/OAI 参数、稀疏 index QK 与 shared expert overlap
  条件。
tags:
- task.implementation
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/minimax_m3.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/minimax_m2.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang 昇腾 MiniMax M2/M3 的 QK 与 SwiGLU-OAI 适配

## QK 与 router

M2 在 use_qk_norm 时 gather cos/sin，并调用 split_qkv_tp_rmsnorm_rope，明确传 attention-TP world/group；否则 split 后让 q/k contiguous 再 RoPE。M3 使用 position-cache-half 融合，传 Gemma 的 gemma_weight、rope_dim 和 cast_norm_to_bf16=True；稀疏层还计算独立 index_qkv，仅当 disable_index_value=True 时 V 宽度为0并拆为两段 q/k；其他稀疏层仍按实际 q_size、idx_head_dim、idx_head_dim 拆 Q/K/V，不能统一按两段或三等份拆。

M3 的 BF16 router 在 NPU 用 BF16 torch.mm 后 `.float()`，绕过不支持的 aten::mm.dtype；这不同于在 FP32 做同一次 matmul，应以该舍入语义比较 TopK。非 BF16-router 分支仍将输入转 FP32 交 gate。

## 激活与并行

M3 swigluoai 传模型的 alpha/limit 到 sgl_kernel_npu，Dense/shared 非量化激活使用 need_quant=False，不能替换 plain SwiGLU。DeepEP shared experts replicated，NPU 对 extend、target_verify、decode 都可启动 process_shared_expert，尾部 wait 后直接与已经完整的 routed result 相加，不再 TP all-reduce。

空 attention 短路先保证 o_proj 不需 all-reduce；空 MoE rank 仍参与 experts collective。验证 M2/M3 的各自 norm、router 舍入、index Q/K 和 OAI limit 边界，比较输出而非仅 shape。回退重建单流/明确 unfused 路径，并保留全部激活参数；源码不构成本次加速或精度测量。

## 相关机制

- [SGL张量并行QKV RMSNorm与NeoX RoPE接口](../../apis/sgl_kernel_npu/sgl_qkv_tp_rmsnorm_rope.md)
- [SGL SwiGLU-OAI 的裁剪、INT8舍入与分组输出](../../apis/sgl_kernel_npu/sgl_swiglu_oai_quant.md)
