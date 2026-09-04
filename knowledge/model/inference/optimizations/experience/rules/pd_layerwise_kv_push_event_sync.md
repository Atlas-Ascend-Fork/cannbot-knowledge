---
type: Optimization
title: PD 分离 layerwise KV push：整条 model stream 同步换成逐层 torch.npu.Event 同步
description: 在 PD（Prefill-Decode）分离在线推理的 layerwise KV push 场景，P（KV producer）侧 prefill 边算边把每层 KV 逐层推送到 D 侧时，把 KV 发送线程原先每次换层做的整条 model stream 同步 self.model_stream.synchronize() 替换为逐层的 torch.npu.Event 点到点同步 reshape_cache_event.synchronize()。event 在 P 侧每层 reshape_and_cache（MHA）及 exec_kv_prefill（MLA 路径）之后 record()，随 (req_id, req_meta, layer_index, key, value) 一起入 send_queue，使某层 KV 写入一完成即可开传该层，无需等整条计算流排空。原理：stream 同步等整条 NPU 流排空、粒度过粗会连带等无关计算；torch.npu.Event 同步点到点、粒度精确到本层 KV 写完，缩小同步粒度放开 layerwise 传输与 prefill 计算的重叠面，缓解 prefill_slow。参考实现在 vllm-ascend mooncake_layerwise_connector（KVCacheSendingLayerThread._transfer_kv_cache）与 mla_v1.py，仅 is_kv_producer 侧 record，无独立量化 benchmark（收益定性）。注意该 event 同步路径在特定 CANN 版本前有 event.synchronize() hang 隐患，与本粒度优化互补。涉及 hixl / mooncake KV 传输与 kv-cache-manager。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/4842
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- agnostic
---

# PD 分离 layerwise KV push：整条 model stream 同步换成逐层 torch.npu.Event 同步

## 适用场景

- 部署形态：PD（Prefill-Decode）分离在线推理，P（KV producer）侧 prefill 边算边把 KV 逐层（layerwise）push 到 D 侧，而不是等整模型 prefill 完成后一次性传全量 KV。参见 [online-pd-inference](../../../concepts/frameworks/online_pd_inference.md)。
- 触发信号：layerwise KV 传输与 prefill 计算的**重叠度不足**，push 吞吐上不去、prefill 侧显得慢（`prefill_slow`）。发送线程在传某一层 KV 之前要先确认该层 KV 已写入 KV cache，若这个「等待写入完成」的同步做得过粗，就会连带阻塞传输、吃掉重叠收益。
- 判断落点：如果发送线程换层时用的是**整条计算流的同步**（等 model stream 排空），那它等的不只是「本层 KV 写完」，而是整条流上排在后面的、与本层 KV 无关的计算也一并等到——这正是本规则要修的粒度过粗问题。
- 前提：目标是 NPU（Ascend）侧、以 `torch.npu.Event` / NPU stream 表达同步的实现；KV 落 cache 的写入点是可插桩的（MHA 的 `reshape_and_cache`、MLA 的 `exec_kv_prefill`）。

## 规则：把粗流同步换成逐层点到点事件同步

**条件 → 优先尝试**：当 layerwise KV push 的发送线程用 `model_stream.synchronize()`（整条计算流同步）来等某层 KV 写入完成时，优先改为**逐层 `torch.npu.Event` 同步**——为每一层 KV 写入单独创建并 record 一个 event，发送线程只 `synchronize()` 该层对应的 event。

为何有效：

- **stream 同步是等整条流排空**——粒度是「这条流上所有已下发的 kernel 都做完」，会把与本层 KV 完全无关的后续计算也纳入等待，把传输卡在无关计算后面。
- **event 同步是点到点**——`torch.npu.Event.record()` 在某个具体位置打点，`synchronize()` 只等这一个已 record 的事件到达，粒度精确到「本层 KV 写完」。层 L 的 KV 一写完就能立即开传，不必等层 L+1、L+2 的计算。
- 缩小同步粒度直接放开了 layerwise 传输与 prefill 计算的重叠面：多层的「写→传」可以流水叠起来，而不是被一次次整流同步串行化。这与 [multi-stream](../../../concepts/techniques/multi_stream.md) 的思路一致——用更细的依赖表达换取更多重叠。

**依据**：该技法在 vllm-ascend layerwise connector 的合并态 diff 中落地（见「参考实现」），是「提升 Layerwise Connector 性能」的三项改动之一。

**反例 / 边界**：这条规则讲的是**同步粒度**优化，不外推为「所有 KV 传输都应换成事件同步」。同时，逐层 event 同步这条路径在特定 CANN 版本前存在 `event.synchronize()` hang 的隐患（属另一条独立经验），需与本规则配套核对——粒度优化正确不代表该同步路径在任意 CANN 版本上都安全。

## 参考实现及其约束

参考实现：vllm-ascend layerwise connector 的 KV 逐层推送发送线程（`KVCacheSendingLayerThread._transfer_kv_cache`），合并态代码见 `vllm_ascend/distributed/mooncake_layerwise_connector.py` 与 `vllm_ascend/attention/mla_v1.py`。

改动骨架（三步）：

1. **P 侧每层 KV 写入处创建并 record 事件**（仅 `is_kv_producer` 分支）：
   - MHA 路径：`attn_metadata.reshape_cache_event = torch.npu.Event()`，在 `reshape_and_cache(...)` 完成后 `attn_metadata.reshape_cache_event.record()`。
   - MLA 路径：同样在 `exec_kv_prefill` 前后 `torch.npu.Event()` + `record()`。参见 [mla-prolog](../../../concepts/kernels/mla_prolog.md) 相关的 MLA KV 写入路径。
2. **event 随该层 KV 一起入发送队列**：`send_queue` 元组类型追加一个 `torch.npu.Event` 项，与 `(req_id, req_meta, layer_index, key, value)` 一起排队，把「这层的写入完成信号」传递给发送线程。
3. **发送线程换层时改用事件同步**：把 `self.model_stream.synchronize()` 替换为 `reshape_cache_event.synchronize()`，只等本层 KV 写入事件。

约束（是该参考实现的限制，不是技法本身的限制）：

- 仅在 P（`is_kv_producer`）侧 record 事件；D 侧不涉及。KV cache 的块管理承接方见 [kv-cache-manager](../../../concepts/frameworks/kv_cache_manager.md)。
- 该参考实现未给出独立量化 benchmark（仅过 CI），收益为**定性**：更细同步粒度 → 更好的 push/prefill 计算重叠。落地前应在目标 workload 上自测重叠度与端到端收益，不要当作已量化的确定加速。
- 事件的创建/入队/同步分散在算子路径与发送线程两处，需保证 `layer_index` 与其 event 的对应关系不错位，否则会等错层的写入。

## Evidence

- 合并态 diff（merge sha `46a16143876fd303e1e7e172467ee10caf973741`，MERGED 2025-12-31）确认 `model_stream.synchronize()` → `reshape_cache_event.synchronize()`、`torch.npu.Event()` 在 `is_kv_producer` 分支 `record()`。
- 涉及文件：`vllm_ascend/distributed/mooncake_layerwise_connector.py`、`vllm_ascend/attention/mla_v1.py`（`reshape_cache_event` record on `is_kv_producer`）。
- 设计出处：RFC「Use event synchronize to replace stream synchronize」（CDCP scheduling for disaggregated prefilling with KV cache layerwise 的 Proposed Change 2①）。
- 溯源 claim：[layerwise-kv-push-用逐层-torch-npu-event-record-于-reshape-and-c](https://github.com/vllm-project/vllm-ascend/issues/4842)
