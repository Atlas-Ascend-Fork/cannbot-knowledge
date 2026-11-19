---
type: Optimization
title: 变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）
description: 变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）。Prefill
  里请求 seq_len 不定长（每请求长度不同），MLA 段的 FlashAttention 要选输入布局。三种候选在「免 padding」与「访存 / 转置效率」上此消彼长，选错会浪费算力或撞访存瓶颈。
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
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-11-09T09:42:58Z'
platforms:
- a3
---

# 变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）

## 适用场景

Prefill 里请求 seq_len 不定长（每请求长度不同），MLA 段的 FlashAttention 要选输入布局。三种候选在「免 padding」与「访存 / 转置效率」上此消彼长，选错会浪费算力或撞访存瓶颈。

## 问题信号

- 用 BNSD 布局 `[batch, num_head, seq_len, head_dim]`：不定长请求要 padding 到统一 seq_len，短请求填大量无效计算，算力浪费。
- 用 TND 布局 `[batch*seq_len, num_head, head_dim]`（合轴成 token 数、免 padding，把请求Token合轴并按实际路径传长度边界；非PA入口使用累计长度，PA的KV长度另有独立语义）：易用性好，但引入两个新问题——① 数据排布对 FA 计算不亲和、访问不连续，FA 带宽效率低；② 由 BNSD → TND 需 transpose，带来非必要计算开销。

## 做什么（手段）

Prefill MLA 的 FA 实际改用 **NTD** 布局 `[num_head, token, head_dim]`：保留 TND 的免 padding 优势，同时提升带宽效率、省掉 transpose。进一步配合两点，可完全消除 split / concat / transpose 等额外计算：

- **matmul 权重拆分**；
- **FA 支持独立的 NoPE（No Positional Encoding）与 RoPE（Rotary Positional Encoding）输入**——对应 [FIA](../../concepts/kernels/fused_infer_attention_score.md) 的 `query_rope` / `key_rope` 分离入参，不再把 NoPE/RoPE 拼一起再切。

固定 R1 的 Prefill 选择 `forward_page_attention_normal`，使用 FIA v1（`npu_fused_infer_attention_score`）与 `NTD_TND`。非 Prefill 且启用 MLAProlog 才走 `forward_page_attention_mla_prolog`，后者使用 FIA v2 和 `TND_NTD`；不能把 Decode prolog 链写作 Prefill 前置。

## correctness / 风险

NoPE/RoPE 分离入参须与建模里 q_pe / k_rope 的实际张量对齐（`npu_fused_infer_attention_score(..., query_rope=q_pe, key_rope=k_rope, ...)`）。FIA 的 `actual_seq_lengths_kv` 类型随图 / eager 后端不同，传错会 schema 报错，见 [fia-actual-seq-lengths-kv-backend-type](../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)。MLAProlog v2/v3 属于另行核对的 Decode 前置接口，不用于说明本卡 Prefill normal 分支。

## benchmark（仓自报，无独立复测）

相对 TND 布局，FlashAttention 计算效率提升约 **15%**（本仓 `deepseek_r1_prefill_optimization.md`「TND 格式支持」节）。仅此一个对比点，不外推为通用律。

## 参考实现及其约束

参考 cann-recipes-infer 的 [DeepSeek-R1](../../concepts/models/deepseek_r1.md)（[Kimi-K2](../../concepts/models/kimi_k2_thinking.md) 复用同建模，Atlas A3）prefill MLA。NTD 布局 + NoPE/RoPE 分离是消除 split/concat/transpose 的手段，可迁移到其它变长 prefill 的 [MLA](../../concepts/modules/mla.md) FA；+15% 是该模型该对比点的仓自报值。latent-KV 缓存 + prefill 非 absorb（`NTD_TND`）展开路径见 [mla-weight-absorption-latent-kv](../rules/mla_weight_absorption_latent_kv.md)。

## 主线标准接口的长度补充

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的非PA TND/NTD长度为累计边界。例如请求实际长度[128,256,512,1024]应转为[128,384,896,1920]；若该数组原本已是累计值，则不能再次累加。PA路径KV长度为独立实际长度，是另一个例外。不能仅把batch与Token轴合并就把原始请求长度列表直接传给所有FIA分支。

主线v1/v2的输出布局、产品及D尺寸约束见[packed布局卡](../../guides/fia_mla_and_packed_layouts.md)。本次补充不扩大上文特定A3模型的15%观测或运行验证范围。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/72)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/17)（evidence）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score_v2.md)（constraint）
