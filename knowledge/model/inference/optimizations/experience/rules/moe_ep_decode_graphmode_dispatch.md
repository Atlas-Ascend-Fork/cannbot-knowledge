---
type: Optimization
title: 图模式 decode 下 MoE 专家并行分发必须可图化：避开 double-routing 的 host 数据依赖 all_to_all，用 MC2 或 local_experts
description: 图模式 decode 下 MoE 专家并行分发必须可图化：避开 double-routing 的 host 数据依赖 all_to_all，用 MC2 或 local_experts。在 ge_graph / npugraph_ex 全图（fullgraph）模式下跑 MoE + EP decode，且想让整层被整图捕获（拿图模式的下发头开销收益）时。此时double-routing那条按 token 计数在 host 端切分的 all_to_all 会断图，必须换一条静态形状/切分内建的分发路径。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/403
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/408
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/462
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# 图模式 decode 下 MoE 专家并行分发必须可图化：避开 double-routing 的 host 数据依赖 all_to_all，用 MC2 或 local_experts

## 适用场景

在 [ge_graph / npugraph_ex 全图（fullgraph）](../../../concepts/techniques/npu_graph_mode.md)模式下跑 MoE + [EP](../../../concepts/parallelism/expert_parallel.md) decode，且想让整层被整图捕获（拿图模式的下发头开销收益）时。此时[double-routing](../../../concepts/techniques/double_routing.md)那条按 token 计数在 host 端切分的 all_to_all 会断图，必须换一条静态形状/切分内建的分发路径。

## 问题信号

- 手动 EP 路径里出现 `combine_tokens.cpu().tolist()` 取出 `input_splits/output_splits`，再喂给变长 `all_to_all_single(gathered_tokens, output_splits, input_splits)`：切分尺寸依赖运行时 token 分布，是 host 端数据依赖，在 fullgraph 捕获下触发 **graph break**（优化报告记为「手动 EP all_to_all 数据依赖导致 fullgraph graph break」）。

## 根因

double-routing 的跨卡 token 交换要先把「每 rank 每专家收到多少 token」D2H 到 host、算出 AllToAll 的 split sizes，再发起变长 all_to_all。这个 split 是运行时 token 分布决定的动态量，图捕获期拿不到定值 → 断图。

## 修法（两条可图化路径，二选一）

图模式 decode 改走**切分内建、无 host 同步**的路径：

1. **MC2 融合 dispatch/combine**（`npu_moe_distribute_dispatch_v2` → 专家 GroupedMatmul → `npu_moe_distribute_combine_v2`）：切分由算子内部承担，全链路无 `.cpu()`、无 host 数据依赖，可整图捕获。
2. **local_experts（每 rank 算全部本地专家 + mask + AllReduce）**：每 rank 只算本地 `experts_per_rank` 个专家，非本地专家的 routing weight `masked_fill(not_local, 0)`，用固定 shape 的 `init_routing` v1，`finalize_routing` 后跨 EP group `all_reduce` 求和。与 double-routing 数学等价，但形状静态、可图化。

手动 double-routing 路径仅保留给 eager / prefill（不入图，`.cpu().tolist()` 无害）。

## 选 MC2 还是 local_experts

- **硬件门控**：MC2 `dispatch_v2` 在 Atlas A2 的 unlayered tiling 下每卡专家数封顶（约 24），超过则该路径不可用；A3 无此上限。参考实现按平台自动选默认（`platform=="A2" and experts_per_rank>24` 时默认关 MC2），A2 超限即自动回退 local_experts / double_routing。该 ≤24 上限与其它平台/结构兼容边界详见 [mc2-fused-comm-op-compatibility-fallback](../../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)。
- **小 batch/单 token decode 收益接近**：受控实测（A3、8 卡 EP=8、BS=8、input_len=256）ge_graph 下 local_experts 10.20ms vs MC2 10.50ms、npugraph_ex 下 11.59 vs 11.73，两路径输出一致。此工况（约 64 token-expert 对、AllReduce 张量约 22KB 极小）下 MC2 的两次 AllToAll 风格通信 + 输出 padding 到 `max_dispatch_tokens` 的固定开销摊不开，反慢约 0.2–0.3ms。MC2 的收益预期在更大 batch 或 prefill（每层实际路由 token 数显著增大）才体现——**仅在报告的这几组配置内陈述，不外推「越大越快」单调律**。
- 另注：Prefill 恒走 double_routing——单层 token 数超出 MC2 dispatch 的 batch 上限（约 512），与硬件无关。

## 收益 / 关联

- 把 double-routing 手动 all_to_all（graph break）换成 MC2 dispatch/combine + GMM 后，某 295B MoE 的 ge_graph decode 从 246 ms/t 降至 33.3 ms/t（约 7.4x，仓自报、无独立复测），是该阶段的主导增益。
- 阶段选型的通用取向（prefill double-routing / decode 融合）见 [moe-ep-dispatch-path-by-stage](moe_ep_dispatch_path_by_stage.md)。
- 同在 GE 图下、但落在 MoE **路由门控权重布局**（gate 转置非连续 / classifier 错误 NZ）的另一类坑见 [ge-graph-moe-gate-router-weight-layout](../../../runbooks/runtime/ge_graph_moe_gate_router_weight_layout.md)。

## Evidence

- 手动 EP 路径 `.cpu().tolist()` 数据依赖切分触发 graph break、改走 `dispatch_v2/combine_v2` 无 host 同步：diff 事实 @f7e80e5fbd73；7.4x 为优化报告仓自报。溯源下探 [cann-recipes-infer-pr-403-feat-adapt-and-optimize-hy3-preview-inference-via-deepseek-v4-pro-recipe](https://gitcode.com/cann/cann-recipes-infer/merge_requests/403)。
- 四条 forward 分派（TP / EP-prefill double-routing / EP-decode MC2 / EP-decode 图模式 local_experts）、`experts_per_rank<=24` 阈值门控、local_experts 的 mask + init_routing v1 + AllReduce：diff 事实 @8721be444490；§7.2 受控 benchmark 为仓自报、无独立复测。溯源下探 [cann-recipes-infer-pr-408-feat-add-gemma-4-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/408)。
- A2 `platform_version=="A2" and experts_per_rank>24` 自动回退 double_routing、prefill 恒 double_routing：diff 事实 @895615c；≤24/约512 上限为仓自报（代码注释 + 报告）。溯源下探 [cann-recipes-infer-pr-462-refactor-longcat-flash-lite-tnd-pa-npugraph-ex-mc2-ep-decode](https://gitcode.com/cann/cann-recipes-infer/merge_requests/462)。

<!-- cannbot:related:start -->
## 相关

- [Gemma-4-26B-A4B](../../../concepts/models/gemma4_26b_a4b.md)（`related`）：Gemma-4 的 MoE EP decode 使用 MC2 或 local_experts，避免 Double-Routing 的 Host 数据依赖阻碍图捕获。
- [MoE 专家并行跨卡分发按 prefill/decode 阶段选型：多 token 走 double-routing、少 token 走融合 dispatch/combine](moe_ep_dispatch_path_by_stage.md)（`related`）：“在 ［ge_graph / npugraph_ex 全图（fullgraph）］(../../../concepts/techniques/npu_graph_mode.md)模式下跑 MoE + ［EP］(../../../concepts/parallelism/expert_parallel.md) decode，且想让整层被整图捕获（拿图模式的下发头开销收益）时。此时［double-routing］(../../../concepts/techniques/double_routing.md)那条按 token 计数在 host 端切分的 all_to_all 会断图，必须换一条静态形状/切分内建的分发路径。”与“- **decode（单/少 token、时延敏感）→ 融合 ［dispatch/combine（MC2）］(../../../concepts/techniques/moe_dispatch_combine_v2.md)**：`npu_moe_distribute_dispatch_v2` + `npu_moe_distribute_combine_v2` 把跨卡通信与专家排布融进一对算子，摊薄每步固定通信延迟，避免 double-routing 那样多段独立 all_to_all 打断流水。”是双方正文中的具体合同。图模式规则解释 decode 阶段为何不能使用 host 动态切分，阶段选型规则则确定 decode 应落到融合 dispatch/combine；两端合起来闭合阶段判断和可图化实现路径。
- [double-routing：MoE 从 TP 切 EP 把 routing/finalizing 开销降到 1/ep_size 的 8 步 AllToAll 骨架（相对 AllGather 更省峰值内存/通信）](moe_ep_double_routing_skeleton.md)（`related`）：“代价是引入 2~3 次 all_to_all 通信 + Local/Global rerouting”；“此时［double-routing］(../../../concepts/techniques/double_routing.md)那条按 token 计数在 host 端切分的 all_to_all 会断图”。这一断图边界说明该骨架在全图 Decode 中必须迁移到静态分发路径。
<!-- cannbot:related:end -->
