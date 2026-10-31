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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/3
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/offload_cache.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      model_features:
        all_of:
        - mla
---

# DSA decode 显存预算：Full MLA KVCache + 新增 Indexer Key Cache（勿漏）+ Indexer 权重

## 适用场景

部署 [dsa](../../concepts/modules/dsa.md) 结构（[mla](../../concepts/modules/mla.md) + [lightning-indexer](../../concepts/kernels/lightning_indexer.md) 稀疏选择）做长序列 decode 显存规划时。相较无 indexer 的 MLA 模型，DSA 的 decode 显存**不只是 Full MLA KVCache**——Lightning Indexer 带来两笔新增显存（一笔 cache、一笔权重），漏算会低估显存需求。

## 注意力相关局部预算（三项都要计入）

在原模型权重、激活、workspace、通信缓冲及运行时预留之外，还须计入以下注意力相关项目：**Full MLA KVCache + Indexer Key Cache + Indexer 新增权重**。这不是整机总显存等式：

- **Full MLA KVCache**：为保障效果，DSA 仍缓存完整 MLA 的 Full KVCache（不因稀疏而少存 KV），是显存占比最高项。
- **Indexer Key Cache（易漏）**：为避免 decode 阶段重复计算 Indexer Key，需新增缓存 Indexer Key Cache，在未量化且无额外padding的粗略估计中，大小 ≈
  `batch_size × kv_length × Indexer_head_dim × storage_bytes × num_layers`。
  文档示例：每 rank 4 batch、64K 序列、BF16 下约 **4GB**——长序列 / 大 batch 下不可忽略。
- **Indexer 新增权重**：Lightning Indexer 是轻量类 MQA 结构，新增 `q_b_proj`、`wk_proj`、`weight_proj` 三个 Linear，综合所有 Layer 权重参数量新增约 **0.85B**。

## 当前源码预算补充

Indexer Key与可选INT8 scale以各层CacheEntry声明，独立于MLA nope/rope；真实预算需含页块取整、null block和scale。CP Prefill存在全局临时计算视图与请求所有者持久视图，不能把每rank4batch的文档示例无条件乘到所有拓扑。启用offload时Full MLA移至Host，设备仍有逐层selection、临时KV及状态/块表workspace，不能只减掉整份Full MLA而漏加这些项目。框架在分配前纳入模型申报的OffloadWorkspaceMemoryInfo。

## 可迁移判断

给 DSA / 带独立稀疏索引器的模型做 decode 显存规划时，除 KVCache 外必须单列「索引器为避免重复计算而新增的 key cache」这一项；它随 batch × 序列 × 层数线性放大，长序列大 batch 下与主 KVCache 同量级。为降 DSA 显存的进一步手段：C8 int8 KV 见 [mla-c8-int8-kv-cache-op-wiring](mla_c8_int8_kv_cache_op_wiring.md)，KVCache offload 见 [kvcache-offload-host-swap](kvcache_offload_host_swap.md)，压 Lightning Indexer 单算子时延（量化算子选型）见 [quant-lightning-indexer-latency](quant_lightning_indexer_latency.md)。

## 参考实现及其约束

参考 cann-recipes-infer 的 [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md)（`indexer.py` Lightning Indexer + Indexer Key Cache）。~4GB / ~0.85B 为文档给的单点示例值（4 batch / 64K / BF16），非全量配置扫掠、非独立复测；内存公式用于显存规划、数字不外推。

## 相关经验
- [DSA IndexCache 跨层 top-k 复用观测（草稿）](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)

## Evidence

- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（primary）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/3)（evidence）
- [offload_cache.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/offload_cache.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
