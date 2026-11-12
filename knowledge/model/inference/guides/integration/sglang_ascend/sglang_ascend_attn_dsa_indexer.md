---
type: Guide
title: SGLang Ascend DSA索引器：缓存写入、量化与CP/DCP元数据
description: 闭合NPU DSA索引器Q/K准备、独立投影流、全局缓存地址、Hadamard量化和Lightning Indexer的TopK输出契约。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/dsa/dsa_npu_indexer.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/dsa/dsa_indexer.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/deepseek_v2_attention_mla_npu.py
  role: implementation
created_at: '2026-11-08T12:07:55Z'
updated_at: '2026-11-09T04:31:21Z'
platforms: []
aliases:
- DSANPUIndexerMixin
- npu_lightning_indexer
---

# SGLang Ascend DSA索引器：缓存写入、量化与CP/DCP元数据

## 准备与依赖

`Indexer`通过DSANPUIndexerMixin选择NPU实现。indexer是DSA CP元数据的首个消费者，因此必须先调用prepare_dsa_cp_metadata，再投影Q/K、K norm和RoPE；CP下query为本地行，K恢复全序列后写池。NeoX sin/cos可按ForwardBatch缓存，避免层层重复gather。

Q投影仅在 NeoX RoPE 且 alt_stream 非空时在侧流执行；非NeoX分支的Q投影直接在当前流执行。weights_proj 则由 SGLANG_NPU_USE_MULTI_STREAM 控制是否进入独立权重流，record_stream保护结果生命周期，主流等待事件后才发Lightning Indexer。weights投影由FP32 x参与计算再交BF16 kernel权重；不能把“权重流独立”解释为不需要同步。

## 缓存和量化

DCP target写index K仍使用allocator-global `dcp_origin_out_cache_loc`，并assert写地址数量与positions一致；attention本地KV位置不能直接作为indexer写地址。是否量化indexer由index_k_scale_buffer是否存在决定。启用量化池时，head128 的 BF16 K 先做归一化 Hadamard，再动态量化到池 dtype（INT8或FP8），scale 保留 FP32；写 K scale 后写 K。只有非 CP 索引分支还对 Q 做相同量化，并调用带 query/key 反量化 scale 的 npu_quant_lightning_indexer。prefill CP 且有 attn_cp_metadata 时优先走 do_npu_cp_balance_indexer，使用普通 npu_lightning_indexer，未量化 Q、未传反量化 scale；不能将非 CP 的量化组合保证外推到 CP。

普通Lightning Indexer使用TND query与PA_BSND key、sparse_mode3、sparse_count=index_topk，query/KV长度显式转device int32。CP平衡路线是一组本地Q对全KV的单次调用，不再按旧prev/next方案拆TopK。

## 输出与接入边界

TopK统一为[T,K] int32，attention侧再扩展维度。需要恢复attention-TP全token时按batch输入token数分配目标buffer并all-gather，不能按局部query数量误配容量。跳过返回TopK不等于跳过K缓存更新。

建议按BF16与量化indexer、空请求、共享TopK、CP和DCP分别对照cache位置、scale尺寸及最终TopK，检查跨rank新TopK只本地化一次。代价包括Hadamard、量化和多流事件，收益需真实测量。本次仅核对源码，未运行模型或算子测试；不据NPU分支推导具体芯片支持。
