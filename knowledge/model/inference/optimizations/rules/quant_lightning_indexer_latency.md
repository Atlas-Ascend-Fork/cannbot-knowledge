---
type: Optimization
title: 压 LightningIndexer 单算子时延优先切量化算子 npu_quant_lightning_indexer（INT8 Q/K 与混合精度计算）
description: 昇腾 Atlas A3 上做 DeepSeek 系 dsa（DeepSeek 稀疏 attention，deepseek-v3.2-exp 使用）推理，需要降低 lightning-indexer 的单算子时延时：从 fp16 非量化版切到量化版算子 npu_quant_lightning_indexer——Q/K 以 INT8 存储并参与首轮矩阵乘，累加为 INT32 后转 FP16，后续矩阵乘、反量化及 Vector Top-k 使用混合精度，该量化版对 Vector 做了优化。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/23
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:19Z'
platforms:
- a3
---

# 压 LightningIndexer 单算子时延优先切量化算子 npu_quant_lightning_indexer（INT8 Q/K 与混合精度计算）

## 条件 → 优先尝试

昇腾 Atlas A3 上做 DeepSeek 系 [dsa](../../concepts/modules/dsa.md)（DeepSeek 稀疏 attention，[deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md) 使用）推理，需要**降低 [lightning-indexer](../../concepts/kernels/lightning_indexer.md) 的单算子时延**时：从 fp16 非量化版切到量化版算子 **`npu_quant_lightning_indexer`**——Q/K 以 INT8 存储并参与首轮矩阵乘，累加为 INT32 后转 FP16，后续矩阵乘、反量化及 Vector Top-k 使用混合精度，该量化版对 Vector 做了优化。

LightningIndexer 是 DSA 的前处理算子：计算 index query × index key 相关性，经 ReLU、沿 head 加权归约后，在上下文 key 序列维选择 Top-k 索引，长序列下是稀疏注意力的时延热点之一。

## 依据

维护者确认：量化版已发布、对 Vector 做了优化，列为该场景推荐路径。算子调用约定 / 参数 / 约束（INT8 Q/K、Per-Token-Head 量化、`layout_key=PA_BSND`、N1=64、D=128、`sparse_count`、图模式支持、需配 `..._metadata` 先算分核信息等）为 canonical 静态内容，见 [lightning-indexer](../../concepts/kernels/lightning_indexer.md)，此处不复制其规格。DSA 长序列 Prefill 的并行选型另见 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md)。

## 取舍 / 反例 / rollback

- INT8 引入 Q/K 精度取舍；量化版比 fp16 版有更强的布局/量化约束（见静态页）。
- **无量化前后收益数字**：仓自报 BSZ=16 / seq_len=8k 下 fp16 版 ~60us 及 top-k 耗时占比，但维护者显式推迟「测试确认后再答复」、该讨论内未给确认；故加速幅度不可量化，不写任何量化收益 / 单调规律。
- rollback：回退到 fp16 非量化 LightningIndexer 路径。

## 相关经验
- [DSA IndexCache 跨层 top-k 复用观测（草稿）](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/23)（evidence）
