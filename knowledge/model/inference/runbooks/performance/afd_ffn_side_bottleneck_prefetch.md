---
type: Runbook
title: AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取
description: AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取。在 Attention-FFN 解耦（AFD）部署下（Attention 侧解除控核、计算算子提速后），profiling 里 Attention 侧的 Recv 算子长时间收不到 FFN 侧发回的数据，计算流上出现 EVENT_WAIT 间隙的拖尾。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/249
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/99
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取

## 信号（现象）

在 [Attention-FFN 解耦（AFD）](../../optimizations/experience/cases/afd_attn_ffn_disaggregation.md)部署下（Attention 侧解除控核、计算算子提速后），profiling 里 Attention 侧的 Recv 算子长时间收不到 FFN 侧发回的数据，**计算流上出现 EVENT_WAIT 间隙的拖尾**。

## 触发条件 / 根因

解耦本身会**重排瓶颈**。AFD 让 Attention 侧解除多流控核后，MLA_Prolog/FA/MM/TBMM/QBMM 等算子耗时下降，于是 FFN 侧（Router/Dispatch/MoE-GMM/Combine）反而成为新瓶颈——一侧被优化后另一侧暴露为拖尾源，是解耦部署的通用陷阱。Attention 侧 Recv 等不到 FFN 回传，就在计算流上留下 EVENT_WAIT 拖尾。

## 修法

对 FFN 侧访存 Bound 的算子（MoE-GMM、MatMul）做**通信间隙权重预取**（[`npu_prefetch`](../../concepts/techniques/weight_prefetch.md)），用 Send/Recv 通信间隙填掉访存等待、降低 FFN 侧整体耗时、消除拖尾：

- 当前层：router 出结果后预取本层 GMM2(w2) 权重 `npu_prefetch(enable_prefetch, experts.w2_weight.data, router_logits, gmm2_prefetch_size, 0)`。
- 跨层流水：拿到 `gmm2_out` 后预取**下一层** `layers[i+1]` 的 `router.classifier.weight`、`experts.w13_weight`（GMM1）。
- 预取字节数按张量规模换算（`gmm1_prefetch_size = hidden_size*intermediate_size*2*dtype_bit//...` 等）。

## 为什么 AFD 才做得了 MoE-GMM 预取（可迁移判断）

非分离场景里 Stream0 计算耗时与 Stream1 上 Router/Dispatch/MoE-GMM/Combine 耗时相当、**没有好的时间窗口**，故当时只对 QBMM/MLA_Prolog/matmul 预取、对 MoE-GMM 未做；AFD 把 MoE 独立到 FFN 节点后才腾出可预取 MoE-GMM 的时间窗。即**预取哪些权重要看该部署形态下有没有可用的通信/计算间隙，不是无脑全预取**。AFD 下 Attention 侧的权重预取与非分离场景保持一致（QBMM/MLA_Prolog/matmul）。

## 适用边界

这是 AFD 特有的可复用失败签名——下一个在 MoE 上做 AFD 的 agent 遇到 Recv EVENT_WAIT 拖尾可对号入座、优先补 FFN 侧 GMM 权重预取。参考实现为 LongCat-Flash-560B FFN 节点（Atlas A3、W8A8、torchair ge_graph）。

## Evidence

- FFN 侧层间/层内 `npu_prefetch`（router 分类器、experts w13/w2 权重）+ `gmm1/gmm2_prefetch_size` 换算：diff 事实 @72495f0ee845；「EVENT_WAIT 拖尾 + AFD 后 FFN 成瓶颈」为 doc 披露（作者 profiling 叙述、示意图，无独立复现数字），整体收益并入 AFD benchmark。溯源下探 [cann-recipes-infer-pr-249-feat-longcat-support-attention-ffn-disaggregation-afd](https://gitcode.com/cann/cann-recipes-infer/merge_requests/249)、[cann-recipes-infer-issue-99-rfc-longcat-flash-model-support-afd-feature](https://gitcode.com/cann/cann-recipes-infer/issues/99)。