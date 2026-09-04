---
type: Concept
title: AICPU Scheduler（值依赖分核下沉 ARM 核）
description: AICPU Scheduler 将稀疏注意力 SAS、LightningIndexer 等值依赖算子的分核策略从 Host 或主 AICore 下沉到芯片内 AICPU，生成可复用 metadata，避免 Host 往返或在主核内计算分核打断流水。流程拆成两段：Host 根据 shape 计算最大 workspace、tiling key、block dim 和静态 tiling data；AICPU 再结合 actualSeqLengths 等运行时值完成具体分核。DeepSeek-V4 通过三个 custom metadata 算子覆盖 SAS 非量化、SAS KV 伪量化和量化 LI，并可用独立 metadata stream 掩盖开销。它适合需要入图且分核依赖运行时值的场景；与 V3.2-Exp 将 LI 分核融入 AICore 主算子的机制不同，两者不存在已证实的取代关系。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md
  role: primary
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# AICPU Scheduler（值依赖分核下沉 ARM 核）

## Summary

**AICPU Scheduler** 是 DeepSeek-V4 引入的一种**值依赖分核下沉**优化：把 Attention / Lightning Indexer 这类"值依赖算子"的分核策略计算，从 Host 或 AICore 下沉到昇腾芯片内置的 **AICPU（若干个 ARM 计算核）**上独立执行，产出蕴含分核信息的 metadata 供后续 NPU 算子消费。

Scheduler 的核心职能是**执行流的静态预演与管控**：通过预分配显存、锁定执行分支、优化分核策略，消除运行时开销、保持指令流水线饱和。它是一种跨 [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)（SAS）与 [lightning-indexer](../kernels/lightning_indexer.md)（LI）复用的**技术机制**，而非单个算子——SAS 与 LI 各自发布了对应的 AICPU Scheduler 算子。

## 问题：值依赖算子的分核困境

对 Attention 及 LI 这类"值依赖算子"，仅靠输入的 **shape 信息无法得到好的分核策略**——还需要在运行时获取**实际的上下文长度**（`actualSeqLengths`）才能均衡各核计算负载。两种朴素做法都有代价：

- **回 Host 执行 Scheduler**：会打断整体执行流水（host bound）；
- **在算子 kernel 内计算分核**：这部分计算耗时**无法被掩盖**，引入极大的头开销。

AICPU（ARM 核）下沉同时规避两者：既保证算子**入图**，又让分核计算耗时**被掩盖**。

## 机制：Scheduler 两段拆分（host-shape vs 值依赖）

AICPU Scheduler 把整个 Scheduler 过程拆成两部分：

**① 只需 shape 即可计算的部分（由 Host 执行）：**

- **max workspace**：提前为算子分配足够 device 空间；
- **tiling key**：确定实际编译的算子模板；
- **block dim**：确定开核情况；
- **tiling data**：提取实际 shape 做常量折叠，减少算子运行时标量计算。

**② 需要实际上下文长度才能算的部分（下沉 AICPU）：**

- **具体的分核策略**：每核要执行的实际计算部分，提高负载均衡以实现高算力利用率。

第二部分被单独定义为一个 **AICPU 算子**，其输出（metadata）供实际的 NPU 算子使用。代码侧三个 `torch.ops.custom` AICPU 算子：`npu_sparse_attn_sharedkv_metadata`（SAS 非量化）、`npu_kv_quant_sparse_attn_sharedkv_metadata`（SAS 伪量化）、`npu_quant_lightning_indexer_metadata`（LI）。

```python
# run in aicpu
metadata = torch_npu.npu_sparse_attn_sharedkv_metadata(......)
# run in aicore
npu_result, softmax_lse = torch.ops.custom.npu_sparse_attn_sharedkv(..., metadata=metadata, ...)
```

## 三大优势

- **更灵活**：框架侧不需额外识别这类特殊的"值依赖"算子，也减轻算子侧适配框架的工作量；
- **aclgraph 友好**：用户通过脚本直接调用 AICPU 算子即可，对 aclgraph 等图模式更为友好（见 [npu-graph-mode](npu_graph_mode.md)）；
- **metadata 复用**：对单次推理而言，每种计算模式对应的 AICPU Scheduler 算子**只需执行一次、可复用**。

## V4 代码落地：metadata 按计算模式分别生成

V4 在前向开始时统一生成各计算模式的 kernel metadata（`modeling_deepseek.py:generate_kernel_metadata`，L2020-2052）：

- 按层的 compress ratio 分别构造 `c1a_metadata` / `c4a_metadata` / `c128a_metadata`（SAS）以及 `lightning_indexer_quant`（LI，仅 C4A 层、`li_cache_quant_mode` 为 int8/float8 时）；
- 调用 `calc_sas_metadata` / `calc_li_metadata`（L1955-1965）执行对应 AICPU 算子，结果写入 `attn_metadata['kernel_metadata'][...]`，后续 SAS（`prepare_fa_kwargs` 取 `metadata=...`）与 LI（`indexer` 取 `kernel_metadata['lightning_indexer_quant']`）消费；
- **host-shape 拆分对应代码**：`generate_sas_metadata_kwargs` / `generate_li_metadata_kwargs`（L1984-2018）只携带纯 shape / 配置入参（`cmp_ratio`、`ori_mask_mode`、`num_heads_q`、`head_dim`、`sparse_count`、`layout_*` 等），运行时上下文长度（`cu_seqlens_q` / `seqused_kv` / `actual_seq_lengths_query/key`）在 `calc_*_metadata` 内补入再交 AICPU；
- metadata 生成可走独立 `metadata_stream`（`enable_multi_streams` 时），用 `record_event` / `wait_event` 与主流同步，进一步掩盖开销。

## 与 LI AICore 内分核下沉的区分（机制差异 / 演进）

V3.2-Exp 阶段 [lightning-indexer](../kernels/lightning_indexer.md) 曾把分核计算**从 AICPU 下沉到 AICore 内部**（消除 Tiling 依赖前序算子的调度开销、简化调用链）。V4 这里的 AICPU Scheduler 方向相反——把值依赖分核**独立为 AICPU 算子**。二者并非同一机制：

| 维度 | V3.2-Exp LI 分核下沉 | V4 AICPU Scheduler |
| ---- | ---- | ---- |
| 下沉目标 | AICore 内部（算子 kernel 内） | AICPU（独立 ARM 核算子） |
| 形态 | 融进主算子，无独立分核算子 | 独立 `*_metadata` 算子，输出 metadata 入参 |
| 覆盖 | 单 LI 算子内部优化 | 跨 SAS / LI 复用的统一机制 |
| 图模式 | 简化调用链 | aclgraph 友好、metadata 单次复用 |

> 待验证（演进归属，源未明示）：源文档未直接说明 V4 的 AICPU Scheduler 是对 V3.2-Exp "AICore 内分核下沉" 的取代、并存还是按算子/场景择优。此处仅按各自 guide 与代码记录两种机制并存的事实，不臆测演进取代关系。对同样有实时 Scheduler 需求的算子，源文档指出也可自定义开发 AICPU Scheduler 算子。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_ascendc_operator_guide.md)（AICPU Scheduler 节——值依赖困境、两段拆分、三优势、SAS/LI AICPU Scheduler 算子链接）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/models/modeling_deepseek.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modeling_deepseek.py)（实现：`sas_metadata_ops = torch.ops.custom.npu_sparse_attn_sharedkv_metadata`（L1753）/ 伪量化 `npu_kv_quant_sparse_attn_sharedkv_metadata`（L1755）；`calc_li_metadata` 调 `npu_quant_lightning_indexer_metadata`（L1965）；`generate_kernel_metadata` 按 c1a/c4a/c128a 分别生成（L2020-2052）；`generate_sas_metadata_kwargs`/`generate_li_metadata_kwargs` 纯 shape 入参（L1984-2018）；`calc_sas_metadata` 补 `cu_seqlens_q`/`seqused_kv`（L1955-1960）；`metadata_stream` 多流同步）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/models/modules/indexer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modules/indexer.py)（实现：LI 消费 `attn_metadata["kernel_metadata"]["lightning_indexer_quant"]`，L214）
- 上游算子仓：[SAS AICPU Scheduler](https://gitcode.com/cann/ops-transformer/tree/ca41b0b5eb9dbf6eb94a58aa20fe379681c1d751/experimental/attention/sparse_attn_sharedkv_metadata)、[LI AICPU Scheduler](https://gitcode.com/cann/ops-transformer/tree/ca41b0b5eb9dbf6eb94a58aa20fe379681c1d751/experimental/attention/quant_lightning_indexer_metadata)（源文档引用的独立算子库；内部实现未作源码级验证）
- 溯源（diff `2f82d10..2c45117` + MR）：`5df82b1` support deepseek v4（!366 merge publish into master）随 V4 0day 引入 SAS/LI AICPU Scheduler；`985b882` 更新 deepseek_v4_ascendc_operator_guide（!367）；`5e9e41d` Edit V4 AscendC Operator Guide（!375）补充 AICPU Scheduler 节。

## Links

- [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [deepseek-v4](../models/deepseek_v4.md)
- [npu-graph-mode](npu_graph_mode.md)
- [ascendc](../frameworks/ascendc.md)
- [ascend-950](../platforms/ascend_950.md)（值依赖分核下沉芯片内置 AICPU 的硬件平台之一，与 A3 同机制）
- [pypto](../frameworks/pypto.md)（PyPTO MPMD 运行时由 AICPU 调度器拓扑下发任务 + 完成回调解依赖）

<!-- cannbot:related:start -->
## 相关

- [SparseAttnSharedKV (SAS) Kernel](../kernels/sparse_attn_sharedkv.md)（`related`）：**AICPU Scheduler** 是 DeepSeek-V4 引入的一种**值依赖分核下沉**优化：把 Attention / Lightning Indexer 这类"值依赖算子"的分核策略计算，从 Host 或 AICore 下沉到昇腾芯片内置的 **AICPU（若干个 ARM 计算核）**上独立执行，产出蕴含分核信息的 metadata 供后续 NPU 算子消费。；SAS 与 LI 属"值依赖算子"：仅靠输入 shape 无法得到好的分核策略，还需运行时**实际上下文长度**。。机制卡给出值依赖分核下沉与 metadata 生产合同，SAS 卡给出该机制在 SparseAttnSharedKV 中的具体输入依赖和 metadata 消费点。
<!-- cannbot:related:end -->
