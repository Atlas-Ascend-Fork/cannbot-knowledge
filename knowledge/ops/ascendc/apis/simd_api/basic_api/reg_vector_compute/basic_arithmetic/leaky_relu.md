---
type: API
title: LeakyRelu
description: 按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量scalarValue后写入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/LeakyRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# LeakyRelu

按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量scalarValue后写入。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：LeakyRelu 与《中级性能优化》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [入门功能落地](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/getting_started.md)（`explains`）：LeakyRelu 与《入门功能落地》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [高阶极限打磨](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/extreme_optimization.md)（`explains`）：LeakyRelu 与《高阶极限打磨》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [AscLeakyrelu](../../../c_api/vector_compute/asc_leakyrelu.md)（`related`）：LeakyRelu 与《AscLeakyrelu》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [AscLeakyrelu](../../../c_api/reg/arithmetic_compute/asc_leakyrelu.md)（`same_topic`）：C++ Reg LeakyRelu 是同一寄存器操作的对应接口，提供直接的 C/C++ 映射。
- [LeakyRelu](../../memory_vector_compute/basic_arithmetic/leaky_relu.md)（`same_topic`）：LeakyRelu 与《LeakyRelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
- [Relu](relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；LeakyRelu正文界定“按元素执行Leaky ReLU操作，大于0的元素直接写入目的操作数，否则乘以标量scalarValue后写入”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
<!-- cannbot:related:end -->
