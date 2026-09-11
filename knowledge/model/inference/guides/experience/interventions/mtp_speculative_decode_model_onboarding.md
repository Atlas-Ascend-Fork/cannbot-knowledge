---
type: Guide
title: 给新模型接入 MTP 推测解码：draft 模型构造 / 权重共享 / prev_hidden_states / 三元组注册 / 无损 verify
description: 给新模型接入 MTP 推测解码：draft 模型构造 / 权重共享 / prev_hidden_states / 三元组注册 / 无损 verify。decode 尚未达计算 bound、想用推测解码（一次主模型前向多产出 token）压等效时延 / 提吞吐：把一个复用主模型输出头的 draft（MTP）模型接入通用 executor 的推测路径，每步预测 next_n 个推测 token（mtp-speculative-decoding）。 参考实现：cann-executor 的通用 MTP 路径，参考接入模型 deepseek-r1（MoE），prefill+decode 全程。
tags:
- task.debugging
- topic.speculative_decoding
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/326
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 给新模型接入 MTP 推测解码：draft 模型构造 / 权重共享 / prev_hidden_states / 三元组注册 / 无损 verify

## 适用场景
- decode 尚未达计算 bound、想用推测解码（一次主模型前向多产出 token）压等效时延 / 提吞吐：把一个复用主模型输出头的 draft（MTP）模型接入通用 executor 的推测路径，每步预测 `next_n` 个推测 token（[mtp-speculative-decoding](../../../concepts/techniques/mtp_speculative_decoding.md)）。
- 参考实现：[cann-executor](../../../concepts/frameworks/cann_executor.md) 的通用 MTP 路径，参考接入模型 [deepseek-r1](../../../concepts/models/deepseek_r1.md)（MoE），prefill+decode 全程。

## 何时不适用
- decode 已计算 bound：推测解码是用相近数据搬运换更多计算，计算已满时收益有限。
- 主模型无法在其上构造复用输出头/词嵌入的 draft（见前置条件）。

## 问题信号
- 给新模型接框架级 MTP 时最易漏三处硬约束——权重共享、`prev_hidden_states` 接口、注册形态——漏了会在加载期报错或让推测静默失效（接受率为 0 / 校验永远不匹配）。

## 前置条件
- 新模型能在主模型基础上构造 draft：draft 复用主模型的 `lm_head` / `embed_tokens`；
- draft 模型 `forward` 必须接受 `prev_hidden_states` 入参（推测算法要从主模型把上一步隐状态喂进 draft）。

## 做什么（脱离具体模型仍成立的调用约定）
- **门控 / rollback**：以 `model_config.next_n>0` 使能、`=0` 关闭回退非推测解码。`next_n>0` 却未提供 MTP 模型类时框架直接 `raise ValueError(... set next_n to 0)`。
- **权重共享**：draft 类把 `lm_head` / `model.embed_tokens` 置 `None`，框架在 `load_model` 阶段用主模型对应层填入（`share_weights_from_main_model`）；MTP checkpoint 无需单独带 `embed_tokens.weight` / `lm_head.weight`，其余层按名映射（`shared_head.norm→shared_head_norm`、`enorm` / `hnorm` / `eh_proj`）。→ 推荐在主模型上搭 MTP、直接复用输出头与词嵌入，别为 draft 单独加载一份。
- **特征融合接口**：MTP 层特征融合 = `eh_proj(concat(enorm(hidden), hnorm(prev_hidden_states)))`，返回 `(logits, prev_hidden_states)`；`prev_hidden_states` 由主模型传入，故 draft `forward` 必须显式支持该参数。
- **注册形态**：在 executor 的 `model_dict` 里，支持 MTP 的模型登记为三元组 `(主模型类, MTP 类, config 类)`；非 MTP 模型仍是二元组 `(模型类, config 类)`。

## correctness 验证（无损性保证）
- decode 每步主模型产出 `next_tokens` 后，框架逐 batch 比较推测 `spec_tokens` 与主模型 argmax 输出，遇首个不匹配即截断接受（全匹配则接受 `next_n` 个），`kv_len` 回退到接受前缀。→ 语义等价于主模型逐 token 贪心解码，接入不改变生成分布，可据此判断接入是否正确（若接受率异常低，先查 `prev_hidden_states` 与权重共享是否接对）。

## benchmark
- 源未给加速比 / 接受率数字；收益方向为 decode 未达计算 bound 时降等效时延。等效时延的正确度量口径见 [mtp-benefit-sparse-attention-and-latency-metric](../../../optimizations/experience/cases/mtp_benefit_sparse_attention_and_latency_metric.md)。

## 风险 / rollback
- 风险：漏权重共享 / `prev_hidden_states` 接口 / 三元组注册 → 加载报错或推测失效。draft 的 KV / 递归状态缓存分配另有结构相关的正确性坑（单层 draft 需 `next_n` 层 KV、SSM 递归状态按接收数推进），见 [mtp-draft-cache-state-correctness](../../../optimizations/experience/rules/mtp_draft_cache_state_correctness.md)。
- rollback：`next_n=0` 关闭 MTP、回退非推测解码。

## 相关经验
- [MoE + 投机解码：draft dummy_run 误带 profile-run 语义触发](../../../runbooks/precision/mtp_draft_dummy_run_in_profile_run_random_experts.md)

## Evidence
- `diff 事实`（@b7a110bd6812）：`load_model` 的 `next_n>0` 门控与 `ValueError`、`share_weights_from_main_model` 自动填层、`verify_spec_tokens` 的 argmax 前缀校验、`model_dict` 三元组均在合入 diff；三步接入约定取自仓内 `mtp_model_guide.md`（`doc 披露`），与代码自洽。
- 溯源下探：[cann-recipes-infer-pr-326-refactor-mtp-refactor-and-r1-adaptation-framework](https://gitcode.com/cann/cann-recipes-infer/merge_requests/326)