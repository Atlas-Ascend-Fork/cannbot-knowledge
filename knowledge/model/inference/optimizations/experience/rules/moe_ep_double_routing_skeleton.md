---
type: Optimization
title: double-routing：MoE 从 TP 切 EP 把 routing/finalizing 开销降到 1/ep_size 的 8 步 AllToAll 骨架（相对 AllGather 更省峰值内存/通信）
description: double-routing：MoE 从 TP 切 EP 把 routing/finalizing 开销降到 1/ep_size 的 8 步 AllToAll 骨架（相对 AllGather 更省峰值内存/通信）。MoE 骨干推理随并行度增大时发现 routing/finalizing 成为瓶颈，或要给一个 MoE 选跨卡专家分发方案（EP 下 double-routing 还是 AllGather）时。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/305
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/17
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# double-routing：MoE 从 TP 切 EP 把 routing/finalizing 开销降到 1/ep_size 的 8 步 AllToAll 骨架（相对 AllGather 更省峰值内存/通信）

## 适用场景

MoE 骨干推理随并行度增大时发现 routing/finalizing 成为瓶颈，或要给一个 MoE 选跨卡专家分发方案（EP 下 double-routing 还是 AllGather）时。

## 为什么从 TP 切 EP：routing/finalizing 开销不随 TP 份数缩

MoE 在 [TP](../../../concepts/parallelism/tensor_parallel.md) 切分下，routing 与 finalizing 的计算量**与切分份数无关**（固定开销）：不论 RANK 数多少其开销一致，随 RANK 数增加占比越来越大且无法优化。改用 [EP](../../../concepts/parallelism/expert_parallel.md)（对 gating 切 S 轴 → per-rank gating 被切成 `ceil(S/ep_size)`）后，routing 与 finalizing 计算量降为约 **`1/ep_size`**。代价是引入 2~3 次 all_to_all 通信 + Local/Global rerouting，实现方式即 [double-routing](../../../concepts/techniques/double_routing.md)。

## double-routing 的 8 步算子调用链（可迁移的 EP MoE dispatch 骨架）

1. GatingTopK 后 **InitRouting**（`npu_moe_init_routing_v2`，`expert_tokens_num_type=1` count 模式、`quant_mode=-1` 非量化）确定本 RANK token 分给哪些专家；
2. **all_to_all**（`dist.all_to_all_single(..., group=moe_ep_group)`）把 `tokens_per_expert` 发到对应 RANK，`view(2, ep_size, -1).sum(2)` 合并 D2H 得 input/output splits；
3. **all_to_all**（第二次，带 splits）把 tokens（`expanded_x`）发到对应 RANK；
4. **LocalRerouting**（`npu_moe_re_routing`）在每个 RANK 内按专家序重排 token；
5. **GroupedMatMul**（`experts(**gmm_args)`，`group_list_type=1`）做专家计算；
6. **LocalFinalizeRerouting**（`torch.index_select(..., gathered_ids_unsort.float().argsort().int())`）排序回第二次 all_to_all 后的排布；
7. **all_to_all**（第三次）把算完的 token 发回原域内对应 RANK；
8. **FinalizeRouting**（`npu_moe_finalize_routing`，`drop_pad_mode=2`）累加专家结果。

**配套可迁移技巧**：共享专家用独立 stream 与路由专家 all_to_all/计算路径重叠掩盖（`torch.npu.Stream` + `torch.npu.Event` record/wait），见 [moe-shared-expert-decode-dual-stream](moe_shared_expert_decode_dual_stream.md)。

## double-routing 相对 AllGather 的取舍（带共享专家的 EP 部署）

带共享专家的 MoE 走 EP（路由专家均分各卡、每卡另存一份共享专家）时，**prefill 选 double-routing 而非 AllGather**：负载较均匀时每卡只取需计算的 token、无冗余，故相对 AllGather 峰值内存更低、通信量更低、通信耗时更优。

## 何时用哪条 / 关联

- prefill（多 token）用 double-routing；decode（少 token、时延敏感）用融合 dispatch/combine（大 EP 下高吞吐低时延）——阶段选型取向见 [moe-ep-dispatch-path-by-stage](moe_ep_dispatch_path_by_stage.md)。
- double-routing 的 host 端数据依赖 all_to_all 切分**不可图化**，图模式 decode 须换 MC2/local_experts，见 [moe-ep-decode-graphmode-dispatch](moe_ep_decode_graphmode_dispatch.md)。
- prefill 端 double-routing 的 dispatch/combine AllToAll 可再用 micro-batch 双流被计算掩盖。
- 结构性收益 `1/ep_size` 为源文档披露 + 机制推断，无端到端 before→after 数字，不外推「越大 ep 越快」。适用面按证据限定到本仓 MoE-EP 建模（HunyuanImage-3.0、DeepSeek-R1/Kimi-K2 同建模），不外推整栈。

## Evidence

- `moe_infer_double_routing`/`moe_dispatch_double_routing` 的 8 步算子调用链、TP routing/finalizing 不随份数缩、EP→1/ep_size + 共享专家独立 stream 掩盖：diff 事实 @f4a8014a8db0；`1/ep_size` 为源文档披露 + 机制推断。溯源下探 [cann-recipes-infer-pr-305-feat-hunyuanimage-3-0-supports-moe-ep-and-the-performance-is-optimized](https://gitcode.com/cann/cann-recipes-infer/merge_requests/305)。
- prefill 侧 double-routing（`init_routing_v2`/`re_routing`/`finalize_routing`/`all_to_all_single`）与 decode 侧 `distribute_dispatch_v2/combine_v2` 并存、double-routing 相对 AllGather 峰值内存/通信更优：diff 事实 + 本仓一手优化文档披露 @2c45117。溯源下探 [cann-recipes-infer-issue-17-rfc-deepseek-r1-kimi-k2-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/17)。

<!-- cannbot:related:start -->
## 相关

- [Expert Parallel](../../../concepts/parallelism/expert_parallel.md)（`related`）：“- 专家权重按组分布到不同 Rank”明确给出左端事实；“## double-routing 的 8 步算子调用链（可迁移的 EP MoE dispatch 骨架）”明确给出右端事实。EP 的专家分卡与跨 rank token 路由由 double-routing 页具体化为 InitRouting、三次 AllToAll、LocalRerouting、GMM 和 FinalizeRouting 的可迁移调用链。
- [MoE Double-Routing](../../../concepts/techniques/double_routing.md)（`related`）：DeepSeek-R1 / Kimi-K2 等大 EP MoE 模型在 Prefill 阶段使用的专家路由方案。；MoE 在 ［TP］(../../../concepts/parallelism/tensor_parallel.md) 切分下，routing 与 finalizing 的计算量**与切分份数无关**（固定开销）：不论 RANK 数多少其开销一致，随 RANK 数增加占比越来越大且无法优化。改用 ［EP］(../../../concepts/parallelism/expert_parallel.md)（对 gating 切 S 轴 → per-rank gating 被切成 `ceil(S/ep_size)`）后，routing 与 finalizing 计算量降为约 **`1/ep_size`**。代价是引入 2~3 次 all_to_all 通信 + Local/Global rerouting，实现方式即 ［double-routing］(../../../concepts/techniques/double_routing.md)。。概念卡定义 Prefill Double-Routing，规则卡把它落实为 TP 转 EP 后的 routing/finalizing 降本和通信骨架。
- [MoE 专家并行跨卡分发按 prefill/decode 阶段选型：多 token 走 double-routing、少 token 走融合 dispatch/combine](moe_ep_dispatch_path_by_stage.md)（`related`）：“或要给一个 MoE 选跨卡专家分发方案（EP 下 double-routing 还是 AllGather）时”；“按 `is_prefill` 在 EP 分支内分流成两条跨卡通信路径”。前者提出分发选型，后者按 Prefill/Decode 给出直接决策与回退。
- [MoeFinalizeRouting 950 ACLNN 算子知识](../../../../../ops/ascendc/operators/aclnn/transformer/moe/moe_finalize_routing_950.md)（`related`）：CANN 9.1.0 中 950 最新公开 `aclnnMoeFinalizeRoutingV3GetWorkspaceSize/aclnnMoeFinalizeRoutingV3`；内部 OpType 为 `MoeFinalizeRoutingV2`；8. **FinalizeRouting**（`npu_moe_finalize_routing`，`drop_pad_mode=2`）累加专家结果。；候选把该算子放入 EP double-routing 的最终回排和累加步骤。
- [图模式 decode 下 MoE 专家并行分发必须可图化：避开 double-routing 的 host 数据依赖 all_to_all，用 MC2 或 local_experts](moe_ep_decode_graphmode_dispatch.md)（`related`）：“代价是引入 2~3 次 all_to_all 通信 + Local/Global rerouting”；“此时［double-routing］(../../../concepts/techniques/double_routing.md)那条按 token 计数在 host 端切分的 all_to_all 会断图”。这一断图边界说明该骨架在全图 Decode 中必须迁移到静态分发路径。
<!-- cannbot:related:end -->
