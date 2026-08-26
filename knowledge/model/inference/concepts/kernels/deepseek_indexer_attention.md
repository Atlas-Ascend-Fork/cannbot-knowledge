---
type: Concept
title: Deepseek Indexer Attention Kernel
description: '`Deepseek Indexer Attention` (DIA) 是 cann-recipes-infer 用 **PyPTO** 实现的**大融合算子** —— 把 DSA 的 4 个相对独立子算子 MLAProlog + IndexerProlog + Lightning Indexer + Sparse Flash Attention 融合成单一 kernel，在整网范围内挖掘更大并行度、提升内存利用率。这是 PyPTO "MegaKernel" 能力在 DeepSeek-V3.2-Exp 上的典型实例。 PyPTO 源码：`ops/pypto/src/deepseek_indexer_attention/op_kernel/deepseek_indexer_attention.cpp`。'
tags:
- task.implementation
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Deepseek Indexer Attention Kernel

## Summary

`Deepseek Indexer Attention` (DIA) 是 cann-recipes-infer 用 **PyPTO** 实现的**大融合算子** —— 把 DSA 的 4 个相对独立子算子 MLAProlog + IndexerProlog + Lightning Indexer + Sparse Flash Attention 融合成单一 kernel，在整网范围内挖掘更大并行度、提升内存利用率。这是 PyPTO "MegaKernel" 能力在 DeepSeek-V3.2-Exp 上的典型实例。

PyPTO 源码：`ops/pypto/src/deepseek_indexer_attention/op_kernel/deepseek_indexer_attention.cpp`。

## Role In Pipeline

![Deepseek Indexer Attention 计算逻辑](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention.png)（cann-recipes-infer @ 2f82d10）*

开发策略（源文档）："对于复杂融合算子，可以将复杂融合算子拆分成若干个相对独立的子算子；根据泳道图对各个子算子进行独立性能调优。当各子算子接近最优性能后，再把子算子们进行更大程度的融合，以期获得完整融合算子的最优性能。"

## Performance Signals

### 首版开箱泳道图

首版 DIA 上板后的泳道图：

![DIA 泳道图 V0](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_0.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_0.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_0.png)（cann-recipes-infer @ 2f82d10）*

四个关键性能瓶颈（源文档）：

1. **离散 Gather 部分耗时占比 >70%**：SFA 根据 LI 产出的 TopK index 从 `kv_cache/kr_cache` 离散读取对应 KV —— 原实现在 Vector 核完成"离散到连续"转换后写 GM Workspace，Cube 核再搬到 L1 使用，**既浪费内存又重复搬运**。
2. **Indexer Prolog matmul 任务过多**：M 轴为 1，未合轴 → Matmul 利用率过低。
3. **流水线 bubble 较大**：两个子图之间存在未消除的 barrier，后续无依赖 task 也被停滞。
4. **Reshape 空子图导致启动延迟**：未充分优化的 reshape 形成空子图，依赖其结果的 task 停滞。

### 优化措施

| 瓶颈 | 措施 | | ---- | ---- | | 1 | PyPTO 允许开发者**自定义 Tile Op** —— 开发一个"根据 index 直接从 GM 离散搬运到 L1 连续空间上"的 TileOp，使 Matmul 可直接消费，省去 workspace、消除冗余搬运 | | 2 | **b × s1 合轴** + 调整 Tiling，撑大 M 轴，用满 L0A，提高 Matmul 计算效率（性能倍增） | | 3 | 消除两个子图之间的 barrier —— 把两个子图充分融合，不依赖的 task 提前启动 | | 4 | Reshape 操作不改变数据排布 → 消除 reshape，原依赖 task delay 消除，减少解依赖时间 |

自定义 Gather TileOp 示意：

![自定义 Gather Tile Op](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttentionGather.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttentionGather.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttentionGather.png)（cann-recipes-infer @ 2f82d10）*

### 优化后泳道图

![DIA 泳道图 V1](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_1.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_1.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_1.png)（cann-recipes-infer @ 2f82d10）*

> 源结论："在经过上述分析和优化后，得到新版的泳道图如下，可以看到，使能以上优化措施后，该融合算子的运行时长缩短了 **75%**。"

## Optimization Notes

### 下一步优化方向（源文档列出）

- **任务排布紧凑化**：Task 排布相对离散，调度不够紧密 → 分析任务依赖消除 Pipeline Bubble。
- **SparseAttention 搬运并行度**：离散数据搬运效率较低 → 提高搬运并行度。
- **跨子图融合**：多个子图之间仍存在较大空隙 → 进一步融合，把有数据依赖的计算整合到同一个 LOOP 中。

### Future Plan 关联

DeepSeek-V3.2-Exp 的 Future Plan 明示："MegaKernel：Decode 阶段仍然存在较多流水并行空间，可通过 PyPTO 实现更大范围的 MegaKernel，完成多核 MPMD 并行调度，提升计算效率。"DIA 是这个路径的已落地样例。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md)（DIA 四个瓶颈 + 对应优化 + 75% 运行时缩短）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md) Future Plan（MegaKernel 方向）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/pypto/src/deepseek_indexer_attention/op_kernel/deepseek_indexer_attention.cpp`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/pypto/src/deepseek_indexer_attention/op_kernel/deepseek_indexer_attention.cpp)

## Links

- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)
- [lightning-indexer](../modules/lightning_indexer.md)
- [sparse-flash-attention](../modules/sparse_flash_attention.md)
- [lightning-indexer](lightning_indexer.md)
- [sparse-flash-attention](sparse_flash_attention.md)
- [indexer-prolog](indexer_prolog.md)
- [mla-prolog](mla_prolog.md)
- [pypto](../frameworks/pypto.md)
- [dsa](../modules/dsa.md)（DSA 架构模式，DIA 是其 LI+Prolog+SFA 融合的算子级实现）
