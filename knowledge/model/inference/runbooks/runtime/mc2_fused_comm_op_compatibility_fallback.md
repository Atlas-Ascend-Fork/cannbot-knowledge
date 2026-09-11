---
type: Runbook
title: MC2 融合通信算子的平台/结构兼容性约束与回退（A2 专家上限、mm-reduce-scatter、fullmesh_v2 零专家）
description: MC2 融合通信算子的平台/结构兼容性约束与回退（A2 专家上限、mm-reduce-scatter、fullmesh_v2 零专家）。启用 MC2 融合通信算子（把 matmul / MoE dispatch·combine 与集合通信融成单算子的快 EP 路径）跑 MoE 推理时，有三条已知兼容性边界，命中会在 A2 上报错或不使能。要用 MC2 前先对照，未满足就按下面回退到非融合等价路径。所有约束都是本仓部署配置层面的门控，不是"该算子只能跑某平台"的绝对合约。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/405
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/178
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/421
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# MC2 融合通信算子的平台/结构兼容性约束与回退（A2 专家上限、mm-reduce-scatter、fullmesh_v2 零专家）

## 信号（现象）

启用 [MC2](../../concepts/techniques/moe_dispatch_combine_v2.md) 融合通信算子（把 matmul / MoE dispatch·combine 与集合通信融成单算子的快 [EP](../../concepts/parallelism/expert_parallel.md) 路径）跑 MoE 推理时，有三条已知兼容性边界，命中会在 A2 上报错或不使能。要用 MC2 前先对照，未满足就按下面回退到非融合等价路径。所有约束都是本仓部署配置层面的门控，不是"该算子只能跑某平台"的绝对合约。

## 约束一：A2 上 MC2 dispatch/combine v2 的每 rank 专家数上限

- **触发**：Atlas A2 + ge_graph + MC2 `npu_moe_distribute_dispatch_v2` 跑 EP-decode，且每 rank 专家数超上限。LongCat-Flash-Lite EP8 时 `experts_per_rank = n_routed_experts / ep = 256/8 = 32`，超过 MC2 op unlayered 模式 `moe_expert_num` 上限（代码/yaml 注释：≤24）。
- **根因**：MC2 融合 dispatch/combine 是 Atlas A3 + ge_graph 的快 EP-decode 路径；A2 的 unlayered tiling 限制每 rank 专家数。（≤24 为注释所述，未对 MC2 算子规格独立核验、可能随算子版本变化。）
- **回退**（yaml，二选一）：
  - `model_config.exe_mode: eager` —— 放弃图模式 + MLA prolog，每芯片可跑但更慢。
  - `model_config.custom_params.enable_moe_mc2_dispatch: false` —— 保图 + MLA prolog，decode 改走 Prefill 同款 [double_routing AllToAll](../../concepts/techniques/double_routing.md) 路径，在 A2 上跑 EP。
- 分派默认值：`enable_moe_mc2_dispatch` 缺省 = `(exe_mode == "ge_graph")`，即 ge_graph 默认开、eager 默认关。

## 约束二：A2 上 `npu_mm_reduce_scatter_base`（o_proj matmul + ReduceScatter 融合）未使能

- **触发**：Atlas A2（`torch.npu.get_device_name()` 含 `Ascend910B`）+ EP 分支（`moe_ep_size > 1`）。HunyuanImage-3.0 的 attention 输出投影处直接调该 MC2 式融合算子会报错。融合算子**只出现在 EP 分支内**，非 EP 分支本就走独立 o_proj。
- **根因**：A2 平台未使能这个把 `o_proj` 权重 matmul 与 ReduceScatter 融成单算子的 MC2 式算子（仓内文档追注"A2平台下暂未使能该融合算子"）。
- **回退**：`moe_ep_size > 1` 分支内按设备名拆分——含 `Ascend910B` 走"独立 `o_proj` matmul + 通用 `dist.reduce_scatter`"，否则走原融合路径。两路 layout 不同：融合路 rearrange 成 `(s b) (n d)` 沿第 0 轴切；A2 回退 rearrange 成 `b s (n d)` 先做独立 `o_proj`，再手动按 s 轴切成 `moe_ep_size` 块 `dist.reduce_scatter(..., op=SUM, group=moe_ep_group)`。

```python
if self.moe_ep_size > 1:
    if pad_len > 0:
        attn_output = F.pad(attn_output, (0, 0, 0, pad_len), mode="constant", value=0.0)
    if "Ascend910B" in torch.npu.get_device_name():          # A2 回退：融合前两步等价
        attn_output = rearrange(attn_output, 'b n s d -> b s (n d)')
        attn_output = self.o_proj(attn_output)               # 独立 matmul
        new_output = torch.empty([bsz, s_per_rank, h], ...)
        dist.reduce_scatter(new_output,
            [attn_output[:, i*s_per_rank:(i+1)*s_per_rank, :].contiguous()
             for i in range(self.moe_ep_size)],
            op=dist.ReduceOp.SUM, group=self.moe_ep_group)
    else:                                                    # A3 等：MC2 融合
        attn_output = rearrange(attn_output, 'b n s d -> (s b) (n d)')
        attn_output = torch_npu.npu_mm_reduce_scatter_base(
            attn_output, self.o_proj.weight.transpose(0, 1), <hccl_comm_name>,
            self.moe_ep_size, reduce_op='sum')
```

- 分支判断**必须置于 `moe_ep_size > 1` 之内**（融合算子只在 EP 分支用到，维护者 review 确认）。回退路丢了 matmul+通信融合的收益，是 A2 上的兼容性代价、非性能优化。仓内文档另注：调用该融合算子时 s 轴必须在最内侧、否则精度问题。

## 约束三：MC2 `fullmesh_v2` 通信算法不支持零专家（copy_expert）

- **不要**给含零专家计算的 MoE 启用 `comm_alg="fullmesh_v2"`。给 5 个 MoE（DeepSeek-V3.2-Exp / DeepSeek-R1 / GLM-5 / Kimi-K2-Thinking / Qwen3-MoE）的 `dispatch_kwargs` 都加了 `comm_alg="fullmesh_v2"`，唯独 [LongCat-Flash](../../concepts/models/longcat_flash.md) 不加——因其有零专家（`combine_kwargs` 带 `copy_expert_num = self.num_zero_experts`），fullmesh_v2 不支持零专家计算。
- 适用边界：只约束 fullmesh_v2 这条通信算法；零专家 MoE 仍建独立 `moe_ep_group_mc2` 通信域（拓扑一致），只是 dispatch 走默认 `comm_alg`。"fullmesh_v2 为何不支持零专家"为仓自报（作者披露）、源未展开机理。

## 相关经验
- [大 MoE 昇腾部署选型：并行形态/模型变体按集群规模选 + 非默认平台(310P/950)](../../optimizations/experience/rules/ascend_deploy_parallel_variant_and_nondefault_platform.md)

## Evidence

- **约束一（A2 专家上限）**
  - **代码事实**（clone `@8fd8db72`）：`longcat_flash_lite_ep8.yaml` 头注 "A2 fallback: MC2 dispatch_v2 caps moe_expert_num <= 24 in unlayered mode (Lite has 32/rank at ep=8)" + 两条回退；`LongcatFlashMoE.__init__` 的默认逻辑。回退机制为 diff 事实，≤24 为注释来源。
  - 溯源下探：[cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)
- **约束二（mm-reduce-scatter 未使能）**
  - **代码事实**：`models/hunyuan-image-3.0/adaptor_patches/hunyuan.py` 的设备分支与两条 layout、doc "(A2平台下暂未使能该融合算子)"。设备分支为 diff 事实。
  - **维护者确认**：融合算子只在 EP 分支用到；报障侧 issue（HunyuanImage-3.0 在 A2 EP 并行报错）确认 `npu_mm_reduce_scatter_base` 在 A2「暂未使能」、按设备名回退。
  - 溯源下探：[cann-recipes-infer-pr-405-fix-a2](https://gitcode.com/cann/cann-recipes-infer/merge_requests/405)、[cann-recipes-infer-issue-178-bug-report-models-hunyuan-image-3-0](https://gitcode.com/cann/cann-recipes-infer/issues/178)
- **约束三（fullmesh_v2 零专家）**
  - **代码事实**（clone `@d4b8eb61`）：6 模型 `set_mc2_kwargs` 差异化处理（5 加 `comm_alg=fullmesh_v2`、longcat-flash 不加且带 `copy_expert_num`）。
  - **仓自报**："fullmesh_v2 不支持零专家"为作者描述披露、与 diff 差异化自洽。
  - 溯源下探：[cann-recipes-infer-pr-421-refactor-mc2-use-independent-communication-group](https://gitcode.com/cann/cann-recipes-infer/merge_requests/421)