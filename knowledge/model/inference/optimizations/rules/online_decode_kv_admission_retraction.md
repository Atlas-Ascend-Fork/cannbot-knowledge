---
type: Optimization
title: 在线 Decode 的缓存准入与压力驱逐
description: 以当前每类缓存的reserved_tokens预算、首Decode预分配和finished_requests驱逐通知更新旧队列公式。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode_queues.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/kv_cache_manager.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/single_type_kv_cache_manager.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:44:44Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      serving_mode:
      - online
      framework:
      - cann_executor
---

# 在线 Decode 的缓存准入与压力驱逐

## 准入在每类缓存管理器执行

当前 DecodePreallocQueue 不再自行计算全局 `admittable_blocks`。它调用 `KVCacheManager.allocate_slots(..., reserved_tokens=num_reserved_decode_tokens)`，后者逐类检查再分配。Full 类管理器按自己的 block_size 计算：

```text
required = ceil(num_tokens/block_size)
need = max(0, required - 已持有块数)
reserved = ceil(reserved_tokens/block_size) × len(req_to_blocks)
允许分配 = need <= free_blocks - reserved
```

`reserved_tokens` 在此调用中是准入预算，不等于预先为所有请求实际占住这些块。Sliding/压缩/状态缓存有各自管理器，不能套用全模型单一块大小。默认 num_reserved_decode_tokens=64，吞吐与后续增长余量须按负载测量。

普通首Decode预分配 `computed=prompt长度, new=1+next_n, lookahead=max(next_n-1,0)`；需要保留Prefill缓存的draft后端则为 `computed=0, new=prompt长度, lookahead=next_n`。metadata槽不足或缓存失败留待后续，继续考察后续请求。超长prompt已经在统一准入层拒绝，不在传输队列重复校验。

## 空批时驱逐并释放

Decode调度返回空批但running非空时，按 `(len(output_id_list), -prompt_tokens)` 选受害者，释放KV和metadata再重试。一般标记preempted_oom，最后一个仍无法装入标记abort_oom；写入finished_requests由分派器回给客户端，不再依赖StepOutput返回被驱逐ID。TP一致性依赖相同池、相同请求顺序和确定性选择；传输队列推进仍需Gloo共识，不能省掉集合通信。

Decode CP固定为1。Decode的allocate_slots失败会continue；Prefill虽然严格FIFO，缓存分配失败后仍continue并重试未移除的队首，因此不能据此声称Prefill队首阻塞已解决；offline CP该失败则显式RuntimeError。

## 验收

覆盖长请求拒绝、缓存/metadata耗尽、传输失败、最后单请求OOM与混合长度突发；检查客户端终态及释放后的KV水位。源码没有隔离该策略的吞吐数字，不宣称性能保证。入口见[在线PD](../../concepts/frameworks/online_pd_inference.md)。


## Evidence

- [decode_queues.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode_queues.py)（primary）
- [decode.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode.py)（implementation）
- [kv_cache_manager.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/kv_cache_manager.py)（implementation）
- [single_type_kv_cache_manager.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/kv_cache/single_type_kv_cache_manager.py)（implementation）
- [scheduler.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py)（implementation）
