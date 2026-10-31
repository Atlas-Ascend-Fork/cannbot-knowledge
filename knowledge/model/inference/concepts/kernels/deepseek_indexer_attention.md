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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_pypto_operator_guide.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto/docs/deepseek_indexer_attention.md
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a3
---
# Deepseek Indexer Attention Kernel

## Summary

本卡覆盖固定版本 PyPTO DIA 的 Atlas A3 实现支持范围；支持平台不等于每组性能观测都有完整测量环境。

`Deepseek Indexer Attention` (DIA) 是 cann-recipes-infer 用 **PyPTO** 实现的**大融合算子** —— 把 DSA 的 4 个相对独立子算子 MLAProlog + IndexerProlog + Lightning Indexer + Sparse Flash Attention 融合成单一 kernel，在整网范围内挖掘更大并行度、提升内存利用率。这是 PyPTO "MegaKernel" 能力在 DeepSeek-V3.2-Exp 上的典型实例。

PyPTO 源码：`ops/pypto/src/deepseek_indexer_attention/op_kernel/deepseek_indexer_attention.cpp`。

## Role In Pipeline

![Deepseek Indexer Attention 计算逻辑](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttention.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/DeepseekIndexerAttention.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/DeepseekIndexerAttention.png)（cann-recipes-infer @ 944d2d3）*

开发策略（源文档）："对于复杂融合算子，可以将复杂融合算子拆分成若干个相对独立的子算子；根据泳道图对各个子算子进行独立性能调优。当各子算子接近最优性能后，再把子算子们进行更大程度的融合，以期获得完整融合算子的最优性能。"

## 计算关系与融合边界

MLA Prolog 生成注意力所需的 Q 与压缩 KV；Indexer Prolog 生成索引查询、键与权重；Lightning Indexer 选择 TopK；Sparse Flash Attention 根据索引消费 KV 并输出注意力结果。PyPTO 将四部分纳入同一任务图，允许独立子链交错调度，但 TopK 到稀疏访存等真实依赖仍需保留。融合范围不表示任意 shape、量化或后端均支持；采用时须核对固定算子接口与模型配置。

## 调优案例

Gather 搬运、合轴、barrier 和 reshape 的具体调整及75%来源观测见[DIA A3 调优案例](../../optimizations/cases/deepseek_indexer_attention_a3_tuning.md)。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [deepseek_v3.2_exp_pypto_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_pypto_operator_guide.md)（supporting）
- [deepseek_indexer_attention.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto/docs/deepseek_indexer_attention.md)（constraint）

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
## 定量观测入口

该来源对旧实现的 Gather 耗时占比披露统一见[分组算子观测](../../optimizations/benchmark_observations/operator_tuning_source_observations.md)，不推导其他负载的固定占比。
