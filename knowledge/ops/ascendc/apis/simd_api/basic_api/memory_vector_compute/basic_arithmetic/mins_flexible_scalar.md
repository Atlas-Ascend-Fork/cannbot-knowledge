---
type: API
title: Mins（灵活标量位置）
description: 矢量元素与标量取最小值，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mins_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Mins（灵活标量位置）

Mins 的灵活标量位置变体，每个元素与标量取最小值，支持标量操作数位置灵活配置。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [exp 输入 clamp 上界用 threshold 用户参数致溢出](../../../../../runbooks/precision/exp_clamp_upper_bound_must_decouple_from_user_threshold.md)（`exemplifies`）：exp 输入 clamp 上界用 threshold 用户参数致溢出 与《Mins（灵活标量位置）》的实质衔接是：故障由用户 threshold 充当 Exp 安全上界导致；Exp、Clamp/Mins、Sigmoid 公式及溢出/FTZ/Softplus 分支案例共同限定固定上界和极值验收。
- [Maxs](maxs.md)（`related`）：Maxs 与《Mins（灵活标量位置）》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [AscMinScalar](../../../c_api/reg/arithmetic_compute/asc_min_scalar.md)（`same_topic`）：AscMinScalar 与《Mins（灵活标量位置）》的实质衔接是：AscMinScalar 在 Reg 上比较 vector 与 scalar；Vector 对应入口、tensor-tensor Min、MaxScalar 和灵活 Mins 分别界定执行层、操作数形态与相反边界。
- [AscMinScalar](../../../c_api/vector_compute/asc_min_scalar.md)（`same_topic`）：MinsFlexibleScalar 提供 C++ Memory API 映射，并允许 scalar 来自 LocalTensor 单点或位于任一操作数位置。
- [Mins](mins.md)（`same_topic`）：Mins 与《Mins（灵活标量位置）》的实质衔接是：Mins 是 tensor 与标量逐元素取小值；Reg/灵活标量入口保持同一契约，Maxs/Min/Relu 组合及 exp clamp 案例说明它作为上界限幅的实际语义。
<!-- cannbot:related:end -->
