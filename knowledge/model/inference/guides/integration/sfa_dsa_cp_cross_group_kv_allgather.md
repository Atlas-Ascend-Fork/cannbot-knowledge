---
type: Guide
title: SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径
description: 固定 vLLM Ascend SFA/DSA + PCP/DCP 集成路径：选择有效 block，依次 DCP→PCP all_gather，并对齐 CP KV 交错粒度；该版本 PCP Prefill 不支持 MLAPO。A3 配置与数据流已有源码依据；PR 精度数字的平台仍未知。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/6733
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/vllm_ascend/attention/context_parallel/sfa_cp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/vllm_ascend/attention/context_parallel/common_cp.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/tests/e2e/multicard/4-cards/long_sequence/test_basic.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/tests/e2e/nightly/multi_node/config/DeepSeek-V3_2-W8A8-cp.yaml
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/db51a1b9b6ee93c8c820b6833e244fe0405559b9/docs/source/tutorials/models/DeepSeek-V3.2.md
  role: supporting
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-26T03:49:31Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      parallelism:
        all_of:
        - cp
      framework:
      - vllm
---

# SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径

## 适用场景

当你要在 Ascend NPU 上把 **稀疏注意力（[SFA](../../concepts/kernels/sparse_flash_attention.md) / [DSA](../../concepts/modules/dsa.md)）** 与 **[context parallel](../../concepts/parallelism/context_parallel.md)（PCP/DCP，序列维分片）** 叠加时，会遇到一个结构性冲突：

- CP 沿序列维把 KV cache 分片，**每个 rank 只持有部分 KV block**；
- 但稀疏注意力/indexer 的取数逻辑是「按 `topk_indices` 选择候选 KV token」；候选 token 的全局序列索引必须映射到跨 CP 组重建后的 KV；
- 因此**直接用 rank 本地的 `block_table` 索引会漏 block**，选出来的 top-k 是残缺的，精度错。

本页按固定源码与 A3 配置给出一条待目标环境验收的集成路径：**在注意力/indexer 计算前，先 `index_select` 出有效 block、再依次做 DCP all_gather 和 PCP all_gather 重建完整 KV**，并配套一条**硬前置**——`kv_cache_interleave_size` 必须等于 `block_size`。

**落在本页范围内的前提**：分片维是序列维（context parallel，非 head 维 Ulysses 或 batch 维），KV 为 **paged / block 化** 存储（`layout_kv="PA_BSND"`，存储粒度是 block，稀疏选择粒度是 token（sparse_block_size=1）），注意力算子是稀疏选择型（按 top-k 取 token；其他 attention 的通信路径另行核对）。硬前置 `kv_cache_interleave_size == block_size` 见「前置条件」节。

**不适用**：
- head 维并行的稀疏注意力（分片方向不同，重建维度不同）；
- 非 paged KV（本页基于存储块的 `block_table` 虚拟化不适用）；
- 换 head_dim 或换到非 SFA 算子时——见「风险 / 边界」，本路径的脏值假设未验证仍成立。

## 问题信号

- 开 PCP/DCP 后稀疏注意力精度掉/结果错乱，但同 config 关 CP（单组）时正常；
- 症状根因是 KV 索引仍指向本 rank 的局部存储，跨 CP 组的候选 token 无法正确取数。

## 前置条件

- KV cache 沿 CP 组分片保存（每个节点各存一份局部分片）。
- **固定版本的组合限制**：`db51a1b9b6ee93c8c820b6833e244fe0405559b9` 的 SFA PCP Prefill **不支持 MLAPO**。采用本页路径前须核对实际 Prefill、PCP 与 MLAPO 配置，避开该组合；本卡 Scope 只声明框架与 CP，未覆盖这个开关限制。DCP、Decode 和其他版本的兼容性分别按对应实现核验。
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

- 与关 CP（单组）时的稀疏注意力结果对齐；逐项核对候选 token 的全局索引与 block_table/重建 KV 的映射，覆盖跨 CP 组边界；不要求 Top-k 等于全量 KV。
- PR 自报 AISBench `gsm8k accuracy 96.35`。PR 正文未给出能绑定此分数的硬件及完整启动配置，不将它与源码中的 `TP2 + PCP2 + DCP2 + EP` 测试参数或 A3 夜间配置拼成同一次测量，也不称为本仓复现。

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
  - 同文件的 `AscendSFACPMetadataBuilder` 与 `AscendSFACPImpl` 初始化处均注明 `pcp prefill does not support mlapo`；本页据此记录该固定版本的兼容边界，未执行该组合的设备测试。
  - `vllm_ascend/attention/context_parallel/common_cp.py`：`AscendPCPMetadata` 新增 `block_table_cp` / `valid_block_ids` / `prefill_q_cum_seqlens` 三个字段。
- 相关 canonical 概念页：[context-parallel](../../concepts/parallelism/context_parallel.md) · [sparse-flash-attention](../../concepts/kernels/sparse_flash_attention.md) · [dsa](../../concepts/modules/dsa.md) · [gather-selection-kv-cache](../../concepts/kernels/gather_selection_kv_cache.md)

## 平台证据与集成验收

同提交的 DeepSeek-V3.2 文档明确 A3 部署，`DeepSeek-V3_2-W8A8-cp.yaml` 提供含 `ASCEND_A3_EBA_ENABLE=1` 的 DCP 部署，PR 新增端到端用例包含该稀疏模型的 PCP/DCP 组合。仅按这些固定配置声明 A3，不将 PR 精度数字绑定到 A3，也不代表本仓硬件复测。接入时保存单卡/无 CP 对照，检查有效 block 数、DCP→PCP 聚合顺序、重建 KV 的形状与索引；覆盖无有效 token 和跨组边界，输出不对齐时关闭该 CP 组合。

## 本轮来源核对与剩余缺口

平台与实现范围按固定文档、配置及测试代码核对；没有执行这些测试。PCP/DCP 测试文件中的参数、A3 夜间部署与 PR 的 96.35 分数是三份独立证据，不能混为一份运行记录。

实际配置字段为 `parallel_config.cp_kv_cache_interleave_size`，CLI 为 `--cp-kv-cache-interleave-size`；源码注释中的 `kv_cache_interleave_size` 是其简称。该 SFA 路径要求它与 `block_size` 对齐，不将此限制泛化到所有 CP 算法。Scope 仅声明框架与 CP 条件，阶段及其他条件保留未知，不新增 verified。
