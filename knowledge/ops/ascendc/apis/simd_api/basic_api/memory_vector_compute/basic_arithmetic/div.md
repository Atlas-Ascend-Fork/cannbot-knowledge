---
type: API
title: Div
description: 双目矢量计算接口，对两个输入tensor按元素求商。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Div.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Div

双目矢量计算接口，按元素相除。头文件 `basic_api/kernel_operator_vec_binary_intf.h`。计算公式 dst_i = src0_i / src1_i。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Divs（灵活标量位置）](divs_flexible_scalar.md)（`related`）：Div 与《Divs（灵活标量位置）》的实质衔接是：这些入口执行同一逐元素除法语义，分别落在 memory、Reg、C Reg/C Vector 层；灵活标量 Divs 补充标量位于任一操作数时的调用选择。
- [AscDiv](../../../c_api/reg/arithmetic_compute/asc_div.md)（`same_topic`）：Div 与《AscDiv》的实质衔接是：这些入口执行同一逐元素除法语义，分别落在 memory、Reg、C Reg/C Vector 层；灵活标量 Divs 补充标量位于任一操作数时的调用选择。
- [AscDiv](../../../c_api/vector_compute/asc_div.md)（`same_topic`）：AscDiv 与《Div》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
- [Div](../../reg_vector_compute/basic_arithmetic/div.md)（`same_topic`）：Div 与《Div》的实质衔接是：这些入口执行同一逐元素除法语义，分别落在 memory、Reg、C Reg/C Vector 层；灵活标量 Divs 补充标量位于任一操作数时的调用选择。
<!-- cannbot:related:end -->
