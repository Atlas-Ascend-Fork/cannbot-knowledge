---
type: Optimization
title: Attention-DP + MoE-EP 部署：对访存 / 内存重的投影层（O_proj / LM_Head / Embedding / dense）单独局部 TP
description: MoE 模型（DeepSeek / Kimi 族）注意力走 data-parallel、MoE 走 expert-parallel 的部署里（attn_tp_size==1、moe_tp_size==1），纯 Attention-DP 下每卡各存一份 O_proj / LM_Head / Embedding——这几处大权重成访存瓶颈、Embedding 内存占用大；卡数压到单节点后 W8A8C8 权重 + KV / 激活在 prefill 全量 all_gather 峰值处还会 OOM（EL0004）。这时别把整模型都 TP，只对这些访存 / 内存重的特定投影层单独开局部 TP。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/93
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/54
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/472
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Attention-DP + MoE-EP 部署：对访存 / 内存重的投影层（O_proj / LM_Head / Embedding / dense）单独局部 TP

## 适用场景

MoE 模型（DeepSeek / Kimi 族）注意力走 [data-parallel](../../../concepts/parallelism/data_parallel.md)、MoE 走 [expert-parallel](../../../concepts/parallelism/expert_parallel.md) 的部署里（`attn_tp_size==1`、`moe_tp_size==1`），纯 Attention-DP 下每卡各存一份 O_proj / LM_Head / Embedding——这几处大权重成访存瓶颈、Embedding 内存占用大；卡数压到单节点后 W8A8C8 权重 + KV / 激活在 prefill 全量 all_gather 峰值处还会 OOM（`EL0004`）。这时别把整模型都 TP，只对这些访存 / 内存重的**特定投影层**单独开局部 TP。

## 规则 · 选择性局部 TP

对访存 / 内存重的投影层单独开局部 [tensor-parallel](../../../concepts/parallelism/tensor_parallel.md)，把权重沿相应维切到多 rank 摊薄单 rank 显存 / 访存：

- **O_proj 局部 TP（`oproj_tp_size`）**：注意力输出沿头维切 TP（`view` → all2all → O_proj matmul → reduce_scatter）。**硬门槛：前置 `attn_tp_size == 1`**——`attn_tp_size > 1` 时不支持（二者互斥）。
- **Embedding TP（`embed_tp_size`）**：`vocab_size_per_rank = vocab_size // embed_tp_size`，按 rank 偏移查本 rank 词表分片后 allgather。
- **LM_Head TP（`lmhead_tp_size`，默认继承 `embed_tp_size`）**：沿词表维切 TP。
- **dense TP（`dense_tp_size`）**：dense / 共享层沿 TP 切分。
- **TP 域限单机 HCCS 高速互联域**：局部 TP 的通信域约束在节点内 HCCS 高速互联域内，避免跨节点 TP 的通信代价拖累 Decode（跨机 TP 通信代价高）；BF16 下 Decode 推荐多节点部署。跨卡 MoE 分发路径的选型见 [moe-ep-dispatch-path-by-stage](moe_ep_dispatch_path_by_stage.md)。

单节点 W8A8C8 显存吃紧时的可复用调参（维护者口径、不在 README）：`batch_size` 调小（可到 1）；`oproj_tp_size` 与 `dense_tp_size` 增大（如 16 rank 下取 16，把 output-proj / dense 权重全分片到所有 rank）。约束：`oproj_tp_size` / `dense_tp_size` 须整除 world_size，且 `attn_tp_size>1` 与 `oproj_tp_size>1` 互斥。

## 参考实现坑 · VocabParallelEmbedding 分片直分配、别全量临时 + 覆盖

子类化 `nn.Embedding` 实现 [embedding-tp](../../../concepts/parallelism/embedding_tp.md) 时，应在 `nn.Embedding.__init__` **直接按每卡分片大小 `input_size_per_partition` 分配** weight，而**不是**先按全量 `vocab_size` 构造、再另建 sharded `Parameter` 覆盖 `self.weight`——后者会在**每一张 TP 卡** init 期临时分配一整份 `(vocab_size, hidden)` 权重随即丢弃，大词表下抬高加载峰值显存、拖慢加载。修法是把分片大小传给 `super().__init__(input_size_per_partition, hidden, ...)`、删掉全量分配 + 覆盖的旧路径。

## 收益 / 边界

- 收益：访存瓶颈与 Embedding 内存被机内局部 TP 摊薄；加载峰值显存降低。源未给 before/after 时延 / 内存数字（部分为「缓解方向」，未端到端复测）。
- 边界：规则限定到 Attention-DP + MoE-EP 的 DeepSeek / Kimi 族 MoE 部署；示例取值（如 `oproj_tp_size=8`、`embed_tp_size=16`）随模型 / 卡数而定，规则本身（选访存重的投影层局部 TP、机内约束、oproj 需 `attn_tp==1`）可迁移。
- 参考 [kimi-k2-thinking](../../../concepts/models/kimi_k2_thinking.md)（A3 decode 推荐配置）、[deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)（单节点 W8A8C8 调参）。

## Evidence

- `diff 事实`（@da13d66）：`oproj_tp_size`（all2all + reduce_scatter，`attn_tp_size==1` 前提）、`embed_tp_size`（`vocab_size_per_rank` 分片 + rank 偏移）、`lmhead_tp_size`（默认取 `embed_tp_size`）三处 TP 实现与门控。「O_proj/LM_Head 为 decode 访存瓶颈、Embedding 内存大」为 `doc 披露`。
- `维护者确认` + `diff 事实`（@2c45117）：单机 W8A8C8 内存紧张 → batch_size 调小、oproj_tp/dense_tp>8；`check_parallel_settings` 的整除约束与「attn_tp>1 与 oproj_tp>1 互斥」为 diff 事实。「TP=1 不分片故更占显存」为推断。
- `diff 事实`（@6cb49951）：`VocabParallelEmbedding.__init__` 首参由 `vocab_size` 改为 `input_size_per_partition`、`create_weights` 整体删除。
- 溯源下探：
  - [cann-recipes-infer-pr-93-feat-support-kimi-k2-thinking](https://gitcode.com/cann/cann-recipes-infer/merge_requests/93)
  - [cann-recipes-infer-issue-54-bug-report-deepseek-v3-2-exp-w8a8c8-8p-16](https://gitcode.com/cann/cann-recipes-infer/issues/54)
  - [cann-recipes-infer-pr-472-fix-shard-vocabparallelembedding-weight-at-init](https://gitcode.com/cann/cann-recipes-infer/merge_requests/472)
  - [cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)