---
type: Optimization
title: DIA A3 大融合算子的泳道图调优案例
description: 固定 PyPTO DIA 实现的 Gather、Matmul、barrier 与 reshape 调优，保留75%运行时缩短的来源口径和复测边界。
tags:
- task.implementation
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_pypto_operator_guide.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto/docs/deepseek_indexer_attention.md
  role: constraint
created_at: '2026-10-29T09:38:05Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- a3
---

# DIA A3 大融合算子的泳道图调优案例

## 条件与来源

本案例保留固定 PyPTO DIA 的 Gather、Matmul、barrier 和 reshape 调优过程。来源自报运行时缩短75%，没有完整 shape、重复次数及方差，本仓未独立复测；不能当作其他负载的固定收益。

## Performance Signals

### 首版开箱泳道图

首版 DIA 上板后的泳道图：

![DIA 泳道图 V0](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttention_0.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_0.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttention_0.png)（cann-recipes-infer @ 944d2d3）*

四个关键性能瓶颈（源文档）：

1. **离散 Gather 是来源泳道图中的主要瓶颈**：SFA 根据 LI 产出的 TopK index 从 `kv_cache/kr_cache` 离散读取对应 KV —— 原实现在 Vector 核完成"离散到连续"转换后写 GM Workspace，Cube 核再搬到 L1 使用，**既浪费内存又重复搬运**。
2. **Indexer Prolog matmul 任务过多**：M 轴为 1，未合轴 → Matmul 利用率过低。
3. **流水线 bubble 较大**：两个子图之间存在未消除的 barrier，后续无依赖 task 也被停滞。
4. **Reshape 空子图导致启动延迟**：未充分优化的 reshape 形成空子图，依赖其结果的 task 停滞。

### 优化措施

| 瓶颈 | 措施 |
| ---- | ---- |
| 1 | PyPTO 允许开发者**自定义 Tile Op** —— 开发一个"根据 index 直接从 GM 离散搬运到 L1 连续空间上"的 TileOp，使 Matmul 可直接消费，省去 workspace、消除冗余搬运 |
| 2 | **b × s1 合轴** + 调整 Tiling，撑大 M 轴，用满 L0A，提高 Matmul 计算效率（性能倍增） |
| 3 | 消除两个子图之间的 barrier —— 把两个子图充分融合，不依赖的 task 提前启动 |
| 4 | Reshape 操作不改变数据排布 → 消除 reshape，原依赖 task delay 消除，减少解依赖时间 |

自定义 Gather TileOp 示意：

![自定义 Gather Tile Op](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttentionGather.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttentionGather.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttentionGather.png)（cann-recipes-infer @ 944d2d3）*

### 优化后泳道图

![DIA 泳道图 V1](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttention_1.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention_1.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttention_1.png)（cann-recipes-infer @ 944d2d3）*

> 源结论："在经过上述分析和优化后，得到新版的泳道图如下，可以看到，使能以上优化措施后，该融合算子的运行时长缩短了 **75%**。"

## Optimization Notes

### 下一步优化方向（源文档列出）

- **任务排布紧凑化**：Task 排布相对离散，调度不够紧密 → 分析任务依赖消除 Pipeline Bubble。
- **SparseAttention 搬运并行度**：离散数据搬运效率较低 → 提高搬运并行度。
- **跨子图融合**：多个子图之间仍存在较大空隙 → 进一步融合，把有数据依赖的计算整合到同一个 LOOP 中。

### Future Plan 关联

DeepSeek-V3.2-Exp 的 Future Plan 明示："MegaKernel：Decode 阶段仍然存在较多流水并行空间，可通过 PyPTO 实现更大范围的 MegaKernel，完成多核 MPMD 并行调度，提升计算效率。"DIA 是这个路径的已落地样例。


## 验证与回退

在目标输入上分别核对输出、workspace 与依赖时间线，并对比逐项变更前后的设备时间。质量异常或端到端无净收益时恢复原算子与调度。

## 相关入口

- [DIA 计算关系与融合边界](../../concepts/kernels/deepseek_indexer_attention.md)
- [分组算子来源观测](../benchmark_observations/operator_tuning_source_observations.md)
