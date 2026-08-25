---
type: API
title: Adds（灵活标量位置）
description: 矢量元素与标量做加法，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Adds_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Adds（灵活标量位置）

Adds 的灵活标量位置变体，支持标量操作数在 src0 或 src1 位置灵活配置。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [RegTensor 累加须用 Add 而非 Adds](../../../../../runbooks/compilation/regtensor_add_uses_add_not_adds.md)（`exemplifies`）：Adds（灵活标量位置） 与《RegTensor 累加须用 Add 而非 Adds》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
- [Adds](adds.md)（`same_topic`）：Adds（灵活标量位置） 与《Adds》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
- [AscAddScalar](../../../c_api/reg/arithmetic_compute/asc_add_scalar.md)（`same_topic`）：Adds（灵活标量位置） 与《AscAddScalar》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
- [AscAddScalar](../../../c_api/vector_compute/asc_add_scalar.md)（`same_topic`）：Adds（灵活标量位置） 与《AscAddScalar》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
<!-- cannbot:related:end -->
