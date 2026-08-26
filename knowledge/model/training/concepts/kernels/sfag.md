---
type: Concept
title: SFAG（SparseFlashAttentionGrad，DSA 稀疏注意力反向算子）
description: SparseFlashAttentionGrad（SFAG）是 DeepSeek-V3.2 训练独有的 sparse-flash-attention 反向融合算子，整体沿用 FlashAttentionGrad（FAG）计算流程，针对 DSA 稀疏 Top-k 选择带来的离散访存做指令缩减与搬运聚合。与推理侧不同：推理只有 LI/SFA 正向算子，SFAG 是训练侧新增件，与 slig（Indexer 反向 + KL Loss）一道构成 DSA 训练反向算子组，是「业界率先攻克 DSA 反向」的关键之一。 在 TorchTitan-npu 中，SFAG 并非独立的 autograd.Function，而是 torch_npu.npu_sparse_flash_attention 正向算子在 PyTorch autograd 引擎下注册的反向实现——正向于 dsa_forward 落子，反向由 autograd 自动触发，因此正向调用必须 return_softmax_lse=True 以向反向透传 softmax_max/softmax_sum（见 ［op 绑定］(#op-绑定torch_npunpu_sparse_flash_attention)）。
tags:
- task.implementation
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# SFAG（SparseFlashAttentionGrad，DSA 稀疏注意力反向算子）

## Summary

`SparseFlashAttentionGrad`（SFAG；优化文档 Tiling/Pipeline 实现段用算子全名 `SparseFlashAttentionScoreGrad`，对齐昇腾 `FlashAttentionScoreGrad` 命名——本库及其它页用简写 `SparseFlashAttentionGrad`/SFAG 指代同一算子）是 DeepSeek-V3.2 **训练独有**的 [sparse-flash-attention](../../../inference/concepts/kernels/sparse_flash_attention.md) 反向融合算子，整体沿用 `FlashAttentionGrad`（FAG）计算流程，针对 DSA 稀疏 Top-k 选择带来的**离散访存**做指令缩减与搬运聚合。与推理侧不同：推理只有 LI/SFA **正向**算子，SFAG 是训练侧新增件，与 [slig](slig.md)（Indexer 反向 + KL Loss）一道构成 DSA 训练反向算子组，是「业界率先攻克 DSA 反向」的关键之一。

在 TorchTitan-npu 中，SFAG 并非独立的 `autograd.Function`，而是 `torch_npu.npu_sparse_flash_attention` 正向算子在 PyTorch autograd 引擎下注册的**反向**实现——正向于 `dsa_forward` 落子，反向由 autograd 自动触发，因此正向调用必须 `return_softmax_lse=True` 以向反向透传 `softmax_max`/`softmax_sum`（见 [op 绑定](#op-绑定torch_npunpu_sparse_flash_attention)）。

## 计算逻辑

反向整体分五步（$P$ 为正向 softmax 结果，$Top\text{-}k\ index$ 来自 [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)，$d$ 为头维度）：

1. **Gather**：$K_{topk} = \mathrm{Gather}(K,\ Top\text{-}k\ index)$
2. **重计算** SFA 正向 softmax：$P = \mathrm{Softmax}(Q\,@\,K_{topk}^\top/\sqrt{d})$
3. $dP = dY\,@\,V^\top$
4. $dS = P \ast (dP - \mathrm{FlashSoftmaxGrad}(dY\,@\,attention\_in))$；`FlashSoftmaxGrad` 输入为反向梯度 `dY` 与正向输出 `attention_in`
5. 链式求梯度：$dQ = dS\,@\,K_{topk}/\sqrt{d}$；$dK = \mathrm{ScatterAdd}(dS^\top@Q/\sqrt{d},\ Top\text{-}k\ index)$；$dV = P^\top@dY$

第 2 步重计算（而非缓存全量 $P$）与 SLIG 同理，是显存/算力权衡；$softmax\_max$/$softmax\_sum$ 由正向透传，反向据此重建 softmax 而无需重跑 Top-k 选择。

## op 绑定：`torch_npu.npu_sparse_flash_attention`

SFAG 的 device 算子由正向 `npu_sparse_flash_attention` 的反向注册承载。`dsa_forward`（matrix-absorb 模式）中的正向调用即决定了反向 SFAG 的输入/输出契约：

```python
output, softmax_max, softmax_sum, *_ = torch_npu.npu_sparse_flash_attention(
    q_nope, k_nope, v,
    sparse_indices=topk_indices.to(torch.int32),  # LI 产出的 Top-k index
    block_table=None,
    actual_seq_lengths_query=actual_seq_len,
    actual_seq_lengths_kv=actual_seq_len,
    query_rope=q_pe, key_rope=k_pe,               # MLA 的 RoPE 分量
    scale_value=scale,
    sparse_block_size=1,
    layout_query="BSND", layout_kv="BSND",
    sparse_mode=3,
    attention_mode=2,           # 0: GQA/MHA, 1: MLA-naive, 2: MLA-absorb
    return_softmax_lse=True,    # it must be True in training mode
)
# torchtitan_npu/converters/kernels/dsa.py:248
```

要点：
- **`return_softmax_lse=True` 是训练强制项**——反向 SFAG 需要 `softmax_max`/`softmax_sum`（softmax 的 LSE 聚合量）重建 $P$；漏设则反向无法重计算。
- `q_nope`/`k_nope` 是 MLA weight-absorb 后的低秩部分，RoPE 走旁路 `query_rope`/`key_rope`；`attention_mode=2`（MLA-absorb）是训练唯一支持模式（`dsa_forward` 要求 `num_head_kv == 1`）。
- `sparse_indices` 即 [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md) 的 `topk_indices`（先 `npu_lightning_indexer(..., return_value=False)` 产出，再 `.to(torch.int32)`）；这是 SFAG Gather/ScatterAdd 的离散索引来源。
- SFAG 由 PyTorch autograd 在 `output.backward()` 时自动调度，无显式 `autograd.Function`——与同文件 SLIG 的 `LILossTrain(torch.autograd.Function)` 形成对照（KL Loss 需手写 backward，SFA 反向不需要）。

CP 场景同一 op，仅把 KV 换成 AllGather 后的全局张量（`k_nope_global[:, :slice_end]` 等），其余签名一致，见 [custom-cp-dsa](../parallelism/custom_cp_dsa.md)：

```python
# 先 allgather_sequence(k_nope/v/k_pe, self.cp_mesh)，再喂入同一 npu_sparse_flash_attention
# torchtitan_npu/distributed/context_parallel/dsa_cp.py:199
```

算子经 `@register_npu_converter("npu_dsa")` 的 `DSAKernel` 注册，通过 `converters = ["npu_dsa", ...]` 在训练 toml 中开关（`replace_methods("DSV32_SDPA", "forward", dsa_forward)`，仅支持 matrix-absorb + LI Loss 默认开启）。

## Tiling 设计

- **核间**：Batch 轴与 $S_Q$ 合轴作分核轴，核数随分核轴连续排布（$T = B \times S_Q$，$CoreProcessNum = \mathrm{CeilDiv}(T, CoreNum)$）。
- **核内**：各矩阵乘左右基本块见下表，源数据搬运启 Double Buffer 实现搬运与计算并行；$Q_{index}$ 以 $128{\times}256$ 粒度载入 L1 常驻，供 $d_s@Q_{index}$ 复用减少重复访存（$V_{index}$ 同理）；UB 基本块 $128{\times}128$。

| 矩阵乘 | 左矩阵 L1 基本块 | 右矩阵 L1 基本块 |
|--------|-----------------|-----------------|
| $Q_{index}@K_{index}$ | 128×576 | 128×128×2(DB) |
| $d_y@V$ | 128×512 | 128×128×2(DB) |
| $d_s@K$ | 128×128×2(DB) | 128×128×2(DB) |
| $d_s@Q$ | 128×128×2(DB) | 128×576 |
| $d_y@P$ | 128×128×2(DB) | 128×512 |

## Pipeline 与离散访存优化

五阶段：$K_{index}/V_{index}$ 离散转连续（V0）→ $Q_{index}@K_{index}$ 与 $d_y@V$（C1）→ 算 $P$ 和 $d_s$（V1）→ $d_s@K$ → $d_k/d_V$ 离散写出核外（V2）。严格按计算图的基础流水会让多阶段串行、产生大量气泡；优化为起步阶段**连续发起两次 V0 和 C1**，接触后续数据依赖，实现 CV 并行掩盖，大幅减少 CV 数据依赖损耗。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/d6dc278a-738c-47fe-8d8d-3359e612cdea.png" width="58%"></p>
<p align="center"><sub>图：SFAG 五阶段流水，起步连发两次 V0+C1 实现 CV 并行掩盖（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SFAG Pipeline 设计）</sub></p>

相较传统 FAG，SFAG 离散访存多且单次量小，访存指令开销大、带宽难发挥。优化：用 **Vector 核把离散数据非连续转连续**排布，以 $128{\times}headDim$ 为基本块放 workspace 临时空间，Cube 侧发起计算时连续搬运输入，显著提升带宽利用率。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v32/62465bee-017c-492c-a0cd-597c32048123.png" width="58%"></p>
<p align="center"><sub>图：Vector 核把离散数据转连续到 workspace、Cube 连续搬运提升带宽（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SFAG 离散访存优化）</sub></p>

> SFAG 算子将在下一个 CANN 版本进一步升级，大幅提升性能（源文档 Future Plan）。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v32_pre_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（『DSA 融合算子』→『SparseFlashAttentionGrad』：5 步反向公式、Tiling 表、五阶段 Pipeline、离散转连续；下一 CANN 版本升级）
- [`torchtitan_npu/converters/kernels/dsa.py`](https://gitcode.com/cann/torchtitan-npu/blob/87221a1beaa55314a1cdb73460346ba3cec0b475/torchtitan_npu/converters/kernels/dsa.py)（`dsa_forward` 中 `npu_sparse_flash_attention` 正向调用 → autograd 触发 SFAG 反向；`return_softmax_lse=True` 训练强制；`@register_npu_converter("npu_dsa")` / `DSAKernel` 注册与 `converters` toml 开关）
- `torchtitan_npu/distributed/context_parallel/dsa_cp.py:199`（CP 场景同一 op，KV 走 `allgather_sequence`）

## Links

- [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)（所属预训练实践）
- [slig](slig.md)（同批 DSA 反向算子，Indexer 反向 + KL Loss；其 `LILossTrain` autograd 绑定与本算子的隐式 autograd 反向形成对照）
- [custom-cp-dsa](../parallelism/custom_cp_dsa.md)（CP 场景下与本算子配合，KV 序列维 AllGather 后喂入同一 SFA op）
- [torchtitan](../frameworks/torchtitan.md)（TorchTitan-npu `npu_dsa` converter 插件化挂载本算子）
- [sparse-flash-attention](../../../inference/concepts/kernels/sparse_flash_attention.md)（跨域：SFA 正向算子，SFAG 是其反向）
- [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)（跨域：LI 正向算子，产 Top-k index 供 SFAG Gather/ScatterAdd）
- [ascendc](../../../inference/concepts/frameworks/ascendc.md)（跨域：Ascend C 算子编程框架）
- [sasg](sasg.md)（同源对应：V4 SAS 统一算子的训练反向，SASG 之于 SAS 等价于 SFAG 之于 SFA）
- [smla](smla.md)（V4 SMLA 与 DSA SFAG 同族）
