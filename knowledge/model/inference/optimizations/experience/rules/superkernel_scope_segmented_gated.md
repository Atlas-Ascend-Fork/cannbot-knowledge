---
type: Optimization
title: GE 图模式 decode superkernel 按功能段分别包 scope（attention 段、MoE 段各一）+ 可门控空上下文零开销
description: GE 图模式 decode superkernel 按功能段分别包 scope（attention 段、MoE 段各一）+ 可门控空上下文零开销。在昇腾 GE 图模式（torchair）decode 上用 superkernel（tng.scope.super_kernel）融合、降低算子下发头开销，且要能按开关切换时。怎么切融合粒度、怎么让关闭态不引入额外开销，有两条可迁移写法。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/205
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# GE 图模式 decode superkernel 按功能段分别包 scope（attention 段、MoE 段各一）+ 可门控空上下文零开销

## 适用场景

在昇腾 GE 图模式（torchair）decode 上用 [superkernel](../../../concepts/techniques/superkernel.md)（`tng.scope.super_kernel`）融合、降低算子下发头开销，且要能按开关切换时。怎么切融合粒度、怎么让关闭态不引入额外开销，有两条可迁移写法。

## 规则

- **融合粒度按功能段切**：decode 层内的 **attention 段与 MoE 段各包一个** `tng.scope.super_kernel` scope（scope 名带 layer id 区分），而非整层一锅端；配合 Grouped Matmul、Dequant-Swiglu 等融合算子一起提高 NPU 计算单元利用率。
- **可门控零开销写法**：把 scope 包装成 `superkernel_scope(enable, scope, options)`——`enable` 为真才返回 `tng.scope.super_kernel(...)`，否则返回一个空的 `FakeContextManager`，使关闭态不引入任何上下文开销、且调用点 `with` 语句不必写分支。

## 边界 / 关联

- 收益方向为减算子下发头开销、提计算单元利用率，参考实现（Qwen3-MoE SGLang，`--enable-superkernel` 门控，依赖 torchair(tng)）未附独立 benchmark。适用面限昇腾 GE 图模式 decode superkernel 使能处，不外推为整栈通用律。
- superkernel 常与多流融合叠加（`option="stream-fusion=1"`），见 [moe-shared-expert-decode-dual-stream](moe_shared_expert_decode_dual_stream.md)。
- **配错易静默失效**：superkernel 开关经带默认值的 `.get(...)` 读取，yaml 键名不匹配会静默回落 False——排查「superkernel 配了却 decode 无效」见 [moe-optimization-silently-disabled-decode](../../../runbooks/performance/moe_optimization_silently_disabled_decode.md)。

## Evidence

- `superkernel_scope`（`FakeContextManager` 分支）、`tng.scope.super_kernel`、decode 层分别包 attn/moe 的 `with` 语句：diff 事实 @50e41b5b8220；「减头开销/提利用率」据 superkernel 语义 + 源描述、无独立 benchmark。溯源下探 [cann-recipes-infer-pr-205-feat-support-qwen3-moe-sglang](https://gitcode.com/cann/cann-recipes-infer/merge_requests/205)。

<!-- cannbot:related:start -->
## 相关

- [SuperKernel](../../../concepts/techniques/superkernel.md)（`related`）：TorchAir `ge_graph`（max-autotune）图模式下，**按用户声明的 scope 将计算子图整体融合为单个大 kernel** 的优化能力。；**融合粒度按功能段切**：decode 层内的 **attention 段与 MoE 段各包一个** `tng.scope.super_kernel` scope（scope 名带 layer id 区分），而非整层一锅端；配合 Grouped Matmul、Dequant-Swiglu 等融合算子一起提高 NPU 计算单元利用率。后者给出前者 scope 边界的可执行分段与门控写法。
<!-- cannbot:related:end -->
