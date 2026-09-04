---
type: Optimization
title: MTP 草稿模型的缓存/状态正确性（按注意力结构）：单层 draft 需 next_n 层 KV、SSM 递归状态按接收数推进
description: MTP 草稿模型的缓存/状态正确性（按注意力结构）：单层 draft 需 next_n 层 KV、SSM 递归状态按接收数推进。给模型接 MTP 推测解码（mtp-speculative-decoding）后，草稿命中率异常低 / 推测输出与主模型总不匹配 / 多步草稿越跑越偏——多半不是算法问题，而是 draft 每步的注意力状态缓存分配或推进方式错了。draft 的缓存正确性随注意力结构分两类处理，接入前先对号入座。
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
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MTP 草稿模型的缓存/状态正确性（按注意力结构）：单层 draft 需 next_n 层 KV、SSM 递归状态按接收数推进

## 适用场景
- 给模型接 MTP 推测解码（[mtp-speculative-decoding](../../../concepts/techniques/mtp_speculative_decoding.md)）后，草稿命中率异常低 / 推测输出与主模型总不匹配 / 多步草稿越跑越偏——多半不是算法问题，而是 **draft 每步的注意力状态缓存分配或推进方式错了**。draft 的缓存正确性随注意力结构分两类处理，接入前先对号入座。

## 结构一：全注意力（KV cache）——单层 draft 跑 next_n 步需 next_n 层 KV
### 问题信号
- draft 网络本体只有 1 层，但每轮 decode 要连跑 `next_n` 步（每步各是一次独立 draft 前向）。若沿用「按模型自身层数」的默认 `init_cache`，只会得到一份共用 cache，第 `k` 步 draft 取不到自己那层、会取错。

### 规则
- 单层 draft 跑 `next_n` 步时**每一步各需一层 KV cache**：第 `k` 步取 `past_key_values[k]`。故按 `num_hidden_layers = next_n`（而非模型自身层数 1）分配，调用形如 `init_cache(input_ids, num_hidden_layers=next_n)`。
- 分配必须发生在**进入 draft 循环之前**；逐步的输入准备已在循环内部，靠它的默认初始化只会每步生成一份共用 cache，撑不起多步 draft。
- cache 层数要作为**外部入参**传入、与模型自身层数及 config 里的 `next_n` 解耦：只有 draft 显式传 `next_n`，主模型走缺省（回退自身层数）。否则主模型也会被错误地按 `next_n` 层分配 KV cache。

### 参考实现及其约束
- 参考：[deepseek-r1](../../../concepts/models/deepseek_r1.md) 的 MTP draft（`next_n ≤ 3`，主模型 61 层、draft 1 层），用同一套 `init_cache` 靠可选 `num_hidden_layers` 入参区分主/副两条初始化路径。该区分是本规则关键，缺了它主/副模型都会按 `next_n` 走。

## 结构二：SSM / 线性注意力（递归状态）——verify 后只按接收数写回
### 问题信号
- 结构含递归状态缓存（Mamba 式 `conv_state` / `ssm_state`，如 Gated-DeltaNet / linear-attention，见 [gated-deltanet](../../../concepts/modules/gated_deltanet.md)）。全注意力的 KVCache 可整段回滚，但递归状态是「逐 token 顺序累积」的，不能简单回滚——若把草稿全部 token 的状态都写回，下一轮草稿会从含未接收 token 的错误状态起算，命中率与正确性双坏。

### 规则
- verify 阶段先把草稿全部 token 的中间递归状态（intermediate conv window / intermediate ssm）算进**临时槽**；verify 后**只把前 `num_accepted_tokens` 个对应的状态写回持久 `conv_state` / `ssm_state`**，被拒 token 的状态丢弃。GDN / recurrent 融合算子须吃 `num_accepted_tokens` 才能做到这点。
- **互斥约束（别组合）**：MTP + SGLang 暂不支持图模式（`--speculative-*` 与 ACLGraph 不兼容，要上投机就放弃 ACLGraph）；暂不支持在 PD 分离下开 MTP；MTP 依赖 GDN 融合算子先使能（未开 GDN 融合则 MTP 通路不可用）。

### 参考实现及其约束
- 参考：cann-recipes-infer 的 Qwen3-Next（Gated Attention + GDN，MTP1 / NEXTN 一步草稿）。互斥约束来自该仓 Qwen3-Next 规格说明，随框架 / 算子版本可能放宽。

## 依据 / 反例
- 依据：两类结构的 diff 事实 + 维护者确认（见 Evidence）。
- 反例：单层 draft 按自身层数（1）分配 KV → 多步 draft 共用一份、互相踩；SSM 结构把草稿全部 token 状态无条件写回 → 下一轮从错误状态起算。
- 范围：限定到「单层 draft + 多步投机」与「含递归状态的混合注意力/SSM 投机 decode」两类结构，不外推为昇腾栈通用律。框架级接入约定见 [mtp-speculative-decode-model-onboarding](../../../guides/experience/interventions/mtp_speculative_decode_model_onboarding.md)。

## Evidence
- `diff 事实` + `维护者确认`（@3242bd8b0a9d，DeepSeek-R1）：`init_cache` 增可选 `num_hidden_layers` 入参、runner 按 `is_mtp` 分流（draft 传 `next_n`、主模型走缺省）、循环内 `past_key_values[next_index]` 按步取用；维护者确认「主模型也会按 next_n 初始化 kv cache，需外传入以区分主/副」「需在进入循环前初始化，默认初始化只生成一份共用 cache」。
- `diff 事实`（@874b41df5de8，Qwen3-Next）：verify 分支按 `num_accepted_tokens` 推进，投机中间态（conv window / ssm）verify 后按有效索引写回 `conv_states` / `ssm_states`；图模式 / PD 分离互斥、依赖 GDN 融合算子为仓级约束披露。
- 溯源下探：[cann-recipes-infer-pr-156-feat-adapt-mtp3](https://gitcode.com/cann/cann-recipes-infer/merge_requests/156)、[cann-recipes-infer-pr-235-feat-support-qwen-next](https://gitcode.com/cann/cann-recipes-infer/merge_requests/235)

<!-- cannbot:related:start -->
## 相关

- [MTP Speculative Decoding](../../../concepts/techniques/mtp_speculative_decoding.md)（`related`）：MTP 状态机要求“按 n 选择性回写”，draft 缓存正确性要求进一步细化为“只把前 `num_accepted_tokens` 个对应的状态写回持久 `conv_state` / `ssm_state`”；两类约束围绕 MTP 接受前缀与缓存推进这一核心决策分别给出总机制和结构化排障规则。
- [给新模型接入 MTP 推测解码：draft 模型构造 / 权重共享 / prev_hidden_states / 三元组注册 / 无损 verify](../../../guides/experience/interventions/mtp_speculative_decode_model_onboarding.md)（`related`）：draft 的 KV / 递归状态缓存分配另有结构相关的正确性坑（单层 draft 需 `next_n` 层 KV、SSM 递归状态按接收数推进）；draft 的缓存正确性随注意力结构分两类处理，接入前先对号入座。。接入指南明确把缓存分配和推进留给该规则，规则则补齐不同注意力结构下 draft 状态正确性的后续步骤。
- [MTP 投机解码的两个记账约束：KV cache 按预测层数(非草稿步数)分配 + 与分片 prefill 共存时延后补跑 draft 步](mtp_cache_and_microbatch_prefill_bookkeeping.md)（`same_topic`）：遇到 cache 份数争议时，先用“cache 层数取 `num_nextn_predict_layers`（KV cache 与 ［offload cache］(../../../concepts/techniques/kvcache_offload.md) 同口径）”核对 checkpoint 是否真的有多预测层，再用“单层 draft 跑 `next_n` 步时**每一步各需一层 KV cache**：第 `k` 步取 `past_key_values［k］`。”核对单层 draft 是否以 past_key_values［k］ 分步取用，避免把两种结构的规则互相套用。
<!-- cannbot:related:end -->
