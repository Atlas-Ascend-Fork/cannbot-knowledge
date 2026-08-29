---
type: Guide
title: SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径
description: 在 SFA/DSA 稀疏注意力叠加 PCP/DCP 时，各 rank 只保存局部 KV block，而 indexer 会按全局 topk_indices 取块，直接使用本地 block_table 会漏取并造成精度错误。修复是在注意力与 indexer 前按 valid_block_ids 选出有效块，依次执行 DCP all_gather、PCP all_gather 重建完整 KV；顺序不可互换。block_table_cp 通过 unique(return_inverse) 虚拟化，并为各 CP 分片增加 num_blocks 偏移。硬约束是 kv_cache_interleave_size 必须等于 block_size；写 KV 时先 all_gather，再按 restore index 恢复顺序后落 cache。该路径限定 SFA 与 paged KV 的 PA_BSND 布局，gsm8k 在 TP2+PCP2+DCP2+EP、block_size=128 下为 96.35%，未提供吞吐或显存收益。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/6733
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径

## 适用场景

当你要在 Ascend NPU 上把 **稀疏注意力（[SFA](../../../concepts/kernels/sparse_flash_attention.md) / [DSA](../../../concepts/modules/dsa.md)）** 与 **[context parallel](../../../concepts/parallelism/context_parallel.md)（PCP/DCP，序列维分片）** 叠加时，会遇到一个结构性冲突：

- CP 沿序列维把 KV cache 分片，**每个 rank 只持有部分 KV block**；
- 但稀疏注意力/indexer 的取数逻辑是「按 `topk_indices` 从**全量 KV** 里 gather 若干 block」——它必须看到跨整个 CP 组的完整 KV 才能选对 block；
- 因此**直接用 rank 本地的 `block_table` 索引会漏 block**，选出来的 top-k 是残缺的，精度错。

本页给出该场景下的一个可执行做法：**在注意力/indexer 计算前，先 `index_select` 出有效 block、再依次做 DCP all_gather 和 PCP all_gather 重建完整 KV**，并配套一条**硬前置**——`kv_cache_interleave_size` 必须等于 `block_size`。

**落在本页范围内的前提**：分片维是序列维（context parallel，非 head 维 Ulysses 或 batch 维），KV 为 **paged / block 化** 存储（`layout_kv="PA_BSND"`，选择粒度是 block），注意力算子是稀疏选择型（按 top-k 取 block，dense full-attention 不需要这条 gather 路径）。硬前置 `kv_cache_interleave_size == block_size` 见「前置条件」节。

**不适用**：
- head 维并行的稀疏注意力（分片方向不同，重建维度不同）；
- 非 paged KV（选择粒度不是 block，本页的 `block_table` 虚拟化不成立）；
- 换 head_dim 或换到非 SFA 算子时——见「风险 / 边界」，本路径的脏值假设未验证仍成立。

## 问题信号

- 开 PCP/DCP 后稀疏注意力精度掉/结果错乱，但同 config 关 CP（单组）时正常；
- 症状根因是 top-k 选择只在本 rank 的局部 block 上做，跨 CP 组的 block 被漏掉。

## 前置条件

- KV cache 沿 CP 组分片保存（每个节点各存一份局部分片）。
- **硬前置：`kv_cache_interleave_size == block_size`**。这是让「gather 后拼接的完整 KV」与虚拟化后的 `block_table` 索引对齐的必要条件，否则 KV 索引会算错。
- 计算前有一步「重建完整 KV」：SFA 的 `kv` 与 `key_rope`、以及 indexer 的 `key` 都必须先走这条 gather。

## 做什么

### 1. block_table 虚拟化

把每个 rank 的局部 `block_table` 重映射成能索引「gather 后拼接完整 KV」的虚拟 `block_table`：

```python
valid_block_ids, new_block_table = block_table.flatten().unique(return_inverse=True)
```

再对 `pcp_size * dcp_size` 份各偏移 `num_blocks`，生成 `block_table_cp`，使其能索引到 gather 后拼接的完整 KV。承载这些的三个字段（`block_table_cp` / `valid_block_ids` / `prefill_q_cum_seqlens`）挂在 CP metadata 上。

Builder 侧确定虚拟 block 尺寸：

```
cp_local_block_size   = cp_kv_cache_interleave_size
cp_virtual_block_size = cp_local_block_size * dcp_size * pcp_size
```

并据此按 gcd 放大 `block_size`——这正是「`kv_cache_interleave_size == block_size`」硬前置的来源。

### 2. 计算前重建完整 KV

在注意力/indexer 计算前，用 `valid_block_ids` 先 `index_select` 出有效 block，再**依次** DCP、PCP all_gather：

```python
kv_cache = torch.index_select(kv_cache, 0, valid_block_ids)
if self.dcp_size > 1:
    kv_cache = get_dcp_group().all_gather(kv_cache, 0)
if self.pcp_size > 1:
    kv_cache = get_pcp_group().all_gather(kv_cache, 0)
```

顺序不能反：**先 DCP all_gather、再 PCP all_gather**，与 `block_table_cp` 的 `pcp_size * dcp_size` 偏移布局一致。SFA 的 `kv`/`key_rope` 和 indexer 的 `key` 都走这条同一 gather。

### 3. 写 KV 侧（pcp_size > 1）

写 KV cache 时同样体现「先 allgather 再各存一份」：对 `kv_c_k_pe` 做 `get_pcp_group().all_gather(..., 0)`，再按 `pcp_allgather_restore_idx` 用 `torch.index_select` 还原原始顺序，最后 `torch_npu._npu_reshape_and_cache` 落 cache。

## 正确性验证

- 与关 CP（单组）时的稀疏注意力结果对齐；确认 top-k 选出的 block 覆盖了跨 CP 组的全量 KV，无漏 block。
- 端到端精度：`gsm8k accuracy 96.35`（AISBench，`TP2 + PCP2 + DCP2 + EP`，`block_size=128`）——属整体正确性验证，非量化加速收益。

## 性能基准

仅有端到端精度（上），**无吞吐/显存 before→after**。本路径不是加速手段，而是「让稀疏注意力 + CP 组合能算对」的正确性使能路径。

## 风险 / 边界

- **脏值假设**：`block_table_cp` 中超出 `kv_lens` 的部分带脏值，参考实现依赖「总能拿到正确的 `kv_lens` 或 KV 索引」而**不清理脏值**。换 head_dim / 换非 SFA 算子前，必须自查该假设是否仍成立。
- **约束绑定 SFA + paged KV**：`kv_cache_interleave_size == block_size` 前置系于 SFA + paged KV（`layout_kv="PA_BSND"`）的索引方式，只在稀疏注意力 + CP 路径证实过；这是**该参考实现的限制，不是 CP-KV-gather 思想本身的普适限制**。
- gather 会把完整 KV 拉到每个 rank，重建后的 KV 显存随 CP 组规模上升——长序列下需评估重建后 KV 的峰值占用。

## 回退

- 关闭 PCP/DCP（回到单 CP 组）即绕过整条 gather 路径与硬前置；稀疏注意力退回本地全量 KV 计算。
- 若 `kv_cache_interleave_size` 无法对齐到 `block_size`，不要强行开 SFA/DSA + CP —— 索引会错，属于本路径的准入未满足。

## Evidence

- 来源：[vllm-ascend-pr-6733-feat-ds3-2-support-pcp](https://github.com/vllm-project/vllm-ascend/pull/6733)（合并态 commit `db51a1b9b6ee93c8c820b6833e244fe0405559b9`）。
- 合并代码中的对应改动：
  - `vllm_ascend/attention/context_parallel/sfa_cp.py`：`gather_kv_cross_cp` 的 `index_select` + DCP/PCP all_gather、`block_table_cp` 构造、`# we need set kv_cache_interleave_size = block_size for sfa!!!` 注释。
  - `vllm_ascend/attention/context_parallel/common_cp.py`：`AscendPCPMetadata` 新增 `block_table_cp` / `valid_block_ids` / `prefill_q_cum_seqlens` 三个字段。
- 相关 canonical 概念页：[context-parallel](../../../concepts/parallelism/context_parallel.md) · [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md) · [dsa](../../../concepts/modules/dsa.md) · [gather-selection-kv-cache](../../../concepts/kernels/gather_selection_kv_cache.md)

<!-- cannbot:related:start -->
## 相关

- [Context Parallel](../../../concepts/parallelism/context_parallel.md)（`related`）：本页给出该场景下的一个可执行做法：**在注意力/indexer 计算前，先 `index_select` 出有效 block、再依次做 DCP all_gather 和 PCP all_gather 重建完整 KV**，并配套一条**硬前置**——`kv_cache_interleave_size` 必须等于 `block_size`。；将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。指南把 Context Parallel 的 Sequence 分片机制具体化为 DSA/SFA 的 DCP 后 PCP KV 重建顺序和块对齐合同。
- [DSA（DeepSeek Sparse Attention）架构模式](../../../concepts/modules/dsa.md)（`related`）：当你要在 Ascend NPU 上把 **稀疏注意力（［SFA］(../../../concepts/kernels/sparse_flash_attention.md) / ［DSA］(../../../concepts/modules/dsa.md)）** 与 **［context parallel］(../../../concepts/parallelism/context_parallel.md)（PCP/DCP，序列维分片）** 叠加时，会遇到一个结构性冲突：；DSA（DeepSeek Sparse Attention）是一种**注意力架构模式**，不是单个 kernel，也不是 MLA 的替代品。其本质是 **MLA 的 Q/K/V LoRA 计算图 + 一个并行的学习式 indexer overlay**：indexer 与 MLA 共享同一份输入 `x`（及 MLA Q 侧 LoRA 中间量 `qr`），独立打分后为**每个 query 位置**选出 `index_topk` 个最相关的 key，产出一个加性 `-inf` mask；该 mask 在 **softmax 之前**叠加到 MLA 的注意力分数上，把非 top-k 位置置零。指南处理的结构性冲突来自 DSA indexer 必须在跨 CP 完整 KV 范围上产生正确 top-k 选择。
- [Sparse Flash Attention Kernel](../../../concepts/kernels/sparse_flash_attention.md)（`related`）：- 但稀疏注意力/indexer 的取数逻辑是「按 `topk_indices` 从**全量 KV** 里 gather 若干 block」——它必须看到跨整个 CP 组的完整 KV 才能选对 block；。`SparseFlashAttention` 是 DeepSeek-V3.2-Exp **DSA** 的主 Attention 算子 —— 在 ［lightning-indexer］(lightning_indexer.md) 产出的 TopK index 基础上，`Gather` 出稀疏 KV 子集并执行 Flash Attention 计算。沿用 ［FlashAttention］(https://arxiv.org/pdf/2307.08691) 的 `C_1 (Q@K^T) → V_1 (online softmax) → C_2 (P@V) → V_2 (rescale)` 四阶段流程，但面向**离散访存**进行了专门优化。模块语义见 ［sparse-flash-attention］(../modules/sparse_flash_attention.md)。指南修复的跨 CP 全量 KV 重建正是该 SFA TopK Gather 在分片缓存上正确执行的前置条件。
- [长序列 Prefill 注意力优先 Context Parallel（CP 仅 prefill 生效，MoE 复用 CP 域走 EP）](../../../optimizations/experience/rules/long_seq_prefill_context_parallel.md)（`related`）：“CP 计算流水（64K、cp_size 为例）：每 rank 拿 `S/cp_size` 个 q token（DeepSeek-V3.2-Exp 64 卡即 1K/rank），算完本地 KV 后对全 CP 域 KV 做 **AllGather** 得完整 KV，再用本地 q + 完整 KV 做注意力。”；“本页给出该场景下的一个可执行做法：**在注意力/indexer 计算前，先 `index_select` 出有效 block、再依次做 DCP all_gather 和 PCP all_gather 重建完整 KV**，并配套一条**硬前置**——`kv_cache_interleave_size` 必须等于 `block_size`。”。目标指南把焦点的全域 KV AllGather 落到 paged SFA/DSA 的顺序、索引和硬前置。
<!-- cannbot:related:end -->
