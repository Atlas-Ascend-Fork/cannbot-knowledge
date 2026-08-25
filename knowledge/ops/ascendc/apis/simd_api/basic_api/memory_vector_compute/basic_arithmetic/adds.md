---
type: API
title: Adds
description: 双目矢量标量计算接口，将矢量tensor每个元素与标量求和。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Adds.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Adds

标量矢量计算接口，每个元素加上标量值。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src_i + scalarValue。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Add](add.md)（`related`）：Add 对两个 tensor 逐元素求和，Adds 对 tensor 与 scalar 求和；选择取决于第二操作数是否需要物化为 tensor。
- [Adds](../../reg_vector_compute/basic_arithmetic/adds.md)（`same_topic`）：Reg Adds 与 Memory Tensor Adds 完成相同逐元素标量加法，可按数据驻留在 RegTensor 或 LocalTensor 选择。
- [Adds（灵活标量位置）](adds_flexible_scalar.md)（`same_topic`）：Adds（灵活标量位置） 与《Adds》的实质衔接是：灵活标量 Adds 与普通 Adds、C Reg/C Vector add-scalar 执行同一 tensor+scalar 运算；RegTensor 误用 Adds 的案例明确区分标量加与张量逐元素 Add。
<!-- cannbot:related:end -->
