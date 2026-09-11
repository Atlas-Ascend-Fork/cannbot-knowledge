---
type: Optimization
title: MC2 dispatch/combine（fullmesh_v2）必须独占一个 HCCL 通信域，不能与 EP/TP/CP 复用
description: MC2 dispatch/combine（fullmesh_v2）必须独占一个 HCCL 通信域，不能与 EP/TP/CP 复用。规划一个用 MC2 融合 dispatch/combine（npu_moe_distribute_dispatch_v2/combine_v2）的 MoE EP decode 部署的通信域时。会有两个直觉都要纠正：（1）图省事把 MC2 挂到已有的 moe_ep_group 上跑；（2）以为独立建域是为了避开 TP 通信冲突。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/421
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/462
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MC2 dispatch/combine（fullmesh_v2）必须独占一个 HCCL 通信域，不能与 EP/TP/CP 复用

## 适用场景

规划一个用 [MC2 融合 dispatch/combine（`npu_moe_distribute_dispatch_v2/combine_v2`）](../../../concepts/techniques/moe_dispatch_combine_v2.md)的 MoE [EP](../../../concepts/parallelism/expert_parallel.md) decode 部署的通信域时。会有两个直觉都要纠正：（1）图省事把 MC2 挂到已有的 `moe_ep_group` 上跑；（2）以为独立建域是为了避开 TP 通信冲突。

## 核心规则

- **MC2 dispatch/combine 只能独占通信域**，不能与任何其它通信域复用——**连 prefill 的 EP/CP 通信域都不能复用**。这不是「为避 TP 冲突」，而是这对算子本身要求非共享通信组（`comm_alg="fullmesh_v2"` 拓扑的硬要求）。
- 因此给 MC2 单独建 `moe_ep_group_mc2`（拓扑与 `moe_ep_group` 一致），dispatch/combine 在这个非共享组上跑；`dispatch_kwargs` 带 `"comm_alg": "fullmesh_v2"`（`combine_kwargs` 不加）。
- **独立域顺带解决 buffer 归位**：只给 `moe_ep_group_mc2` 按需放大 HCCL buffer（`calc_moe_hccl_buffer_size(..., is_full_mesh_v2=True)`），普通 `moe_ep_group`（EP all-to-all）回落默认 env buffer——放大 buffer 只对 decode MC2 路径必要，压在共享 EP 域上是过配。buffer 不足的失败签名见 [moe-dispatch-combine-hccl-buffsize](../../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)。
- **注**：dispatch/combine 是一对 all-to-all 通信算子，**本身不含专家 GMM**——GMM 计算独立于这对通信算子之外。

## 前置 / 落点

- `set_mc2_kwargs()` 应在 `process_weights_after_loading` 阶段（HCCL 组已起、首次 forward 前）预构建 dispatch/combine kwargs，**避免在被 trace 的 decode 图区内构建 kwargs** 触发 graph guard miss。
- `dispatch_kwargs`/`combine_kwargs` 的 `group_ep`/`group_tp` 从 `moe_ep_group_name` 改绑 `moe_ep_group_mc2` 的名字。

## 适用范围

规则适用面 = 用 MC2 dispatch/combine 的 MoE EP decode 通信域规划（参考实现覆盖 DeepSeek-V3.2-Exp / DeepSeek-R1 / GLM-5 / Kimi-K2-Thinking / Qwen3-MoE 等 5 个启用 fullmesh_v2 的 MoE，及 LongCat 系建独立域但不启用 fullmesh_v2 的零专家变体），不外推为整个昇腾栈。含零专家的 MoE 走 MC2 时 dispatch 用默认 `comm_alg`（fullmesh_v2 不支持零专家），见 [mc2-fused-comm-op-compatibility-fallback](../../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md) 与 [moe-zero-expert-copy-expert-num](moe_zero_expert_copy_expert_num.md)。

## Evidence

- 新建独立 `moe_ep_group_mc2` + `dispatch_kwargs` 追加 `comm_alg=fullmesh_v2` + buffer 从 `moe_ep_buffer_size` 归位到 `moe_ep_mc2_buffer_size`、`moe_ep_group` 删 `hccl_buffer_size` 回落默认：diff 事实 @d4b8eb61；「只有 decode mc2 需要单独配置这个 size」「moe_ep_group use default」为维护者确认。溯源下探 [cann-recipes-infer-pr-421-refactor-mc2-use-independent-communication-group](https://gitcode.com/cann/cann-recipes-infer/merge_requests/421)。
- 「MC2 不能与任何其它通信域复用、即使 prefill EP/CP 也不能」「dispatch/combine 不含 GMM」：维护者确认（严重级 review 纠正 + 作者采纳）+ `set_mc2_kwargs` 独立组 + fullmesh_v2 diff 事实 @895615c；`set_mc2_kwargs` 在 `process_weights_after_loading` 预构建避免图区构建。溯源下探 [cann-recipes-infer-pr-462-refactor-longcat-flash-lite-tnd-pa-npugraph-ex-mc2-ep-decode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/462)。