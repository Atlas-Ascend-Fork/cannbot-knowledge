---
type: Concept
title: Sparse Flash Attention (SFA)
description: DSA 中选定 TopK 后的稀疏注意力，更新 packed 索引、C8 Query 拼接与返回值，保留 Absorb/CP 的模型边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:22:24Z'
platforms:
- agnostic
---
# Sparse Flash Attention (SFA)

## Summary

Sparse Flash Attention 是 **DeepSeek Sparse Attention (DSA)** 的核心计算模块。在由 [lightning-indexer](lightning_indexer.md) 选出 TopK 个相关 KV token 之后，SFA 仅在这部分稀疏子集上执行注意力计算，将复杂度从 O(N²) 降到 O(N·TopK)，配合 Flash Attention 的块级 online softmax 思想。DeepSeek-V3.2-Exp 将其作为长序列推理的主力注意力算子，并在此基础上设计了 CP 并行、MLA Absorb 模式适配。

SFA 作为架构概念是 DSA 的一部分；具体算子实现（AscendC / PyPTO / TileLang）见 [sparse-flash-attention](../kernels/sparse_flash_attention.md)。

## Mechanism

### 计算表达

给定 Query `Q`、完整 Key/Value `K, V`，以及稀疏索引张量 `index`（由 Lightning Indexer 产出，当前 packed 形状 `[T,1,TopK]`；教学 BSND 形态可写为 `[B,Sq,1,TopK]`）：

$$
\text{softmax}\left(\frac{Q \cdot \tilde{K}^T}{\sqrt{d_k}}\right) \cdot \tilde{V}
$$

其中 $\tilde{K}, \tilde{V}$ 是依据 `index` 从完整 KV 中 Gather 出的稀疏子集。对每个 query token，仅与 TopK=2048 个 key token 做 Attention。

![SFA 概念图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/sparse-flash-attention.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/sparse-flash-attention.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/sparse-flash-attention.png)（cann-recipes-infer @ 944d2d3）*

### 与 Full FA 的 Shape 对比（1 batch × 64K）

| | BMM1 (Q·K^T) | BMM2 (P·V) |
| ---- | ---- | ---- |
| Full Attention | `(batch, Sq, d, Sk)` 全 KV | `(batch, Sq, Sk, d)` 全 KV |
| SFA | `(batch*Sq, G, d, TopK)` 稀疏 | `(batch*Sq, G, TopK, d)` 稀疏 |

TopK=2048 vs Sk=64K → 计算量降 32×；但引入**离散访存**（非连续 KV Gather），来源 Atlas A3 AscendC 离散访存实现中，当单次搬运耗时低到小于指令下发耗时，可能出现指令下发阻塞；这不是所有 SFA 实现的固定瓶颈（见 [sparse-flash-attention](../kernels/sparse_flash_attention.md) 的访存优化）。

### MLA Absorb 模式

DeepSeek-V3.2-Exp 的 Prefill 阶段选择 **MLA Absorb + SFA**（方案三，见 [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md) Architecture 段的三方案对比）：

- BMM1 Shape `(1*64K, 128, 576, 2048)` —— M=128 对矩阵乘友好
- BMM2 Shape `(1*64K, 128, 2048, 512)`
- 访存量相对"MLA Naive + Sparse Attention"降低几十倍

理由：Absorb 模式让 Prefill 与 Decode 的 MLA 计算流归一，避免两套代码路径。

## Variants

### 非量化 SFA（BF16）

输入 Q/K/V 均为 BF16/FP16，按 `npu_sparse_flash_attention` 接口调用（`models/modeling_deepseek.py:L1409`）：

```python
slc_fa_fusion, _, _ = torch_npu.npu_sparse_flash_attention(**slc_fa_input_kwargs)
```

关键参数（来自 modeling_deepseek.py:L1373）：

```python
slc_fa_input_kwargs = {
 "query": q_nope, "key": k_nope, "value": k_nope,
 "sparse_indices": topk_indices, # 由 Lightning Indexer 产出
 "scale_value": self.softmax_scale,
 "actual_seq_lengths_query": actual_seq_qlen.to(torch.int32),
 "actual_seq_lengths_kv": actual_seq_lengths_kv.to(torch.int32),
 "block_table": block_table,
 "sparse_block_size": 1,
 "layout_query": 'TND',
 "layout_kv": 'PA_BSND',
 "sparse_mode": 3,
 "attention_mode": 2,
 "query_rope": q_pe, "key_rope": k_pe,
}
```

### KV C8 量化 SFA（算 16 存 8）

KVCache Int8 存储、BF16 计算。入口切换到 `npu_kv_quant_sparse_flash_attention`（`modeling_deepseek.py:L1402`），Query 拼接 NoPE/RoPE；量化入口直接返回输出 Tensor，非量化返回三项，另传 `tile_size=128`、`rope_head_dim=64`、`key/value_quant_mode=2`、`quant_scale_repo_mode=1`。见 [w8a8c8](../quantization/w8a8c8.md)。

### Offload 路径变体

当 `enable_offload: True` 且 decode 阶段，KV 来自 Host，SFA 的 `key/value` 指向由 [gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md) 预先聚合好的 `selection_kv_cache`，`block_table` 指向 `selection_kv_block_table`；`sparse_indices` 使用 `torch.where(default_topk_indices < selection_kv_actual_seq.unsqueeze(1), default_topk_indices, -1)` 生成（见 `modeling_deepseek.py:L1340-L1366`）。

## Performance Characteristics

### 对 MTP 的差异化表现

MTP 的访存与计算量分析由[DSA 模块分析案例](../../optimizations/cases/mtp_benefit_sparse_attention_and_latency_metric.md)维护。每个 query 的 TopK 选择会影响搬运复用，需按工作负载验证，不把分析量当作整网时延测量。

### CP 并行下的负载均衡

Prefill CP 场景下，因果注意力按 rank 切片会导致首 rank 轻、尾 rank 重。DeepSeek-V3.2-Exp 的做法：input_ids 按 `cp_size × 2` 切片，每 rank 负责头尾对称两片，LI/SFA 计算前用 Token 重排还原因果顺序。思路与 [zigzag-cp](../parallelism/zigzag_cp.md) 同源。

## Evidence

- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）

## Links

- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)
- [lightning-indexer](lightning_indexer.md)
- [mla](mla.md)
- [sparse-flash-attention](../kernels/sparse_flash_attention.md)
- [gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md)
- [kvcache-offload](../techniques/kvcache_offload.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [context-parallel](../parallelism/context_parallel.md)
- [dsa](dsa.md)（SFA 是 DSA 稀疏注意力路径的计算/kernel 形态）
