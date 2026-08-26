---
type: Optimization
title: DSA decode 显存预算：Full MLA KVCache + 新增 Indexer Key Cache（勿漏）+ Indexer 权重
description: DSA decode 显存预算：Full MLA KVCache + 新增 Indexer Key Cache（勿漏）+ Indexer 权重。部署 dsa 结构（mla + lightning-indexer 稀疏选择）做长序列 decode 显存规划时。相较无 indexer 的 MLA 模型，DSA 的 decode 显存不只是 Full MLA KVCache——Lightning Indexer 带来两笔新增显存（一笔 cache、一笔权重），漏算会低估显存需求。
tags:
- task.optimization
- topic.attention
- topic.memory
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# DSA decode 显存预算：Full MLA KVCache + 新增 Indexer Key Cache（勿漏）+ Indexer 权重

## 适用场景

部署 [dsa](../../../concepts/modules/dsa.md) 结构（[mla](../../../concepts/modules/mla.md) + [lightning-indexer](../../../concepts/kernels/lightning_indexer.md) 稀疏选择）做长序列 decode 显存规划时。相较无 indexer 的 MLA 模型，DSA 的 decode 显存**不只是 Full MLA KVCache**——Lightning Indexer 带来两笔新增显存（一笔 cache、一笔权重），漏算会低估显存需求。

## 显存构成（三项都要预算）

DSA decode 显存 = **Full MLA KVCache + Indexer Key Cache + Indexer 新增权重**：

- **Full MLA KVCache**：为保障效果，DSA 仍缓存完整 MLA 的 Full KVCache（不因稀疏而少存 KV），是显存占比最高项。
- **Indexer Key Cache（易漏）**：为避免 decode 阶段重复计算 Indexer Key，需新增缓存 Indexer Key Cache，大小 ≈
  `batch_size × kv_length × Indexer_head_dim × storage_bytes × num_layers`。
  文档示例：每 rank 4 batch、64K 序列、BF16 下约 **4GB**——长序列 / 大 batch 下不可忽略。
- **Indexer 新增权重**：Lightning Indexer 是轻量类 MQA 结构，新增 `q_b_proj`、`wk_proj`、`weight_proj` 三个 Linear，综合所有 Layer 权重参数量新增约 **0.85B**。

## 可迁移判断

给 DSA / 带独立稀疏索引器的模型做 decode 显存规划时，除 KVCache 外必须单列「索引器为避免重复计算而新增的 key cache」这一项；它随 batch × 序列 × 层数线性放大，长序列大 batch 下与主 KVCache 同量级。为降 DSA 显存的进一步手段：C8 int8 KV 见 [mla-c8-int8-kv-cache-op-wiring](../rules/mla_c8_int8_kv_cache_op_wiring.md)，KVCache offload 见 [kvcache-offload-host-swap](../../../guides/experience/interventions/kvcache_offload_host_swap.md)，压 Lightning Indexer 单算子时延（量化算子选型）见 [quant-lightning-indexer-latency](../rules/quant_lightning_indexer_latency.md)。

## 参考实现及其约束

参考 cann-recipes-infer 的 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)（`indexer.py` Lightning Indexer + Indexer Key Cache）。~4GB / ~0.85B 为文档给的单点示例值（4 batch / 64K / BF16），非全量配置扫掠、非独立复测；内存公式用于显存规划、数字不外推。

## 相关经验
- [DSA/SFA 长序列服务化：跨步复用 top-k 索引（IndexCache）摊薄 ind](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)

## Evidence

- `doc 披露`（@fa6892b）：`deepseek_v3.2_exp_inference_guide.md`「DeepSeek-V3.2-Exp vs V3.1」的权重内存 / KVCache 内存分析给出 Indexer Key Cache 公式、~4GB / ~0.85B 示例；`indexer.py` 存在 Lightning Indexer 实现。「仍缓存 Full MLA KVCache + 新增 Indexer Key Cache」为首方 doc 披露。
- 溯源下探：[cann-recipes-infer-pr-3-feat-add-deepseek-v3-2-exp-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)
