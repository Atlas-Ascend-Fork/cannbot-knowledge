---
type: API
title: Mul
description: 根据mask对源操作数srcReg0、srcReg1按元素相乘，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Mul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Mul

根据mask对源操作数srcReg0、srcReg1按元素相乘，将结果写入目的操作数dstReg。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Reg 尾块 masked Add 清零跨块累加器](../../../../../runbooks/precision/reg_tail_mask_zeroing_clears_cross_chunk_accumulator.md)（`exemplifies`）：修复仍让 Reg《Mul》使用 tailMask，使临时平方的无效 lane 先被置零，再由 full-mask Add 安全累加。
- [MaskMergeMode](../aux_data_types/mask_merge_mode.md)（`related`）：Mul 与《MaskMergeMode》的实质衔接是：Reg Mul 的 masked 写入受 MaskMergeMode 控制；Memory Mul、Reg C API AscMul 和 Vector C API AscMul 执行同一逐元素乘法，但操作数位置、执行层与掩码接口不同。
- [Mull](mull.md)（`related`）：《Mull》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。；《Mul》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将结果写入目的操作数dstReg。。二者在Mull在Memory、Reg C接口中都产生双字宽乘积，普通Mul用于核对仅保留原字宽的不同结果合同上存在可执行的直接衔接。
- [Muls](muls.md)（`related`）：Mul 的第二操作数是 RegTensor，而 Muls 的第二操作数是 scalar，应按参数形态选择。
- [AscMul](../../../c_api/reg/arithmetic_compute/asc_mul.md)（`same_topic`）：Mul 与《AscMul》的实质衔接是：Reg Mul 的 masked 写入受 MaskMergeMode 控制；Memory Mul、Reg C API AscMul 和 Vector C API AscMul 执行同一逐元素乘法，但操作数位置、执行层与掩码接口不同。
- [AscMul](../../../c_api/vector_compute/asc_mul.md)（`same_topic`）：AscMul 与《Mul》的实质衔接是：AscMul 是 UB 向量逐元素乘法；Reg/Memory 对应入口与 scalar 变体覆盖不同承载方式，FMA 舍入和 cyclic scale 卡限定不可等价替换与广播范围。
- [Mul](../../memory_vector_compute/basic_arithmetic/mul.md)（`same_topic`）：Mul 与《Mul》的实质衔接是：Reg Mul 的 masked 写入受 MaskMergeMode 控制；Memory Mul、Reg C API AscMul 和 Vector C API AscMul 执行同一逐元素乘法，但操作数位置、执行层与掩码接口不同。
<!-- cannbot:related:end -->
