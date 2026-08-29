---
type: Concept
title: Gated Attention
description: 承担精确长程检索的标准 Softmax Attention 变体（也称混合注意力模型中的 full attention 层），在 Attention 输出后引入一个元素级 Gate（Sigmoid/SiLU 门控）对输出进行调制，再送入残差路径。在 Qwen3-Next 与 Qwen3.5-MoE 中与线性注意力变体 Gated DeltaNet 混合交替堆叠，构成分层异构注意力。Qwen3.5-MoE 的 full attention 由 merged_qkv_proj 同时产出 gate，并对 Q/K 做 QK-RMSNorm、对部分维度应用 partial MRoPE。
tags:
- task.design
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/qwen3-next/qwen3_next_optimization.md
  role: primary
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Gated Attention

## Summary

承担精确长程检索的标准 Softmax Attention 变体（也称混合注意力模型中的 "full attention" 层），在 Attention 输出后引入一个元素级 Gate（Sigmoid/SiLU 门控）对输出进行调制，再送入残差路径。在 [qwen3-next](../models/qwen3_next.md) 与 [qwen3-5-moe](../models/qwen3_5_moe.md) 中与线性注意力变体 [gated-deltanet](gated_deltanet.md) 混合交替堆叠，构成分层异构注意力。

## Mechanism

- 输入 hidden state 经 qkv_proj 得到 Q、K、V（GQA，num_kv_heads ≤ num_heads；如 Qwen3-Next num_heads=16）。
- 计算标准 Scaled Dot-Product / FlashAttention：`softmax(QKᵀ/√d) · V`。
- Attention 输出与门控分支（通常是 `sigmoid(Wg · x)` 或 `silu(Wz · x)`）逐元素相乘，再经 out_proj 输出。
- Prefill 下计算量 O(S²)，激活值内存随 S² 增长，是长序列部署的主要内存与时延瓶颈。
- Decode 下每步处理单 token（或 MTP1 下额外 1 个 draft token，一次推理可验证 2 个 token），KV 从 KVCache 读取，计算量 O(S)。

## Variants

- **BF16 标准路径**：Attention 后门控，激活 Cube + Vector 联合。
- **C8 KVCache 路径**：KV 写入前以传入的 `k_scale` / `v_scale` 经 `npu_quantize`（quant axis=-1）量化为 Int8，读出时带 `key_antiquant_scale` / `value_antiquant_scale` 反量化，显存减半。见 [w8a8c8](../quantization/w8a8c8.md)。
- **Prefill CP+TP 路径（Qwen3-Next）**：Q 沿 Sequence 切分到 CP rank，KV 通过 AllGather 汇总为完整序列，再执行 Attention；配合 ZigZag 负载均衡。见 [context-parallel](../parallelism/context_parallel.md)、[zigzag-cp](../parallelism/zigzag_cp.md)。
- **Qwen3.5-MoE full attention 路径**：`merged_qkv_proj` 一次 Matmul 同时输出 Q/K/V 与 **attention gate**——Q 投影宽度为 `head_dim*2`，输出按 `torch.chunk(..., 2, dim=-1)` 拆为 query 与 gate；对 Q/K 各做 **QK-RMSNorm**（`q_norm`/`k_norm`，作用在 `head_dim` 维）；**partial RoPE**（`partial_rotary_factor=0.25`，仅前 `rotary_dim`=64 维调 `npu_rotary_mul`，透传部分 `cat` 回来），位置编码为 MRoPE；attention 经 `npu_fused_infer_attention_score_v2`（TND layout + block 化 KV cache，Prefill `sparse_mode=3`，Decode 用 `actual_seq_kvlen` 控可见范围）计算后与 gate 相乘，再过 `o_proj`（TP 下经 all_reduce 或 `npu_mm_all_reduce_base` 汇聚）。见 [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)、[qwen3-5-moe](../models/qwen3_5_moe.md)。

## Performance Characteristics

- Attention Head = 16 限制纯 TP 上限为 TP16，超过需引入 CP 或 SP。
- Prefill 长序列（64K+）下主要受激活内存和 Q·Kᵀ 计算量约束，是 CP 的首要收益模块。
- Decode 单步受 KVCache 带宽主导，C8 量化可直接缓解 HBM 带宽压力。
- 与 GDN 层形成计算/访存特征差异，是 Qwen3-Next 采用"分层异构并行"的直接依据。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/qwen3-next/qwen3_next_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/qwen3-next/qwen3_next_optimization.md) 并行策略章节；`models/qwen3-next/patches/stage2/0002-feat-support-c8.patch`（C8 KVCache）；`models/qwen3-next/patches/stage4/0001-feat-support-context-parallel.patch`（CP 切片与 ZigZag）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/qwen3_5/qwen3_5_moe_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen3_5/qwen3_5_moe_optimization.md)（RoPE / FlashAttention / Attention TP 计算分解章节）、[`models/qwen3_5/models/modeling_qwen3_5_moe.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/models/modeling_qwen3_5_moe.py)（`Qwen3_5MoeAttention` 的 `merged_qkv_proj`+gate chunk、`q_norm`/`k_norm`、partial RoPE `npu_rotary_mul`）。MR!402（分支 chy_new "support qwen3_5"）。

## Links

- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [gated-deltanet](gated_deltanet.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [context-parallel](../parallelism/context_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [w8a8c8](../quantization/w8a8c8.md)

<!-- cannbot:related:start -->
## 相关

- [Qwen3.5-MoE](../models/qwen3_5_moe.md)（`related`）：“- **full attention**：`merged_qkv_proj` 一次 Matmul 同时输出 Q/K/V 与 attention gate；Q/K 做 QK-RMSNorm；partial RoPE（仅 `head_dim` 的一部分应用 MRoPE，`partial_rotary_factor=0.25`）；FlashAttention 走 `npu_fused_infer_attention_score_v2`（TND + block KV，见 ［fused-infer-attention-score］(../kernels/fused_infer_attention_score.md)）。”；“- **Qwen3.5-MoE full attention 路径**：`merged_qkv_proj` 一次 Matmul 同时输出 Q/K/V 与 **attention gate**”。模型卡的 full-attention 结构由模块卡的 Qwen3.5 专用 gated-attention 路径直接展开。
<!-- cannbot:related:end -->
