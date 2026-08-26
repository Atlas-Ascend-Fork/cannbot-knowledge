---
type: Optimization
title: 变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）
description: 变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）。Prefill 里请求 seq_len 不定长（每请求长度不同），MLA 段的 FlashAttention 要选输入布局。三种候选在「免 padding」与「访存 / 转置效率」上此消彼长，选错会浪费算力或撞访存瓶颈。
tags:
- task.optimization
- topic.attention
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/72
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/17
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# 变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）

## 适用场景

Prefill 里请求 seq_len 不定长（每请求长度不同），MLA 段的 FlashAttention 要选输入布局。三种候选在「免 padding」与「访存 / 转置效率」上此消彼长，选错会浪费算力或撞访存瓶颈。

## 问题信号

- 用 BNSD 布局 `[batch, num_head, seq_len, head_dim]`：不定长请求要 padding 到统一 seq_len，短请求填大量无效计算，算力浪费。
- 用 TND 布局 `[batch*seq_len, num_head, head_dim]`（合轴成 token 数、免 padding，把请求合成一个 list 传 `actual_seq_lengths_kv=[128,256,512,1024]` 即可）：易用性好，但引入两个新问题——① 数据排布对 FA 计算不亲和、访问不连续，FA 带宽效率低；② 由 BNSD → TND 需 transpose，带来非必要计算开销。

## 做什么（手段）

Prefill MLA 的 FA 实际改用 **NTD** 布局 `[num_head, token, head_dim]`：保留 TND 的免 padding 优势，同时提升带宽效率、省掉 transpose。进一步配合两点，可完全消除 split / concat / transpose 等额外计算：

- **matmul 权重拆分**；
- **FA 支持独立的 NoPE（No Positional Encoding）与 RoPE（Rotary Positional Encoding）输入**——对应 [FIA](../../../concepts/kernels/fused_infer_attention_score.md) 的 `query_rope` / `key_rope` 分离入参，不再把 NoPE/RoPE 拼一起再切。

MLA 前置计算落在 `forward_page_attention_mla_prolog` 路径（使能 [MLA-prolog](../../../concepts/kernels/mla_prolog.md) 融合 kernel + `npu_fused_infer_attention_score`）。

## correctness / 风险

NoPE/RoPE 分离入参须与建模里 q_pe / k_rope 的实际张量对齐（`npu_fused_infer_attention_score(..., query_rope=q_pe, key_rope=k_rope, ...)`）。FIA 的 `actual_seq_lengths_kv` 类型随图 / eager 后端不同，传错会 schema 报错，见 [fia-actual-seq-lengths-kv-backend-type](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)。术语随仓演进：前置融合算子文档写 `npu_mla_prolog_v2`、代码已用 `npu_mla_prolog_v3`，本经验不依赖具体版本号。

## benchmark（仓自报，无独立复测）

相对 TND 布局，FlashAttention 计算效率提升约 **15%**（本仓 `deepseek_r1_prefill_optimization.md`「TND 格式支持」节）。仅此一个对比点，不外推为通用律。

## 参考实现及其约束

参考 cann-recipes-infer 的 [DeepSeek-R1](../../../concepts/models/deepseek_r1.md)（[Kimi-K2](../../../concepts/models/kimi_k2_thinking.md) 复用同建模，Atlas A3）prefill MLA。NTD 布局 + NoPE/RoPE 分离是消除 split/concat/transpose 的手段，可迁移到其它变长 prefill 的 [MLA](../../../concepts/modules/mla.md) FA；+15% 是该模型该对比点的仓自报值。latent-KV 缓存 + prefill 非 absorb（`NTD_TND`）展开路径见 [mla-weight-absorption-latent-kv](../rules/mla_weight_absorption_latent_kv.md)。

## Evidence

- `doc 披露`（@f5bf59cf）：`deepseek_r1_prefill_optimization.md`「TND 格式支持」节——TND 两问题、改用 NTD、+15%、NoPE/RoPE 分离消除 split/concat/transpose 均为文档原文。溯源下探 [cann-recipes-infer-pr-72-feat-add-deepseek-r1-kimi-k2](https://gitcode.com/cann/cann-recipes-infer/merge_requests/72)。
- `diff 事实`（@2c45117 / @f5bf59cf）：`modeling_deepseek.py` 的 NTD 布局处理、`forward_page_attention_mla_prolog`、`npu_fused_infer_attention_score(..., query_rope=q_pe, key_rope=k_rope)` NoPE/RoPE 分离入参。溯源下探 [cann-recipes-infer-issue-17-rfc-deepseek-r1-kimi-k2-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/17)。
- +15% 属 doc 披露、无独立复测；NTD 布局与 mla_prolog / FIA 调用为代码事实。归因主语为 cann-recipes-infer 的建模实现。
