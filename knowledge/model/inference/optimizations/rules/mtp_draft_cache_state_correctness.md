---
type: Optimization
title: MTP 缓存状态约束：历史按步 KV 与递归状态按接受数写回
description: 区分固定 R1 旧实现按草稿步分配 KV、GLM-5 按预测层复用缓存，以及 Qwen3-Next 递归状态按接受数写回；先核对缓存索引和推进语义，不将某一实现的缓存份数作为通用规则。
tags:
- task.optimization
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/156
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/235
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/3242bd8b0a9d021303557172ac246e499513385f/models/deepseek-r1/models/mtp.py
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/3242bd8b0a9d021303557172ac246e499513385f/models/deepseek-r1/runner_deepseek.py
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:41:05Z'
platforms:
- agnostic
---

# MTP 缓存状态约束：历史按步 KV 与递归状态按接受数写回

## 适用场景
- 给模型接 MTP 推测解码（[mtp-speculative-decoding](../../concepts/techniques/mtp_speculative_decoding.md)）后，草稿命中率异常低 / 推测输出与主模型总不匹配 / 多步草稿越跑越偏——多半不是算法问题，而是 **draft 每步的注意力状态缓存分配或推进方式错了**。draft 的缓存正确性随注意力结构分两类处理，接入前先对号入座。

## 实现一：历史 R1 按草稿步选择 KV 槽
### 条件与版本

本节仅覆盖 R1 固定提交 `3242bd8b0a9d021303557172ac246e499513385f` 的按步缓存策略。GLM-5 固定提交 `d20ac4f4f63910bb66624b2ef542302eb3bb8dab` 则按预测层分配、就地推进，见 [MTP 缓存与分片 Prefill 记账](mtp_cache_and_microbatch_prefill_bookkeeping.md)。先核对 runner 的缓存索引、更新和回退方式，再选择策略；不能仅凭 `next_n > 1` 判断需要几份缓存。

### 该旧实现的问题信号
- draft 网络本体只有 1 层，但每轮 decode 要连跑 `next_n` 步（每步各是一次独立 draft 前向）。若沿用「按模型自身层数」的默认 `init_cache`，只会得到一份共用 cache，第 `k` 步 draft 取不到自己那层、会取错。

### 规则
- 在该 R1 旧实现中，单层 draft 跑 `next_n` 步时**每一步各取一个 KV 槽**：第 `k` 步取 `past_key_values[k]`。故按 `num_hidden_layers = next_n`（而非模型自身层数 1）分配，调用形如 `init_cache(input_ids, num_hidden_layers=next_n)`。
- 须在首次 draft 前向前完成正确份数的初始化并跨步复用。固定 runner 的 `model_input_prepare` 可在循环内首次发现 `past_key_values is None` 时按 `is_mtp` 分配 next_n 份；不要求把初始化移到循环之外，也不会因此每步重新分配。
- cache 层数要作为**外部入参**传入、与模型自身层数及 config 里的 `next_n` 解耦：只有 draft 显式传 `next_n`，主模型走缺省（回退自身层数）。否则主模型也会被错误地按 `next_n` 层分配 KV cache。

### 参考实现及其约束
- 参考：[deepseek-r1](../../concepts/models/deepseek_r1.md) 的 MTP draft（`next_n ≤ 3`，主模型 61 层、draft 1 层），用同一套 `init_cache` 靠可选 `num_hidden_layers` 入参区分主/副两条初始化路径。该区分是本规则关键，缺了它主/副模型都会按 `next_n` 走。

## 结构二：SSM / 线性注意力（递归状态）——verify 后只按接收数写回
### 问题信号
- 结构含递归状态缓存（Mamba 式 `conv_state` / `ssm_state`，如 Gated-DeltaNet / linear-attention，见 [gated-deltanet](../../concepts/modules/gated_deltanet.md)）。全注意力的 KVCache 可整段回滚，但递归状态是「逐 token 顺序累积」的，不能简单回滚——若把草稿全部 token 的状态都写回，下一轮草稿会从含未接收 token 的错误状态起算，命中率与正确性双坏。

### 规则
- verify 阶段先把草稿全部 token 的中间递归状态（intermediate conv window / intermediate ssm）算进**临时槽**；verify 后**只把前 `num_accepted_tokens` 个对应的状态写回持久 `conv_state` / `ssm_state`**，被拒 token 的状态丢弃。GDN / recurrent 融合算子须吃 `num_accepted_tokens` 才能做到这点。
- **互斥约束（别组合）**：MTP + SGLang 暂不支持图模式（`--speculative-*` 与 ACLGraph 不兼容，要上投机就放弃 ACLGraph）；暂不支持在 PD 分离下开 MTP；MTP 依赖 GDN 融合算子先使能（未开 GDN 融合则 MTP 通路不可用）。

### 参考实现及其约束
- 参考：cann-recipes-infer 的 Qwen3-Next（Gated Attention + GDN，MTP1 / NEXTN 一步草稿）。互斥约束来自该仓 Qwen3-Next 规格说明，随框架 / 算子版本可能放宽。

## 依据 / 反例
- 依据：两类结构的 diff 事实 + 维护者确认（见 Evidence）。
- 反例：对上述按步索引的旧实现只分配一个 KV 槽，会与其取槽方式不一致；不能把这一反例套到按预测层、就地推进的实现。SSM 结构把草稿全部 token 状态无条件写回 → 下一轮从错误状态起算。
- 范围：限定到「单层 draft + 多步投机」与「含递归状态的混合注意力/SSM 投机 decode」两类结构，不外推为昇腾栈通用律。框架级接入约定见 [mtp-speculative-decode-model-onboarding](../../guides/integration/mtp_speculative_decode_model_onboarding.md)。

## Evidence
- `diff 事实` + `维护者确认`（@3242bd8b0a9d，DeepSeek-R1）：`init_cache` 增可选 `num_hidden_layers` 入参、runner 按 `is_mtp` 分流（draft 传 `next_n`、主模型走缺省）、循环内 `past_key_values[next_index]` 按步取用；维护者确认「主模型也会按 next_n 初始化 kv cache，需外传入以区分主/副」固定 runner 在循环内首次输入准备时按 is_mtp 初始化 next_n 份并复用；应区分这一实际行为与未按草稿步分配的错误假设。
- `diff 事实`（@874b41df5de8，Qwen3-Next）：verify 分支按 `num_accepted_tokens` 推进，投机中间态（conv window / ssm）verify 后按有效索引写回 `conv_states` / `ssm_states`；图模式 / PD 分离互斥、依赖 GDN 融合算子为仓级约束披露。
- 溯源下探：[cann-recipes-infer-pr-156-feat-adapt-mtp3](https://gitcode.com/cann/cann-recipes-infer/merge_requests/156)、[cann-recipes-infer-pr-235-feat-support-qwen-next](https://gitcode.com/cann/cann-recipes-infer/merge_requests/235)