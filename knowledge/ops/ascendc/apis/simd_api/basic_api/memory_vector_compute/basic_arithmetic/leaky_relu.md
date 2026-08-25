---
type: API
title: LeakyRelu
description: 矢量元素执行Leaky ReLU操作：非负值原样输出，负值乘以标量系数后输出。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/LeakyRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LeakyRelu

单目矢量计算接口，按元素计算 LeakyReLU 激活。头文件 `basic_api/kernel_operator_vec_unary_intf.h`。计算公式 dst_i = max(src_i, alpha*src_i)，alpha 为斜率系数。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《LeakyRelu》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [Maxs](maxs.md)（`related`）：Maxs 与《LeakyRelu》的实质衔接是：Maxs 是 tensor 与标量逐元素取大值；Reg/灵活标量入口保持同一契约，Mins/Relu/LeakyRelu 以及 exp clamp 案例说明它在分段和限幅公式中的实际组合。
- [Mins](mins.md)（`related`）：LeakyRelu 与《Mins》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Muls](muls.md)（`related`）：LeakyRelu 与《Muls》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [AscLeakyrelu](../../../c_api/reg/arithmetic_compute/asc_leakyrelu.md)（`same_topic`）：LeakyRelu 与《AscLeakyrelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [AscLeakyrelu](../../../c_api/vector_compute/asc_leakyrelu.md)（`same_topic`）：LeakyRelu 与《AscLeakyrelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [LeakyRelu](../../reg_vector_compute/basic_arithmetic/leaky_relu.md)（`same_topic`）：LeakyRelu 与《LeakyRelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Prelu](prelu_isasi.md)（`same_topic`）：LeakyRelu 与《Prelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Relu](relu.md)（`same_topic`）：LeakyRelu 与《Relu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Relu](../../reg_vector_compute/basic_arithmetic/relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；LeakyRelu正文界定“矢量元素执行Leaky ReLU操作：非负值原样输出，负值乘以标量系数后输出”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
<!-- cannbot:related:end -->
