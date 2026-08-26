---
type: Optimization
title: 生成式推荐模型多卡——切超大 embedding 表（vocab-parallel + 阈值门控）
description: 生成式推荐模型多卡——切超大 embedding 表（vocab-parallel + 阈值门控）。token 化的生成式推荐 / ranking 模型（把用户/物品/上下文离散特征统一建模为 token，如 HSTU）多卡推理时，容量瓶颈在超大稀疏 embedding 表（vocab 可达千万~上亿）而非 dense Transformer——与 LLM（参数集中在 dense/attention）相反。对这类模型，dense 层 TP 收益有限，单卡放不下 embedding 才是主瓶颈，所以并行的主切分对象应是 embedding 表。
tags:
- task.optimization
- topic.model_architecture
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/225
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 生成式推荐模型多卡——切超大 embedding 表（vocab-parallel + 阈值门控）

## 适用场景

token 化的生成式推荐 / ranking 模型（把用户/物品/上下文离散特征统一建模为 token，如 [HSTU](../../../concepts/models/hstu.md)）多卡推理时，**容量瓶颈在超大稀疏 embedding 表（vocab 可达千万~上亿）而非 dense Transformer**——与 LLM（参数集中在 dense/attention）相反。对这类模型，dense 层 [TP](../../../concepts/parallelism/tensor_parallel.md) 收益有限，单卡放不下 embedding 才是主瓶颈，所以并行的主切分对象应是 embedding 表。

## 规则

- **切分对象 = 按 vocab 维切大 embedding 表**（[vocab-parallel embedding](../../../concepts/parallelism/embedding_tp.md)，Megatron `VocabParallelEmbedding` 式）：本卡只持有 `[vocab_start, vocab_end)` 段，`start = rank * ceil(vocab_size / tp_size)`。embedding 与 dense 用不同并行度——embedding 走 TP、外层套 [DP](../../../concepts/parallelism/data_parallel.md)。
- **阈值门控（关键判断）**：不是所有表都切。用 `should_shard = (tp_size > 1) and (vocab_size >= threshold)` 门控（本仓默认阈值 1000）；小于阈值的小表整表复制到各卡，**避免小表切分后 all_gather/reduce_scatter 的通信开销 > 省下的那点显存**。给新的大稀疏 embedding 模型上多卡前，先按表规模分档再决定切/不切。
- **sharded 表 lookup 通信模式（DP→TP→DP）**：各卡 local ids 先按全局最大长度 pad → `all_gather` 汇聚所有 DP 分片的 ids → 每卡对不落在本 vocab 段的 id 做 mask（`safe_id = where(mask, id - vocab_start, 0)`，查表结果 `× mask` 越界置零）→ `reduce_scatter` 求和并散回各 DP 分片。每张卡只查自己那段 vocab、跨卡求和得完整 embedding。

## 为什么

- 稀疏 embedding 表是这类模型的主显存/主容量来源，单卡放不下；按 vocab 切让显存随卡数摊薄，是唯一能撑起千万~上亿词表的路子。
- 阈值门控理由是通信/显存权衡：小表切分省的显存有限、却每 step 都要付 all_gather+reduce_scatter 通信，整表复制反而更省时。

## 适用边界

规则适用面限定"embedding 主导容量的稀疏推荐类模型"，不外推为通用 LLM 多卡律（LLM 主切分对象是 dense/attention，不是 embedding）。源未给 embedding TP 的显存/时延 before→after 数字，收益方向（显存随卡数摊薄）为结构性推断而非实测。

## Evidence

- `diff 事实`（HSTU，PR 合并 @67aa6b552d7d）：`inference_embedding.py` 的 `VocabParallelEmbedding` vocab 段切分、`should_shard = (embed_tp_size>1) and (vocab_size>=small_table_threshold)` 阈值门控、forward 的 `all_gather→mask→reduce_scatter`，与 `hstu_optimization.md`「Embedding TP + DP、DP→TP→DP」一致。
- "embedding 主导容量、词表千万上亿"为文档动机；"显存随卡数摊薄"为结构性推断，无实测数字。
- 溯源下探：[cann-recipes-infer-pr-225-feat-add-hstu-model-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/225)
