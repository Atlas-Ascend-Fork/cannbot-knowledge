---
type: API
title: Exp
description: 对srcReg按元素进行指数运算，结果写入dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Exp

对srcReg按元素进行指数运算，结果写入dstReg。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../../../../../runbooks/precision/ascend950_ftz_exp.md)（`exemplifies`）：该精度卡用实测说明 Ascend950 Exp 对 subnormal 输入输出的 FTZ 边界，直接补充 Reg Exp 特殊值验证与误差判读。
- [Exp](../../../adv_api/math_compute/exp_interface/exp.md)（`related`）：高阶 Exp 可选泰勒展开并管理临时空间，和基础 Reg Exp 的显式寄存器实现形成抽象层与 workspace 的选型边界。
- [Exp](../../memory_vector_compute/basic_arithmetic/exp.md)（`related`）：Memory Exp 与 Reg Exp 都计算自然指数，但前者直接操作 LocalTensor、后者显式管理 RegTensor 和 mask，可据编程模型选择实现。
- [AscExp](../../../c_api/reg/arithmetic_compute/asc_exp.md)（`same_topic`）：AscExp 与《Exp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
<!-- cannbot:related:end -->
