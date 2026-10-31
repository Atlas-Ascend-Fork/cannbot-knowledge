---
type: Optimization
title: DeepSeek/Kimi A3 Prefill CP：统一元数据与请求所有者
description: 按当前统一Executor解释每请求ZigZag、CP整域约束、计算/持久缓存双视图和请求所有者。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: implementation
created_at: '2026-10-20T12:16:14Z'
updated_at: '2026-10-29T14:49:38Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      objective:
      - latency
      - ttft
      - memory
      context_length:
      - long_context
      - ultra_long_context
      model_features:
        all_of:
        - moe
        - mla
      framework:
      - cann_executor
---

# DeepSeek/Kimi A3 Prefill CP：统一元数据与请求所有者

当前两模型均使用统一Executor。启用CP时InferenceConfig和Engine要求cp_size=world_size、attn_tp_size=1；这一限制属于当前实现，不是CP原理限制。Decode不切头尾query，在线D侧还强制CP=1。

Engine._apply_prefill_cp按每条请求分别补齐至2×CP段，rank取得第r段与第2CP-r-1段。local_indices选择本地token，restore_indices把AllGather后的rank顺序还原为各请求原序；position_ids按每请求重新起算。模型可用cp_segment_min_len声明最小段长，不能仅靠全batch统一平均长度构造。

PrefillCPMetaData同时携带两类PA空间：global_block_table/global_slot_mapping是当前层完整KV的计算视图；persistent_valid_indices/persistent_slot_mapping是后续Decode或传输需要的持久视图。Offline只保留本rank请求所有者的真实token，PREFILL角色保留全局有效token，且只由CP rank0消费全局输出请求。不能把“计算时拿到完整KV”推成“每rank永久缓存所有请求”。

V3.2-Exp的Indexer Key、INT8 scale及MLA latent都遵循这两类视图；Kimi稠密MLA不需Indexer，但仍需正确的token顺序、持久槽和输出恢复。CP与EP覆盖相同rank集合也不证明CommManager不建两个组。

迁移先对齐非CP确定性输出，再检查不等长、多请求、小于CP段数、无本地所有者请求及分片Prefill。记录显存、通信、TTFT与波动；来源没有隔离CP开关的统一实测收益。本次没有执行模型。

选择入口见[长序列CP](../rules/long_seq_prefill_context_parallel.md)，写缓存见[MLA CP双视图](../rules/mla_prolog_zigzag_cp_kv_write.md)。


## Evidence

- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（implementation）
