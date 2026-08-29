---
type: Optimization
title: MTP 投机解码的两个记账约束：KV cache 按预测层数(非草稿步数)分配 + 与分片 prefill 共存时延后补跑 draft 步
description: MTP 投机解码的两个记账约束：KV cache 按预测层数(非草稿步数)分配 + 与分片 prefill 共存时延后补跑 draft 步。实现 MTP 投机解码（next_n>1，多草稿步）推理，尤其要它与分片 / multi-batch-per-die prefill调度共存时。有两个默认假设会出错——KV cache 按什么分配、draft 步在分片 prefill 里何时跑。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/290
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MTP 投机解码的两个记账约束：KV cache 按预测层数(非草稿步数)分配 + 与分片 prefill 共存时延后补跑 draft 步

## 适用场景

实现 [MTP 投机解码](../../../concepts/techniques/mtp_speculative_decoding.md)（`next_n>1`，多草稿步）推理，尤其要它与[分片 / multi-batch-per-die prefill](../../../concepts/techniques/prefill_micro_batch.md)调度共存时。有两个默认假设会出错——KV cache 按什么分配、draft 步在分片 prefill 里何时跑。

## 约束一：MTP KV cache 按预测层数分配、一份 cache 就地推进

- **别按草稿步数 `next_n` 分配**：那会为 mpt3 保留 3 份 MTP cache，并被迫维护一套 per-step 备份/还原状态机（decode 循环里逐步备份各份 cache、切副本、循环后整份还原）。根因是把「草稿步数」误当「cache 层数」——草稿步只是对同一批 MTP 预测层反复迭代，层数应是 `num_nextn_predict_layers`（常远小于 `next_n`），与迭代步数无关。
- **规则**：cache 层数取 `num_nextn_predict_layers`（KV cache 与 [offload cache](../../../concepts/techniques/kvcache_offload.md) 同口径）；草稿步之间在**同一份 cache 上推进 `kv_len`**，删掉逐步备份/还原与 per-step 换 cache 旁路，把「拼 spec_token / 滑动 input_ids」并入统一的单步推进逻辑。
- 收益：MTP KV cache 从 `next_n` 份降为 `num_nextn_predict_layers` 份、去掉备份/还原状态机（`num_nextn_predict_layers` 来自 checkpoint 的 HF config、仓内不硬编码，故只述「按实际预测层数分配」）。

## 约束二：与分片 prefill 共存时，prefill cycle 内 MTP 只跑一步、剩余 draft 步延后补跑

- **draft 步调度冲突**：若每个 prefill cycle 都把 `next_n` 个 MTP draft 步全跑完，会与「逐 cycle 推进」的分片调度冲突——分片 prefill 尚未走完时不能提前生成后续 draft 步。
  - **规则**：分片 prefill（cycle 仍在进行）时 MTP 循环执行一步即退出（本 cycle 只做 prefill）；所有 prefill cycle 结束、进 decode 前，一次性补跑剩余 `next_n-1` 个 draft 步，并把补出的 spec_token 拼回主模型 `input_ids`。
- **actual_seq_lengths 假设失效**：原 prefill 分支的 `actual_seq_lengths`（kv 侧 pad 到 `input_max_len` 再 cumsum、q 侧按单 batch 现算）隐含「单 batch per die」语义，在 multi-batch-per-die（`prefill_mini_batch_size==0`，一个 die 多 batch 同 cycle 处理）下不成立。
  - **规则**：q 侧统一为 `seq_len + i*seq_len for i in range(batch_size)`（每 batch 一个跨步偏移），kv 侧直接用传入的 `actual_seq_lengths_kv`、不再 pad+cumsum。

## 边界

规则适用面限定到「MTP + 分片 prefill」结构，参考实现为 GLM-5（MoE + [DSA](../../../concepts/modules/dsa.md)，`next_n=3`/mpt3、A3、world_size 64、batch 64），不外推到该结构以外；源未给性能/显存 before→after 数字，定量收益属推断。

## Evidence

- 分片 prefill 时 MTP 单步退出、prefill 后补跑 `next_n-1` 步并拼回 `input_ids`、`get_actual_seq_lengths` 改按 batch 跨步：diff 事实 @d20ac4f4f639（动机取自代码注释 `the mtp model performs only prefill`）。溯源下探 [cann-recipes-infer-pr-290-fix-for-glm-5-use-one-cache-data-in-mpt3-and-support-multi-batch-per-die](https://gitcode.com/cann/cann-recipes-infer/merge_requests/290)。
- cache 分配由 `next_n` 改为 `num_nextn_predict_layers`、备份/还原与 per-step 换 cache 旁路删除、草稿步就地推进：diff 事实 @d20ac4f4f639；定量收益标为推断、未并入事实面。溯源同上。

<!-- cannbot:related:start -->
## 相关

- [MTP 草稿模型的缓存/状态正确性（按注意力结构）：单层 draft 需 next_n 层 KV、SSM 递归状态按接收数推进](mtp_draft_cache_state_correctness.md)（`same_topic`）：遇到 cache 份数争议时，先用“cache 层数取 `num_nextn_predict_layers`（KV cache 与 ［offload cache］(../../../concepts/techniques/kvcache_offload.md) 同口径）”核对 checkpoint 是否真的有多预测层，再用“单层 draft 跑 `next_n` 步时**每一步各需一层 KV cache**：第 `k` 步取 `past_key_values［k］`。”核对单层 draft 是否以 past_key_values［k］ 分步取用，避免把两种结构的规则互相套用。
<!-- cannbot:related:end -->
