---
type: Optimization
title: paged KV cache 按阶段选散点写算子：Prefill 连续段用 scatter_update_、Decode 单 token 用 scatter_nd
description: paged KV cache 按阶段选散点写算子：Prefill 连续段用 scatter_update_、Decode 单 token 用 scatter_nd。往 paged KV cache 写 K/V 时，prefill 与 decode 的写入形态不同——用同一个散点写算子覆盖两阶段不是最优。prefill 一次写入一整段新序列（从 position 0 起连续），decode 每步只追加 1 token 到某个可变 slot。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/197
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# paged KV cache 按阶段选散点写算子：Prefill 连续段用 scatter_update_、Decode 单 token 用 scatter_nd

## 适用场景

往 [paged KV cache](../../../concepts/frameworks/kv_cache_manager.md) 写 K/V 时，prefill 与 decode 的写入形态不同——用同一个散点写算子覆盖两阶段不是最优。prefill 一次写入一整段新序列（从 position 0 起连续），decode 每步只追加 1 token 到某个可变 slot。

## 条件 → 用哪个写算子

按 `is_prefill` 分支选散点算子：

- **prefill（整段从 position 0 连续写）→ `torch_npu.scatter_update_`**：传全 0 `indices` + `axis=1`，每个 batch 从序列位 0 起把 `[0:S]` 连续写进 BSND 布局 cache——是**连续内存整段写**，避免 `scatter_nd` 的逐 token 散点索引写。作者代码注 `scatter_update_ performs better in prefill stage`。
- **decode（单 token 写可变 slot）→ `torch_npu.npu_scatter_nd_update_`**：每步只追加 1 token 到 paged cache 里一个可变 slot，是**离散寻址写**，`slot_mapping` + `scatter_nd` 才对得上，decode 不改。

```python
if is_prefill:
    # scatter_update_ performs better in prefill stage（indices 全 0 → 从位 0 连续写 [0:S]）
    torch_npu.scatter_update_(cache.view(batch, -1, D), zeros_int64_indices,
                              value.view(batch, -1, D), axis=1)
else:
    torch_npu.npu_scatter_nd_update_(cache.view(-1, 1), slot_mapping.view(-1, 1),
                                     value.view(-1, D))   # decode 单 token 写可变 slot
```

prefill 分支需一个全 0 的 `kv_scatter_update_indices = torch.zeros((batch,), dtype=torch.int64)` 作 `axis=1` 起始位。

## 受用点（同一份 cache 两阶段走不同写入算子）

- [indexer](../../../concepts/kernels/lightning_indexer.md) 的 `past_key_scales_indexer` / `past_key_values_indexer` 写入；
- [MLA-prolog](../../../concepts/kernels/mla_prolog.md) 写回 nope / rope cache（CP 分支 all-gather 还原后用同一 indices 分别写 nope `view(bsnd_bsz,-1,kv_lora_rank)` / rope `view(bsnd_bsz,-1,qk_rope_head_dim)` cache）。

## 边界 / 关联

- 覆盖 `kv_cache_quant_mode ∈ {int8(C8), 非量化}`；证据仅本仓 [DeepSeek-V3.2-Exp](../../../concepts/models/deepseek_v3_2_exp.md)（[DSA](../../../concepts/modules/dsa.md) = Lightning Indexer + MLA）的 `indexer.py` / `modeling_deepseek.py`。
- 「prefill 下 scatter_update_ 更快」仅作者代码注释、**无 benchmark、无独立复测**，只作定性理由。
- 叠加 zigzag-CP 时，prefill 不能按全局 `slot_mapping` 直写 paged cache，须先 all-gather 还原全序再 `scatter_update_` 写回（两段式），见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)——本页的连续 `scatter_update_(axis=1)` 正是那里「写回真 cache」的算子选择。

## Evidence

- `diff 事实`（@ea8d712a02e2）：`models/deepseek-v3.2-exp/models/indexer.py` 与 `modeling_deepseek.py` 的 `if is_prefill: scatter_update_ … else: npu_scatter_nd_update_` 两处（indexer 的 scales / states、MLA-prolog 的 nope / rope）逐条对上；`kv_scatter_update_indices = torch.zeros((batch_size,))` + 两句注释原文对上。
- 性能仅定性（代码注释），不并入事实面。
- 溯源下探：[cann-recipes-infer-pr-197-fix-tmp-kv-cache-set-to-bsnd-scatter-nd-update-replace-to-scatter-update](https://gitcode.com/cann/cann-recipes-infer/merge_requests/197)