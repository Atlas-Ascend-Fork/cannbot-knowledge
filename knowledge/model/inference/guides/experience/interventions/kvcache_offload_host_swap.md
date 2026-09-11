---
type: Guide
title: KV cache 卸载到 Host 内存：设备单层 temp + 专用流 D2H 重叠 + 逐层异步搬算掩盖
description: KV cache 卸载到 Host 内存：设备单层 temp + 专用流 D2H 重叠 + 逐层异步搬算掩盖。适用：KV cache 占设备内存最高、即使量化后长序列 / 大 batch 仍受限于设备内存、batch size 上不去（memory_bound）；结构如 mla Full KVCache 或分层管理的 KV（hstu 生成式推荐）。参考在 Atlas A3、w8a8c8 之上。 不适用：设备内存充裕的小规格（offload 只带来 H2D 新增开销、无收益）。offload 是设备内存 ↔ Host 内存的权衡，不是纯收益——Host 内存成为新前提。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/134
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/282
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/139
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# KV cache 卸载到 Host 内存：设备单层 temp + 专用流 D2H 重叠 + 逐层异步搬算掩盖

## 适用场景 / 何时不适用

**适用**：KV cache 占设备内存最高、即使量化后长序列 / 大 batch 仍受限于设备内存、batch size 上不去（memory_bound）；结构如 [mla](../../../concepts/modules/mla.md) Full KVCache 或分层管理的 KV（[hstu](../../../concepts/models/hstu.md) 生成式推荐）。参考在 Atlas A3、[w8a8c8](../../../concepts/quantization/w8a8c8.md) 之上。

**不适用**：设备内存充裕的小规格（offload 只带来 H2D 新增开销、无收益）。offload 是设备内存 ↔ Host 内存的权衡，不是纯收益——Host 内存成为新前提。

## 手段 · 三段式（Host 全量 + 设备单层 + 专用流重叠）

- **Host 全量、设备单层**：每层 KV cache 用 host-swapped 内存常驻 Host；设备上只申请**单层** temp 缓冲，计算读写都落在这块单层缓冲上——把「设备驻留 N 层」压成「设备 1 层 + Host N 层」（例：61 层模型每卡 Host 存 61 层、设备只 1 层）。C8 布局时 nope/rope/scale 拼成 int8 供融合算子，见 [mla-c8-int8-kv-cache-op-wiring](../../../optimizations/experience/rules/mla_c8_int8_kv_cache_op_wiring.md)。
- **prefill D2H 与计算重叠（专用流 + event）**：当前层算完后，在**专用 D2H 流**上把 temp 缓冲 scatter / copy 写回 Host 全量 cache；下一层复用同一 temp 缓冲**前**，用 D2H event（blocking wait）等本层卸载完成。用「专用流 + event 依赖」把卸载与计算重叠、又保证共享的单层缓冲不被提前覆盖——这是单层缓冲能安全服务全部层的关键约定（见 [multi-stream](../../../concepts/techniques/multi_stream.md)）。
- **decode 从 Host 取选中块**：decode 依 indexer topk 从 Host 全量 KV 选出参与计算的块到设备喂 [sparse-flash-attention](../../../concepts/kernels/sparse_flash_attention.md)，并跨 step 复用设备常驻选中块摊薄 H2D——该跨-step 复用的细则见 [kvcache-offload-sparse-selection-cross-step-reuse](../../../optimizations/experience/rules/kvcache_offload_sparse_selection_cross_step_reuse.md)。

## 逐层异步 offload 的通用骨架（可迁移到任何有 host KV offload 的 memory-bound 模型）

把「等 dense 全部算完再逐层串行 offload」改为「每层 Attention 结束即在独立 offload stream 上异步触发该层 KV offload」，用 NPU Event 定义计算链与通信链依赖，把 offload 通信隐藏进后续计算：

- **plan 事件**：offload 计划就绪后 record 一次，作为所有层 offload 的公共起点。
- **per-layer attn-done 事件**：主 stream 每层 Attention 算完即 record；offload stream 上该层搬运先 `wait` 本层 attn-done 再启动——保证只搬已算好的层、不早读。
- **per-layer offload-done 事件**：该层搬完后 record，供消费方按层等待。
- **end 事件**：最后一层 offload 完成时 record；统一 `offload_wait()` 只需等这一个。

> 图模式踩坑点：**graph capture 阶段不建立数据依赖的 offload plan**——capture 时检测到 `is_graph_capture` 为真则直接返回、不 record 计算依赖事件，否则会把 capture 期的具体 page 依赖固化进图（见 [npu-graph-mode](../../../concepts/techniques/npu_graph_mode.md)）。每层用「已入队」标志去重，防同层重复 enqueue。

## D2H 写回：连续一一对应时用整块 copy_ 而非 scatter

prefill 阶段当前层整层 cache 在设备与 host 侧均布局连续、源与目的一一对应（无 paged / 乱序 slot 需求）时，直接用整块 `dst.copy_(src, non_blocking=True)`，而**非**按 `slot_mapping` 的 `npu_scatter_nd_update_` 索引 scatter——scatter 的按索引间接寻址在连续一一对应场景下不产生任何布局收益、只徒增开销。⚠️ 该等价**仅在连续一一对应时成立**；写回目标是非连续 / 乱序 slot（paged KV 的 decode 写回）时仍须用 scatter。

## Correctness / 收益 / 风险 / rollback

- **容量收益（仓自报、无独立复测）**：同序列长度下最大 batch size 可翻倍；固定 64K 序列 global batch 1024→2048，固定 global batch 128 序列 256K→384K（基于 MTP3 + perfect eplb 配置采集）。度量为内存容量上限、非吞吐。
- **correctness**：reviewer 仅确认非 offload 基线在新镜像正常，未给 offload 开启态独立精度数字。
- **风险**：offload 引入的 H2D 是 decode 新增开销，靠 decode 侧跨-step gather-selection 复用摊薄；进一步降耗（跨 layer 预取等）为 open。
- **rollback**：offload 开关默认关闭，关掉即回退全量设备 KVCache。

## Evidence

- `diff 事实`（@18c1d975c6ec）：Host-swap 分配 `empty_with_swapped_memory`、专用 `d2h_stream` / `d2h_event`（下一层 wait 后复用单层 temp）、decode `npu_gather_selection_kv_cache`、offload 开关键。容量数字为 doc 披露（`+33/-7` KVCache Offload / Benchmark 节，仓自报）。
- `diff 事实`（@99cf645981392c）：HSTU 逐层异步 offload + 四类事件同步链 + capture 期跳过 plan（`gpu_kv_cache_manager.py` / `inference_ranking_gr.py`）；性能结论仅 doc 披露、无数字。
- `diff 事实`（@75ae5d4b1ce6）：offload prefill 写回两处 `npu_scatter_nd_update_` → 连续 `copy_` 替换；无 benchmark 数字，「为何更省」为机制推断。
- 溯源下探：
  - [cann-recipes-infer-pr-134-feat-deepseek-v3-2-exp-model-support-kv-cache-offload](https://gitcode.com/cann/cann-recipes-infer/merge_requests/134)
  - [cann-recipes-infer-pr-282-feat-hstu-model-add-kv-offload-and-optimize-preprocessing](https://gitcode.com/cann/cann-recipes-infer/merge_requests/282)
  - [cann-recipes-infer-pr-139-bug-replace-scatter-nd-update-with-copy-for-better-performance](https://gitcode.com/cann/cann-recipes-infer/merge_requests/139)