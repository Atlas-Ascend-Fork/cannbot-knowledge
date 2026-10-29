---
type: Optimization
title: 带零/恒等专家的 MoE 用 copy_expert_num 在 MC2 dispatch/combine 内免掉专门 AllToAll
description: 带零/恒等专家的 MoE 用 copy_expert_num 在 MC2 dispatch/combine 内免掉专门 AllToAll。MoE 结构里有一类零计算 / 恒等专家（输出 MoE(x)=x、无 FFN），走 EP 切分、路由专家与零专家均分到每卡时。直觉会为零专家单独走一条计算分支、或为它的 identity 贡献单独再 AllToAll 交换一遍 token 回本地做 identity——这两种都多余。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:41:05Z'
platforms:
- a3
---

# 带零/恒等专家的 MoE 用 copy_expert_num 在 MC2 dispatch/combine 内免掉专门 AllToAll

## 适用场景

MoE 结构里有一类**零计算 / 恒等专家**（输出 `MoE(x)=x`、无 FFN），走 [EP](../../concepts/parallelism/expert_parallel.md) 切分、路由专家与零专家均分到每卡时。直觉会为零专家单独走一条计算分支、或为它的 identity 贡献单独再 AllToAll 交换一遍 token 回本地做 identity——这两种都多余。

## 核心规则

昇腾 [MC2 融合 dispatch/combine（`npu_moe_distribute_dispatch_v2/combine_v2`）](../../concepts/techniques/moe_dispatch_combine_v2.md)靠 `copy_expert_num` 参数原生处理零专家：把 `copy_expert_num` 设为零专家数（**而非默认 0**），combine 算子就对专家 ID 落在 `[n_routed_experts, n_routed_experts+zero_expert_num)` 区段的 token 直接就地产出 `input*weight`（即 `MoE(ori_x)=ori_x`）。identity 贡献折进 MC2 dispatch/combine，**不必在建模里为零专家单开计算路径，也不必额外一次 AllToAll hop**。

配套约定：
- `expert_num = n_routed_experts + zero_expert_num`；来源变量 `zero_expert_mask = topk_ids < n_routed_experts` 实际选中路由专家，随后将这些位置的权重清零，留下零专家权重。真正的零专家选择区间是 `n_routed_experts <= topk_ids < n_routed_experts + zero_expert_num`。
- 阶段分流仍按取向走：Prefill 恒走 [double-routing](../../concepts/techniques/double_routing.md) AllToAll（每芯片可用、对每 rank 专家数无约束）；Decode 才在 `enable_moe_mc2_dispatch` 开时切 MC2 融合路径。阶段选型见 [moe-ep-dispatch-path-by-stage](moe_ep_dispatch_path_by_stage.md)。

## 前置条件 / 约束

- 用前检查 `HCCL_BUFFSIZE` 等通信 buffer 配置合理（见 [moe-dispatch-combine-hccl-buffsize](../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)）。
- 迁移到别的模型前须确认其零专家语义确为 `MoE(ori_x)=ori_x`；`copy_expert_num` 的算子内语义随 MC2 算子版本，用前对当前算子核一遍。
- **与 fullmesh_v2 互斥**：MC2 `comm_alg="fullmesh_v2"` 不支持零专家计算——含零专家的 MoE 走 MC2 时 dispatch 用默认 `comm_alg`、不加 fullmesh_v2（仍建独立通信域）。这条结构兼容边界详见 [mc2-fused-comm-op-compatibility-fallback](../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md) 与 [mc2-dedicated-comm-domain](mc2_dedicated_comm_domain.md)。

## 参考实现

LongCat-Flash 族含零专家：建模里两处传 `"copy_expert_num": self.num_zero_experts`（`= config.zero_expert_num`）给 dispatch/combine。LongCat-Flash-Lite 有 128 个 zero 专家，`_set_mc2_kwargs` 取 `copy_expert_num=self.zero_expert_num`、`zero_expert_num=0`、`const_expert_num=0`，`_forward_ep_decode` 用 `dispatch_v2/combine_v2`。规则适用面 = 带 zero/identity 专家的 MoE EP，不外推为整栈通用律。

## Evidence

- `copy_expert_num=zero_expert_num` 传参 + 零专家 mask + `expert_num=n_routed+zero`：diff 事实 @0640521a8170；`MoE(ori_x)=ori_x` 语义为文档披露 + 传参佐证。溯源下探 [cann-recipes-infer-pr-124-feat-support-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/124)。
- `_set_mc2_kwargs` 的 `copy_expert_num=zero_expert_num`、prefill double-routing / decode MC2 分派：diff 事实 @8fd8db72；`copy_expert_num` 算子内语义据代码调用、未对 MC2 算子规格独立核。溯源下探 [cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)。