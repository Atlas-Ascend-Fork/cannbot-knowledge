---
type: Optimization
title: MoE 专家并行跨卡分发按 prefill/decode 阶段选型：多 token 走 double-routing、少 token 走融合 dispatch/combine
description: MoE 专家并行跨卡分发按 prefill/decode 阶段选型：多 token 走 double-routing、少 token 走融合 dispatch/combine。优化一个 MoE + 专家并行(EP) 部署（moe_tp_size==1、专家均分各卡），要决定「跨卡把 token 送到目标专家再收回」的分发/合并怎么实现时。EP 下同一份建模在 prefill 与 decode 对跨卡分发的开销诉求不同，用同一套实现覆盖两阶段不是最优。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/4
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/4
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/11
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MoE 专家并行跨卡分发按 prefill/decode 阶段选型：多 token 走 double-routing、少 token 走融合 dispatch/combine

## 适用场景

优化一个 MoE + [专家并行(EP)](../../../concepts/parallelism/expert_parallel.md) 部署（`moe_tp_size==1`、专家均分各卡），要决定「跨卡把 token 送到目标专家再收回」的分发/合并怎么实现时。EP 下同一份建模在 prefill 与 decode 对跨卡分发的开销诉求不同，用同一套实现覆盖两阶段不是最优。

## 核心规则

按 `is_prefill` 在 EP 分支内分流成两条跨卡通信路径：

- **prefill（长序列、多 token）→ [double-routing](../../../concepts/techniques/double_routing.md)**：`npu_moe_init_routing_v2` 本地排序后，用两次 `dist.all_to_all_single`（先换每专家 token 计数、再换 token）路由；专家算完 `npu_moe_re_routing` 反重排、反向 all_to_all 收回、`npu_moe_finalize_routing` 加权求和。prefill 分发的是大批 token、更吃聚合带宽，变长 AllToAll 此时只发有效 token、无冗余。
- **decode（单/少 token、时延敏感）→ 融合 [dispatch/combine（MC2）](../../../concepts/techniques/moe_dispatch_combine_v2.md)**：`npu_moe_distribute_dispatch_v2` + `npu_moe_distribute_combine_v2` 把跨卡通信与专家排布融进一对算子，摊薄每步固定通信延迟，避免 double-routing 那样多段独立 all_to_all 打断流水。
- **对照**：若走 MoE 张量并行（`moe_tp_size>1`）而非 EP，则不分阶段——统一 `init_routing_v2 → GroupedMatmul → finalize_routing`，在 `moe_tp_group` 上 `all_reduce`。

## 依据（为什么 decode 选融合 dispatch/combine 而非 double-routing）

维护者确认：double-routing 会引入多次 alltoallv 通信、导致断流水，对 decode 场景影响较大；dispatch/combine 性能更好。关键澄清——**dispatch/combine 不引入额外通信量**：它只是把 dispatch 产物放进一块较大内存以避免动态 shape，实际只有一部分是有效数据，通信仍按每卡实际需要处理的 token 数分发。故两者取舍是：

- double-routing 代价 = 多次 alltoallv 打断流水，收益 = 低峰值内存；
- dispatch/combine 代价 = 较大静态内存（decode 序列短、可承受），收益 = 固定 shape 可入图、通信融合、不增通信量。

二者「主要解决的问题不同」，不是性能相当只差入图能力。

## 何时不适用 / 前置

- decode 走融合 dispatch/combine 以支持 MC2 的硬件/图模式为前提（Atlas A3 + 图模式）。A2 因每卡专家数上限、或 eager 模式下，decode 需回退 double-routing——图模式可捕获性与硬件回退见 [moe-ep-decode-graphmode-dispatch](moe_ep_decode_graphmode_dispatch.md)，平台/结构兼容边界见 [mc2-fused-comm-op-compatibility-fallback](../../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)。
- 调用融合 dispatch/combine 前须核 `HCCL_BUFFSIZE` 等通信 buffer 是否够大，见 [moe-dispatch-combine-hccl-buffsize](../../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)；MC2 还要求独占通信域，见 [mc2-dedicated-comm-domain](mc2_dedicated_comm_domain.md)。
- double-routing 技术本身（8 步 AllToAll 骨架、相对 TP/AllGather 的取舍）见 [moe-ep-double-routing-skeleton](moe_ep_double_routing_skeleton.md)。

## 参考实现及其约束

Qwen3-MoE 建模 `Qwen3MoeSparseMoeBlock.forward` 先经 `self.gate`（`npu_moe_gating_top_k_softmax` 一次算出 topk）得 `topk_idx/topk_weight`，再三路分派：`moe_tp_size>1 → moe_infer_tp`（TP-GMM + `all_reduce`）；否则 EP，`is_prefill → moe_infer_double_routing`、`else → moe_infer_dispatch_combine`（MC2，注释 `support ep for decode stage`）。这套三路分派可迁移到同为 MoE+EP 的其它模型（DeepSeek 系同构建模）；融合算子相对 all_to_all 的性能优劣幅度参考实现未给对比数据、不外推。

## 相关经验
- [256-expert MoE 的融合 allgather-EP 专家链（四算子融合，硬门控在](fused_allgather_ep_moe_256expert_deepseek_v3r1.md)
- [NPU fused_topk 默认先归一化再按 routed_scaling_factor](../../../runbooks/precision/moe_router_norm_topk_prob_fused_topk_npu.md)

## Evidence

- Qwen3-MoE 三路分派（TP-GMM / EP-prefill double-routing / EP-decode MC2）+ 各自算子调用链：diff 事实 @e8eb6979565c。溯源下探 [cann-recipes-infer-pr-4-qwen3moe](https://gitcode.com/cann/cann-recipes-infer/merge_requests/4)、[cann-recipes-infer-issue-4-rfc-qwen3-moe-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/4)。
- 「decode 用 dispatch/combine 而非 double-routing、不增通信量、按实际 token 分发」：维护者确认（无独立 benchmark）；decode 分支走 `moe_infer_dispatch_combine`、double-routing 侧多段 `all_to_all_single` 为 diff 事实 @2c45117。溯源下探 [cann-recipes-infer-issue-11-question-prefill-moe-moe-infer-double-routing](https://gitcode.com/cann/cann-recipes-infer/issues/11)。
