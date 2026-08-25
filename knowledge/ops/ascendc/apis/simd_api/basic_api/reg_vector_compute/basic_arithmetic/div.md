---
type: API
title: Div
description: 对srcReg0和srcReg1按元素相除，结果写入dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Div.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Div

对srcReg0和srcReg1按元素相除，结果写入dstReg。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscDiv](../../../c_api/reg/arithmetic_compute/asc_div.md)（`same_topic`）：Div 与《AscDiv》的实质衔接是：这些入口执行相同逐元素除法，分别位于 Reg、Memory、C Reg/C Vector 层；Divs 补充一个操作数为标量时的调用契约。
- [AscDiv](../../../c_api/vector_compute/asc_div.md)（`same_topic`）：AscDiv 与《Div》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
- [Div](../../memory_vector_compute/basic_arithmetic/div.md)（`same_topic`）：Div 与《Div》的实质衔接是：这些入口执行同一逐元素除法语义，分别落在 memory、Reg、C Reg/C Vector 层；灵活标量 Divs 补充标量位于任一操作数时的调用选择。
- [Divs（灵活标量位置）](../../memory_vector_compute/basic_arithmetic/divs_flexible_scalar.md)（`same_topic`）：Div 与《Divs（灵活标量位置）》的实质衔接是：这些入口执行相同逐元素除法，分别位于 Reg、Memory、C Reg/C Vector 层；Divs 补充一个操作数为标量时的调用契约。
<!-- cannbot:related:end -->
