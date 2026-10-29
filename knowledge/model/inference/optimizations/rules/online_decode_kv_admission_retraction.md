---
type: Optimization
title: online decode 调度防 KV 打满死锁：入场预留 + cheapest-victim retraction + break→continue
description: online-pd-inference 的 decode 实例、连续调度、共享 kv-cache-manager KV 池、高 QPS 突发负载。若无入场控制，高 QPS 突发会贪婪填满 KV cache，随后没有一个 running 请求能再长出下一个 token → 死锁；另有两种退化：running 非空但当前 step 预算装不下任何请求时永远 fall through 到 dummy batch（KV 一直满、无请求推进）；队首单个不可装的大请求阻断其后本可入场的小请求（head-of-line blocking）。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/315
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/c695829cd2c075fdd49894c9918a98ece476c78a/executor/online/scheduler/decode.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/c695829cd2c075fdd49894c9918a98ece476c78a/executor/online/scheduler/queues.py
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:41:21Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase: [decode]
      serving_mode: [online]
      framework: [cann_executor]
---

# online decode 调度防 KV 打满死锁：入场预留 + cheapest-victim retraction + break→continue

## 适用场景

[online-pd-inference](../../concepts/frameworks/online_pd_inference.md) 的 decode 实例、连续调度、共享 [kv-cache-manager](../../concepts/frameworks/kv_cache_manager.md) KV 池、高 QPS 突发负载。若无入场控制，高 QPS 突发会贪婪填满 KV cache，随后**没有一个 running 请求能再长出下一个 token → 死锁**；另有两种退化：running 非空但当前 step 预算装不下任何请求时永远 fall through 到 dummy batch（KV 一直满、无请求推进）；队首单个不可装的大请求阻断其后本可入场的小请求（head-of-line blocking）。

## 三段机制

**（1）入场控制 + KV 预留**：为每个在途请求（running + transfer 队列）预留 `⌈num_reserved_decode_tokens / block_size⌉` 块未来 decode 增长空间；只有新请求 input + 预留能装进剩余预算才允入场：
```python
reserved_blocks_per_req = (num_reserved_decode_tokens + block_size - 1) // block_size
in_flight = len(running_requests) + len(transfer_queue.waiting)
admittable_blocks = free_blocks - reserved_blocks_per_req * in_flight
```
权衡：`num_reserved_decode_tokens`（默认 64，可 YAML 覆盖）越小并发吞吐越高但突发下 retraction 越频繁；越大反之。

**（2）尾部 OOM 时 cheapest-victim retraction**：当 decode 调度返回空 batch 但 running 非空，循环驱逐直到能装或空。受害者选「输出进度最少 + 输入最大」（释放最多 KV、浪费最少已做工）：
```python
victim = min(running_requests.values(),
             key=lambda r: (len(r.output_id_list), -r.prompt_tokens))
```
最后一个也装不下时也 abort 保证循环终止；被驱逐 id 汇入下一步 `finished_requests` 回给 client（不静默泄漏）。

**（3）head-of-line：`break`→`continue`**：base 调度里 `allocate_slots` 失败的处理由 `break` 改为 `continue`，队首不可装请求不再阻断其后小请求；prefill 侧并把 prompt 长度检查移到 `allocate_slots` 之前，避免为随即丢弃的请求分配 KV 块（否则泄漏刚分配的块）。

## correctness / 边界

固定 DecodeDisaggScheduler 初始化要求 `attn_cp_size == 1`，否则抛 ValueError；这组在线 Decode 调度规则不能用于 CP>1 的实例拓扑。

- Scope 覆盖上述 CANN Executor 在线 Decode 调度规则。固定实现的 `DecodeDisaggScheduler.mode='online'`，`run_step` 向基类传入 `phase='decode'`；离线调度或其他框架不能直接套用这组队列和参数。高 QPS 突发是来源给出的风险场景，不能据此确定 batch 或并发的定性分档，二者仍未标注。
- correctness：TP 各 rank 对同尺寸 KV 池跑同样的 `allocate_slots`，空 batch 检测与受害者选择（按 request_id 有序 + 稳定 sort key）在各 rank 一致，无需额外集合通信。
- 边界：decode 实例侧机制；`num_reserved_decode_tokens` 需按 QPS / 突发特性调（默认 64）。本 PR 未披露性能 benchmark 数字，故不作性能断言。对齐 sglang 的 `retract_decode`。

## 参考实现及其约束

参考 cann-recipes-infer 的 online decode 调度器（`executor/online/scheduler/{queues.py,decode.py}` + base `executor/core/scheduler/scheduler.py` + `SchedulerConfig.num_reserved_decode_tokens`）。相关：分页 KV 的算子契约见 [ascend-paged-attention-kv-cache](ascend_paged_attention_kv_cache.md)。

## Evidence

- `diff 事实`（@c695829cd2c0）：`pop_preallocated` 的预留计算、`_retract_one` 的受害者 key、`_schedule_decode_batch` 的 retraction 循环、`SchedulerConfig.num_reserved_decode_tokens=64` 及 docstring、base scheduler 的 `break→continue` 与 prompt-length-check-before-allocate 均为读到的实际 diff；死锁根因与权衡表述来自代码内注释 / docstring。
- 溯源下探：[cann-recipes-infer-pr-315-refactor-online-batch](https://gitcode.com/cann/cann-recipes-infer/merge_requests/315)
