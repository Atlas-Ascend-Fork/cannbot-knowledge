---
type: API
title: Maxs（灵活标量位置）
description: 矢量元素与标量取最大值，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Maxs_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Maxs（灵活标量位置）

Maxs 的灵活标量位置变体，每个元素与标量取最大值，支持标量操作数位置灵活配置。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMaxScalar](../../../c_api/vector_compute/asc_max_scalar.md)（`related`）：AscMaxScalar 与《Maxs（灵活标量位置）》的实质衔接是：Reg 与基础 MaxScalar 操作同一 vector-scalar 最大值，MinScalar 给出相反选择边界。
- [Maxs](../../reg_vector_compute/basic_arithmetic/maxs.md)（`related`）：Maxs 与《Maxs（灵活标量位置）》的实质衔接是：Reg Maxs 是 vector-scalar 下限 clamp，Mins/Max/其他层级 Maxs 对照操作数形态；Exp/FTZ/sigmoid 卡直接验证 clamp 阈值改变数值尾部。
- [Maxs](maxs.md)（`same_topic`）：Maxs 与《Maxs（灵活标量位置）》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
<!-- cannbot:related:end -->
