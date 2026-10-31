---
type: Concept
title: SFAG（SparseFlashAttentionGrad，DSA 稀疏注意力反向算子）
description: DSA 主注意力反向的数学与离散访存优化，以及当前 DeepSeek-V3.2 TND AscendC backend、softmax 统计量、CP metadata 和显式 override 接入契约。
tags:
- task.implementation
- topic.attention
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/ascendc.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/__init__.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/fused_ops.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- a3
---

# SFAG（DSA 稀疏注意力反向）

## Summary

SFAG 是 Sparse Flash Attention 的训练反向，重建 TopK 位置的 softmax 并计算 Q/K/V 梯度。当前 TorchTitan NPU 的 `AscSparseInnerAttention` 调用 `torch_npu.npu_sparse_flash_attention`，其 autograd 注册触发主注意力反向；[SLIG](slig.md) 是另一条 Indexer 梯度与 KL 分支，时机和归一化不同。

## 计算逻辑


反向整体分五步（$P$ 为正向 softmax 结果，$Top\text{-}k\ index$ 来自 [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)，$d$ 为头维度）：

1. **Gather**：$K_{topk} = \mathrm{Gather}(K,\ Top\text{-}k\ index)$
2. **重计算** SFA 正向 softmax：$P = \mathrm{Softmax}(Q\,@\,K_{topk}^\top/\sqrt{d})$
3. $dP = dY\,@\,V^\top$
4. $dS = P \ast (dP - \mathrm{FlashSoftmaxGrad}(dY\,@\,attention\_in))$；`FlashSoftmaxGrad` 输入为反向梯度 `dY` 与正向输出 `attention_in`
5. 链式求梯度：$dQ = dS\,@\,K_{topk}/\sqrt{d}$；$dK = \mathrm{ScatterAdd}(dS^\top@Q/\sqrt{d},\ Top\text{-}k\ index)$；$dV = P^\top@dY$

第 2 步重计算（而非缓存全量 $P$）与 SLIG 同理，是显存/算力权衡；$softmax\_max$/$softmax\_sum$ 由正向透传，反向据此重建 softmax 而无需重跑 Top-k 选择。


## 当前后端接入与边界

显式启用 `torchtitan_npu.override.deepseek_v3_2.sparse_attn.asc`，由替换后的 Config 构造融合 attention 及共享 metadata，不再设置 npu_dsa converter 或旧 TOML converters。

当前 `AscSparseInnerAttention.forward` 将 Q/K/RoPE/Indexer 输入折为 TND，LI 用 `sparse_count=index_topk`、sparse_mode3 生成稀疏索引；SFA 使用 TND/TND、attention_mode2（MLA absorb）、query_rope/key_rope，且 `return_softmax_lse=True`。max/sum 还交给 Indexer loss；训练必须保留这条统计量链路。

CP 的 key 顺序由当前 CPVarlenMetadata 和 k_global_gather_indices 恢复，Q/K 累计 offset 来自 rank-local metadata，不能沿用旧 BSND 的 allgather 后按单个 slice_end 裁剪示例。aux loss 用全局有效 token 分母，不应给 SFAG 主路重复加入 Indexer 的缩放。

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

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/d6dc278a-738c-47fe-8d8d-3359e612cdea.png" width="58%"></p>
<p align="center"><sub>图：SFAG 五阶段流水，起步连发两次 V0+C1 实现 CV 并行掩盖（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SFAG Pipeline 设计）</sub></p>

相较传统 FAG，SFAG 离散访存多且单次量小，访存指令开销大、带宽难发挥。优化：用 **Vector 核把离散数据非连续转连续**排布，以 $128{\times}headDim$ 为基本块放 workspace 临时空间，Cube 侧发起计算时连续搬运输入，显著提升带宽利用率。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v32/62465bee-017c-492c-a0cd-597c32048123.png" width="58%"></p>
<p align="center"><sub>图：Vector 核把离散数据转连续到 workspace、Cube 连续搬运提升带宽（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md">DeepSeek-V3.2 预训练优化文档</a>·SFAG 离散访存优化）</sub></p>

> 来源包含后续内核优化计划，但没有给出可据此断言当前已交付的性能数据；部署验收以实际 kernel 和测量为准。


## Evidence

- [deepseek-v32_pre_train_optimization.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v32_pre_train_optimization.md)（primary）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/ascendc.py)（implementation）
- [__init__.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/__init__.py)（implementation）
- [fused_ops.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/fused_ops.md)（supporting）

## Links

- [SLIG](slig.md)
- [训练 CP](../parallelism/custom_cp_dsa.md)
- [V3.2 训练](../../guides/recipes/deepseek_v32_pretrain.md)
- [SFA 推理](../../../inference/concepts/kernels/sparse_flash_attention.md)
- [V4 SASG](sasg.md)
