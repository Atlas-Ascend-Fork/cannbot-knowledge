---
type: Optimization
title: 多流并行后还要分核：limit_core_num 给两条重路径流配不同 Cube/Vector 核数、让时长趋近
description: 多流并行后还要分核：limit_core_num 给两条重路径流配不同 Cube/Vector 核数、让时长趋近。已经给 decode 开了多流并行（如把 MoE/共享专家旁路切到副流），但 profile 里两条流时长差很多、明显拖尾，整体关键路径没缩短时。尤其两条路径都很重（attention 主路径与 FFN/shortcut-MoE 副路径都吃算力）的模型。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/351
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多流并行后还要分核：limit_core_num 给两条重路径流配不同 Cube/Vector 核数、让时长趋近

## 适用场景

已经给 decode 开了多流并行（如把 MoE/共享专家旁路切到副流），但 profile 里两条流时长差很多、明显拖尾，整体关键路径没缩短时。尤其两条路径**都很重**（attention 主路径与 FFN/shortcut-MoE 副路径都吃算力）的模型。

## 问题信号 / 根因

单纯多流并行不一定稳定获益：一个流可能吃掉过多 Core、另一个流即使切出去也跑不起来；一个流拖尾、另一个流提前结束，整体关键路径仍长。关键不是「多流」本身，而是**多流之后还要分核**——两条流没显式分配核数时争抢 Cube/Vector 核，时长失衡。

## 做什么

主流跑 dense/attention 主路径，副流提前执行重的旁路（如 shortcut MoE），用 `limit_core_num(True, aic, aiv)` 给两条流分配不同 AI Core / Vector Core 数，让两流时长更接近：

```python
if (self.enable_multi_stream > 0) and not is_prefill:
    return self.multi_stream_forward(...)
# 副流：shortcut MoE 放 "1" 号流、单独控核
with npu_stream_switch(True, "1"):
    with limit_core_num(True, self.aic_num1, self.aiv_num1):
        shortcut_mlp_output = self.mlp(hidden_states_norm, is_prefill, cur_topk_list=cur_topk_list)
# 主路径：另一套核数配置
with limit_core_num(not self.enable_afd, self.aic_num2, self.aiv_num2):
    ...  # dense/attention 主路径
```

四者耦合设计：`limit_core_num`（分核）+ `npu_stream_switch`（多流）+ [`npu_prefetch`](../../../concepts/techniques/weight_prefetch.md) + [superkernel](../../../concepts/techniques/superkernel.md) 在此案例一起用，拆开后收益可能不成立。

## 何时不适用 / 风险

- `aic_num*/aiv_num*` 不是通用值——控核参数要结合 profile 调整，硬搬别的模型的核数配比大概率不最优。
- 分核是「两条流都够重」时的手段；若副路径很轻，分核反而饿死主路径。
- 控核本身有代价：控核后每条流只能用部分核、算子受算力约束（见 AFD 里「解除控核反而提速」的对照 [afd-attn-ffn-disaggregation](afd_attn_ffn_disaggregation.md)）。分核是同卡多流方案内部的再平衡，不是无脑加。
- 关联：共享专家 decode 双流重叠的基本骨架见 [moe-shared-expert-decode-dual-stream](../rules/moe_shared_expert_decode_dual_stream.md)。

## 收益

参考实现（LongCat-Flash Stage2 decode）未给 before→after 数字；定性目标为让双流时长趋于接近、缩短双路径 decode 关键路径。

## Evidence

- `npu_stream_switch` + `limit_core_num(enable, aic, aiv)` 两套核数配置 + `npu_prefetch` 的耦合并行段：diff 事实 @d739fecb4232（skill 示例具名披露 LongCat-Flash，未逐字核模型源建模文件；`aic_num*/aiv_num*` 具体数值未给、案例强调按 profile 调，无 benchmark）。溯源下探 [cann-recipes-infer-pr-351-feat-update-agent-skills-with-full-optimization-pipeline-and-role-based](https://gitcode.com/cann/cann-recipes-infer/merge_requests/351)。
