---
type: Concept
title: Embedding Tensor Parallel
description: Embedding Tensor Parallel（Embedding TP）是针对**稀疏参数占主导**的推荐/生成式推荐模型的并行策略：把超大规模的 **Embedding Tables 按 vocab 维度切分**到多张 NPU 上，以减少单卡显存负担，支撑超大 Embedding 词表的推理。在 cann-recipes-infer 中首次用于 hstu（Meta 生成式推荐模型）。 与 LLM 的 tensor-parallel 切 Attention Head / FFN 隐藏维度不同：LLM 参数主要集中在 dense Transformer 权重里，输入 token 来自相对固定的文本词表；而**生成式推荐往往把用户、物品、上下文等离散特征统一建模为 token，模型容量绝大部分来自超大规模的稀疏参数（Embedding Tables），词表规模可达千万甚至上亿**。
tags:
- task.design
- topic.parallelism
- topic.model_architecture
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/hstu_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hstu/modules/inference_embedding.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- agnostic
---

# Embedding Tensor Parallel

## Summary

Embedding Tensor Parallel（Embedding TP）是针对**稀疏参数占主导**的推荐/生成式推荐模型的并行策略：把超大规模的 **Embedding Tables 按 vocab 维度切分**到多张 NPU 上，以减少单卡显存负担，支撑超大 Embedding 词表的推理。在 cann-recipes-infer 中首次用于 [hstu](../models/hstu.md)（Meta 生成式推荐模型）。

与 LLM 的 [tensor-parallel](tensor_parallel.md) 切 Attention Head / FFN 隐藏维度不同：LLM 参数主要集中在 dense Transformer 权重里，输入 token 来自相对固定的文本词表；而**生成式推荐往往把用户、物品、上下文等离散特征统一建模为 token，模型容量绝大部分来自超大规模的稀疏参数（Embedding Tables），词表规模可达千万甚至上亿**。

## Mechanism

基于上述稀疏容量差异，cann-recipes-infer 在推理侧引入 Embedding TP：**对大表按 vocab 维度切分到不同 NPU 上**，以减少单卡显存负担，支撑模型推理。同时，在 Embedding TP 外采用 DP 进行并行处理——Embedding 部分执行 **DP → TP → DP** 的切换。

**vocab-range 掩码 + 置零再规约**（`inference_embedding.py` 钉定实现）：`VocabParallelEmbedding` 按 `input_size_per_partition = ceil(vocab_size / tp_size)` 将词表等分，每个 rank 仅持有连续区间 `[vocab_start_index, vocab_end_index)`（`vocab_start_index = tp_rank * input_size_per_partition`），本地 `nn.Embedding` 的 `num_embeddings` 即该分片大小。forward 里：

1. 先用 _get_global_max_length 的 AllReduce(MAX) 确定 padding 长度，再 all_gather_into_tensor 把各卡（padding 对齐后的）全局 id 聚合到每张卡；
2. 用 `new_input_ids = all_input_ids - vocab_start_index` 把全局 id 平移到本 rank 的本地索引空间；
3. 用区间掩码 `mask = (new_input_ids >= 0) & (new_input_ids < vocab_size_per_rank)` 过滤本 rank 不持有的 id，越界 id 经 `safe_input_ids = torch.where(mask, new_input_ids, 0)` 安全查表后，结果 `tp_embeddings = tp_embeddings * mask.unsqueeze(-1)` **乘掩码置零**；
4. 最后 `reduce_scatter_tensor` 把各卡的（已置零无效项的）部分向量求和并拆回 DP batch，等价于"谁持有该 id 谁贡献非零、其余贡献 0"，从而得到完整 embedding。

这套 vocab-range 区间掩码 + 越界置零 + ReduceScatter 求和聚合，是 Embedding TP 的核心机制。

![HSTU Embedding Tensor Parallel](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/figures/embedding_tp.png)
*来源：[`docs/models/hstu/figures/embedding_tp.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/figures/embedding_tp.png)（cann-recipes-infer @ 944d2d3）*

数据流示意（DP → TP → DP 切换）：

```mermaid
flowchart LR
 DP_in[DP 输入<br/>各卡独立 batch] --> Len[AllReduce MAX<br/>对齐 ID 长度]
 Len --> AllGather[AllGather<br/>all_gather_into_tensor<br/>聚合全局 id]
 AllGather --> TP_lookup[Embedding Table<br/>vocab 区间切分 查表<br/>越界 id 掩码置零]
 TP_lookup --> ReduceScatter[ReduceScatter<br/>reduce_scatter_tensor<br/>求和聚合 + 拆回 DP batch]
 ReduceScatter --> DP_out[DP 输出<br/>送入 dense 部分]
```

> 集合通信算子按钉定 `inference_embedding.py` 定版：聚合用 `dist.all_gather_into_tensor`、拆回用 `dist.reduce_scatter_tensor`（源码无 `all_to_all`）；分片前先 `dist.all_reduce(op=MAX)`（`_get_global_max_length`）求各卡 id 数的全局最大值，对齐 padding 长度后再聚合。

## Applicable Scenarios

- **生成式推荐模型**（如 [hstu](../models/hstu.md)）：Embedding 占模型容量大头，dense 部分相对小
- **大规模稀疏 Embedding**：词表千万~亿级，单卡显存无法装下完整表
- **多卡推理需要支撑更大 dense 参数模型**：切分 Embedding 后，每卡省出的显存可以用于放更大的 HSTU dense 权重

## Configuration

- HSTU `inference_gr_ranking.py` 通过 `--embed_tp_size <N>` 指定切分大小；示例：单机两卡 `torchrun ... --nproc-per-node=2 ... --embed_tp_size 2`
- Embedding TP **与 DP 叠加**使用：Embedding TP 内做查表并行，TP 外用 DP 并行处理 dense 前向
- **阈值门控的混合切分**：`InferenceEmbedding` 持 `small_table_threshold`（默认 `1000`，可配），仅 `should_shard = (embed_tp_size > 1) and (vocab_size >= small_table_threshold)` 成立的大表才走 `VocabParallelEmbedding` 分片；不满足的小表保持 replicated `torch.nn.Embedding`，每卡各持一份完整表

## Constraints

- **Embedding Table 必须按 vocab 切分**：若对 dim 维度切分则需另外集合通信与聚合逻辑，源文档未讨论
- **小表不分片**：`vocab_size < small_table_threshold`（默认 1000）的表 replicated 驻留每卡，不进入 vocab-range 掩码路径
- **每个分片特征的 DP → TP → DP 切换引入三次集合通信**（长度 AllReduce(MAX) + ID AllGather + 向量 ReduceScatter）：通信开销与 embedding lookup 频次成正比
- **与 LLM Attention 头切分约束解耦**：受词表规模与卡数约束，而非 head 整除约束

## 当前 LLM 公共模块的区别

HSTU上述实现保留按长度MAX、ID AllGather、向量ReduceScatter的DP→TP→DP流程；公共module/linear.py的VocabParallelEmbedding是另一实现，分片大小通过divide要求vocab整除TP，不能照用HSTU的ceil分片公式。

公共模块现在直接以本地input_size_per_partition初始化nn.Embedding，并把全局padding_idx仅在归属本rank时转换为local_padding_idx，其余rank传None；权重requires_grad=False并附加weight_loader。该修正避免初始化全表和padding下标越界，不能据此推定Decode时延收益。查表/通信仍由消费该模块的模型组织。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [hstu_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/hstu_optimization.md)（supporting）
- [inference_embedding.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hstu/modules/inference_embedding.py)（implementation）
- [linear.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py)（implementation）

## Links

- [hstu](../models/hstu.md)
- [tensor-parallel](tensor_parallel.md)
- [data-parallel](data_parallel.md)
