---
type: Optimization
title: V3.2-Exp Offload 的 Prefill 搬运流与事件
description: 按当前统一缓存和OffloadWorkspace接口说明Prefill事件配对，区分CP持久槽与非CP整层异步复制。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/offload_cache.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: implementation
created_at: '2026-10-22T01:39:38Z'
updated_at: '2026-10-29T14:47:07Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
---

# V3.2-Exp Offload 的 Prefill 搬运流与事件

## 当前调用链

A3 V3.2-Exp 由 `model_config.custom_params.enable_offload` 启用；模型明确只支持offline。Full KV CacheEntry 使用SWAPPED_MEMORY分配器，独立OffloadCache负责设备临时及逐层selection workspace；不再由旧OffloadCache.init_cache直接分配所有Host层。

Prefill prolog先写设备临时KV，主流record d2h_event；d2h_stream等待该事件后搬运并重新record；本层decoder完成MLP后主流wait，约束下一层复用临时缓冲。非CP路径整层copy_(non_blocking=True)，CP路径只按persistent_slot_mapping选择并写回应持久化的槽；不能把两条分支统一写成整层连续copy。

INT8把nope/rope/scale等编码在实际拼接布局中，无独立rope副本；非量化分支分别搬nope与rope。单事件反复记录的顺序须与当前流上下文一起检查，不只看变量名判断完成关系。

Decode先更新Host KV，再按LI TopK调用torch_npu.npu_gather_selection_kv_cache填设备selection缓存，SFA消费对应selection block table。D2H事件只描述Prefill搬运边界，不能替代Decode gather、状态命中和workspace复用的全部依赖。

## 容量与验收

OffloadWorkspaceSpec在分配前申报temp、逐层selected、selection表/状态及default topk索引的设备字节；框架据此预留，真实Host Full KV仍按各CacheEntry及层数另算。batchseq=batch_size_per_dp_rank×(next_n+1)，临时PA块多保留null block0。

有独立流与non_blocking调用只说明可异步编排，是否掩盖带宽需看时间线。覆盖CP/非CP、INT8/非量化、首轮和跨请求状态重置；当前Prefill会reinit_status。输出或时序不对齐时关闭offload回到基线，本次没有硬件复测。

机制见[KV Offload](../../concepts/techniques/kvcache_offload.md)，算子见[GatherSelection](../../concepts/kernels/gather_selection_kv_cache.md)。


## Evidence

- [offload_cache.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/offload_cache.py)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（implementation）
