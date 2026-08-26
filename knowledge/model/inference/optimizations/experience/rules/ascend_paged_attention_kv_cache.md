---
type: Optimization
title: 昇腾 Paged-Attention KV cache：无需专用算子（block_table/slot_mapping 同 vLLM）+ offline 分配前显存预校验
description: 昇腾 Paged-Attention KV cache：无需专用算子（block_table/slot_mapping 同 vLLM）+ offline 分配前显存预校验。要在昇腾上做非连续（分页）KV Cache 以块为单位管理显存、支持多请求共享有限 NPU 显存（高并发、避免为每请求预分配整段序列长度），或要把 Ascend 注意力层接到 vLLM 等分页 KV 框架。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/150
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/388
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾 Paged-Attention KV cache：无需专用算子（block_table/slot_mapping 同 vLLM）+ offline 分配前显存预校验

## 适用场景

要在昇腾上做非连续（分页）KV Cache 以块为单位管理显存、支持多请求共享有限 NPU 显存（高并发、避免为每请求预分配整段序列长度），或要把 Ascend 注意力层接到 vLLM 等分页 KV 框架。

## 契约 · 不需要专用 paged-attention 算子

昇腾上做分页注意力**不需要另造一个「paged attention 专用算子」**——用标准 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md) v2 + KV 写回算子，靠喂索引结构达成分页，且与 vLLM 相同的 block_table / slot_mapping 约定，故样例注意力层可直接移植到 vLLM 等分页 KV 框架：

- **Decode 读分页 KV**：给 `npu_fused_infer_attention_score_v2` 传 `block_table` + `block_size`，从块池物理 cache 张量按块表寻址读非连续 KV。Prefill 对当前 prompt token 直接算 FA（不带 `block_table`），算完再写回。
- **KV 写回**：用 `npu_scatter_nd_update_` 按 `slot_mapping` 把新 K/V 散写进块池（`dst.view(-1, num_kv_heads, head_dim)`、`slot_mapping.view(-1, 1)`、`src`）。
- **框架侧索引由 KVCacheManager 三层结构产出**（[kv-cache-manager](../../../concepts/frameworks/kv_cache_manager.md)）：`KVCacheManager`（请求级总协调）→ `SingleTypeKVCacheManager`（单 attention type 逻辑块管理，Full / SlidingWindow）→ `BlockPool`（物理 block 发放 / 回收）；`prepare_block_tables()` / `prepare_slot_mapping()` 按 `attn_type` 组织成字典。

**迁移时的算子约束（坑）**：融合注意力 / 分页算子**要求 block_table 中每一项都是合法 block 索引、不能有空洞**。故实现上额外申请一个 `_null_block` 占位块用于逻辑对齐（不承载真实 KV）：逻辑块表长度须与 `⌈kv_len/block_size⌉` 对齐，滑窗失效的历史 block 位置用 `_null_block` 占位并把物理块归还池。把 vLLM 的 block_table / slot_mapping 正确喂进算子、并保证块表无非法 / 空洞索引（必要时补 null block）即可移植。

## offline 分块分配前必做显存预校验

offline 批量推理的分页 KV cache 预分配（`offline_max_len` 已知固定长度分支）里，`calculate_block_num` 若只按固定 token 长度推 `block_num`、不校验实际空闲显存，当 `offline_max_len × batch × per_token_bytes` 超过空闲 HBM 时会照常返回块数，真正的显存不足要到后续 KV cache 张量分配才暴露、报错深、信息不友好。

**修法**：算出 `block_num` 后、return 前用 `torch.npu.mem_get_info()` 预校验——`required = (block_num+1)*block_size*per_token_bytes + fixed_block_memory_bytes`，`required > free_memory` 则提前 `raise MemoryError`，并附「缩短请求长度 / 减小总 batch」的可操作提示。把「事后深层崩溃」前移为「事前明确报错」。

## 参考实现及其约束

契约参考 cann-recipes-infer 的 [gpt-oss](../../../concepts/models/gpt_oss.md) 样例（`GptOssAttention.forward` / `update_cache` + `docs/design/kv_cache_design.md`）；预校验参考通用 executor 的 `executor/core/kv_cache/cache_utils.py`。「可直接移植 vLLM」为维护者定性、无独立复测；DeepSeek / Kimi / GLM 的 MLA+indexer decode FA 路径与 gpt_oss 的普通 FIA 不同，未逐一核，不对其算子细节作断言。范围限定本仓 offline executor / gpt_oss 样例，未外推整栈。

## 相关经验
- [跨层 KV-sharing（CLA）模型在昇腾上误选 PrefillNoCache：共享层要](../../../runbooks/runtime/vllm_ascend_cla_kv_sharing_forces_chunked_prefill.md)

- 另见 [online decode 调度防 KV 打满死锁：入场预留 + cheapest-victim retraction + break→continue](../cases/online_decode_kv_admission_retraction.md)。


## Evidence

- `diff 事实` + `维护者确认`（@2c45117）：`GptOssAttention` decode 分支带 `block_table` / `block_size`、`update_cache` 用 `npu_scatter_nd_update_` + `slot_mapping`；`kv_cache_design.md` 的三层结构 + `_null_block` 系「算子要求 block table 必须存在合法 block 索引」的占位；维护者确认样例 FA/KVCache-update 算子 PA 场景可 work、可移植 vLLM。
- `diff 事实`（@c0f5c30949703c）：`calculate_block_num` offline 分支新增 `torch.npu.mem_get_info()` 预校验块并 `raise MemoryError`；「过大 offline_max_len×batch 会深层崩溃」为守卫的显见意图（据代码 + 报错文案推断）。
- 溯源下探：
  - [cann-recipes-infer-issue-150-question-paged-attention-kv-cache](https://gitcode.com/cann/cann-recipes-infer/issues/150)
  - [cann-recipes-infer-pr-388-fix-fix-page-attention-cache-management-and-packed-sequence](https://gitcode.com/cann/cann-recipes-infer/merge_requests/388)
