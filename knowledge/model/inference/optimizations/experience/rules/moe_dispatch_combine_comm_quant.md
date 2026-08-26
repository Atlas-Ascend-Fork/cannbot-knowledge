---
type: Optimization
title: MoE dispatch/combine 通信侧量化：dispatch 量化模式随激活 dtype、combine 通信可开 MXFP8（昇腾 950）
description: MoE dispatch/combine 通信侧量化：dispatch 量化模式随激活 dtype、combine 通信可开 MXFP8（昇腾 950）。MoE 走 EP dispatch/combine，在低比特量化下要决定「token 派发/回收这对通信算子该用什么量化模式」，或想对 combine 阶段的 all-to-all 数据做低精度传输降通信量时。注意区分：这是通信侧量化，和专家 GMM 的权重量化是两回事（后者见 moe-expert-gmm-weight-lowbit-prep）。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.precision
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/410
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/450
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- '950'
---

# MoE dispatch/combine 通信侧量化：dispatch 量化模式随激活 dtype、combine 通信可开 MXFP8（昇腾 950）

## 适用场景

MoE 走 [EP dispatch/combine](../../../concepts/techniques/moe_dispatch_combine_v2.md)，在低比特量化下要决定「token 派发/回收这对通信算子该用什么量化模式」，或想对 combine 阶段的 all-to-all 数据做低精度传输降通信量时。注意区分：**这是通信侧量化，和专家 GMM 的权重量化是两回事**（后者见 [moe-expert-gmm-weight-lowbit-prep](moe_expert_gmm_weight_lowbit_prep.md)）。

## 规则一：dispatch 量化模式跟着激活 dtype 走，与权重位宽无关

MoE token 派发（dispatch/combine）的量化模式由**激活 dtype** 决定、**不随权重位宽变**：`w4a8int4` 与 `w8a8int8` 同用 `dispatch_quant_mode = 2`（int8 派发）。int4 只作用于专家 grouped_matmul 的权重，激活侧仍走 a8（int8）per-token 动态量化（进 GMM 前 `npu_dynamic_quant`）。映射规律：`*a8int8 → 2`、`*a8mxfloat* → 4`，即 W4A8 与对应 W8A8 共用同一 dispatch 量化路径。

**工程结论**：给 MoE 加 W4A8-int4 时**无需新增 dispatch 量化模式或新的通信/量化通路**，直接复用既有 int8(a8) 派发，差异集中在 GMM 权重侧。

## 规则二：combine 通信在昇腾 950 上可开 MXFP8 降通信量

MoE dispatch/combine 是 EP all-to-all，通信量大、combine（把各专家结果聚回）尤其吃带宽。`moe_distribute_combine` 算子暴露 `comm_quant_mode` 选 combine 通信的量化方式，量化发生在算子通信内部、**对外部建模逻辑不感知**。在昇腾 950（A5）上给 `combine_kwargs["comm_quant_mode"] = 4`（=MXFP8）即把 combine 阶段 all-to-all/reduce 数据量化为 MXFP8、降通信传输量：

```python
if self.platform_version == "950":
    # comm_quant_mode=4 denotes MXFP8 quantization
    self.combine_kwargs["comm_quant_mode"] = 4
```

- **适用边界**：用 `platform_version == "950"` 精确门控，仅 950/A5 启用；其它平台不置该 kwarg（走各自默认、不做 combine MXFP8 通信量化）。
- 收益（combine 通信量下降）为该手段的设计意图，参考实现未给 benchmark、MXFP8 通信量化对端到端精度的影响也未披露——用前须自行评估精度。

## Evidence

- `dispatch_quant_mode` 新增 `"w4a8int4": 2`（与 `w8a8int8` 同值）、int4 权重-only、激活 `npu_dynamic_quant` 到 int8：diff 事实 @6857a2062f66。溯源下探 [cann-recipes-infer-pr-410-feat-w4a8int4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/410)。
- `platform_version=="950"` 门控 + `combine_kwargs["comm_quant_mode"]=4`（MXFP8）：diff 事实 + 维护者确认（`4` 表示走 mxfp8）@a9f61599688c；「外部不感知 / combine 通信内部量化」为作者披露，收益/精度影响未实测。溯源下探 [cann-recipes-infer-pr-450-feat-a5-combine-quant](https://gitcode.com/cann/cann-recipes-infer/merge_requests/450)。
