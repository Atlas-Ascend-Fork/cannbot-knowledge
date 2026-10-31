---
type: Concept
title: Gated Attention
description: 门控Attention机制与当前3.5 Page cache/分片归约/950量化边界，区分Next投机与C8实现。
tags:
- task.design
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/README.md
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:31:37Z'
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
- **C8 KVCache 路径（固定 Qwen3-Next/SGLang）**：该版本暂不支持与 MTP 同时开启，不能把下列 C8 变体与上面的 MTP1 直接组合。KV 写入前以传入的 `k_scale` / `v_scale` 经 `npu_quantize`（quant axis=-1）量化为 Int8，读出时带 `key_antiquant_scale` / `value_antiquant_scale` 反量化，显存减半。见 [w8a8c8](../quantization/w8a8c8.md)。
- **Prefill CP+TP 路径（Qwen3-Next）**：Q 沿 Sequence 切分到 CP rank，KV 通过 AllGather 汇总为完整序列，再执行 Attention；配合 ZigZag 负载均衡。见 [context-parallel](../parallelism/context_parallel.md)、[zigzag-cp](../parallelism/zigzag_cp.md)。
- **Qwen3.5-MoE full attention 路径**：`merged_qkv_proj` 一次 Matmul 同时输出 Q/K/V 与 **attention gate**——Q 投影宽度为 `head_dim*2`，输出按 `torch.chunk(..., 2, dim=-1)` 拆为 query 与 gate；对 Q/K 各做 **QK-RMSNorm**（`q_norm`/`k_norm`，作用在 `head_dim` 维）；**partial RoPE**（`partial_rotary_factor=0.25`，仅前 `rotary_dim`=64 维调 `npu_rotary_mul`，透传部分 `cat` 回来），位置编码为 MRoPE；attention 经 `npu_fused_infer_attention_score_v2`（TND layout + block 化 KV cache，Prefill `sparse_mode=3`，Decode 用 `actual_seq_kvlen` 控可见范围）计算后与 gate 相乘，再过 `o_proj`（TP按当前路径AllReduce，纯EP匹配的Prefill token分片可ReduceScatter；mm_all_reduce_base仅950且受其他条件限制）。见 [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)、[qwen3-5-moe](../models/qwen3_5_moe.md)。

## 当前模型接入边界

Qwen3.5 FullAttention已接统一Page cache：Prefill直接算有效K/V后写入，Decode先按slot写入后读PA，长度、掩码与block_table保持一致。该模型只允许next_n=0；上文MTP机制示例来自Next，不证明3.5支持投机解码。950 FP8/MXFP8是其Linear/专家量化方案，不等同Next的Int8 C8 cache。

## Performance Characteristics

- 来源所述 Qwen3-Next 按头切分路径的 Attention Head=16，故该路径纯 TP 上限为 16；其他模型须读取各自 config.num_attention_heads 及 KV 头/实现限制，不是 Gated Attention 的固定属性。
- Prefill 长序列（64K+）下主要受激活内存和 Q·Kᵀ 计算量约束，是 CP 的首要收益模块。
- Decode 单步受 KVCache 带宽主导，C8 量化可直接缓解 HBM 带宽压力。
- 与 GDN 层形成计算/访存特征差异，是 Qwen3-Next 采用"分层异构并行"的直接依据。

## Evidence

- [qwen3_next_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md)（supporting）
- [modeling_qwen3_5_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/README.md)（constraint）

## Links

- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [gated-deltanet](gated_deltanet.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [context-parallel](../parallelism/context_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [w8a8c8](../quantization/w8a8c8.md)
