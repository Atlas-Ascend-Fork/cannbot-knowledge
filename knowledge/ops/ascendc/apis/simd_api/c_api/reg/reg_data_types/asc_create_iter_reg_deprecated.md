---
type: API
title: asc_create_iter_reg (废弃)
description: 该接口已废弃，请使用asc_update_addr_reg实现此功能。 地址寄存器通过该接口初始化，然后在循环之中使用地址寄存器存储地址偏移量，该重载接口同步支持1-4个offset参数，并支持初始化b8/b16/b32位宽的寄存器，适配1-4维Tensor。底层在多维循环中自动计算地址偏移，消除标量地址运算开销。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_create_iter_reg_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_create_iter_reg (废弃)

该接口已废弃，请使用asc_update_addr_reg实现此功能。 地址寄存器通过该接口初始化，然后在循环之中使用地址寄存器存储地址偏移量，该重载接口同步支持1-4个offset参数，并支持初始化b8/b16/b32位宽的寄存器，适配1-4维Tensor。底层在多维循环中自动计算地址偏移，消除标量地址运算开销。
函数原型：iter_reg asc_create_iter_reg_b32(uint32_t offset)
返回值：地址寄存器。
约束：请勿在循环内使用 if/else。；iter_reg必须在最内层循环体内赋值使用。；不同步长的操作数，建议使用多个iter_reg，避免地址被覆盖。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AddrReg](../../../basic_api/reg_vector_compute/register_data_types/addr_reg.md)（`related`）：废弃的 CreateIterReg 说明初始化式迭代寄存器已由 AscUpdateAddrReg 取代，有助于迁移旧 AddrReg 循环代码。
- [AscCreateMask](asc_create_mask.md)（`related`）：当前迭代通常由显式 AddrReg/Mask 管理，CreateMask 补充有效 lane。
- [AscUpdateAddrReg](asc_update_addr_reg.md)（`related`）：废弃 IterReg 的地址推进可迁移为 AddrReg + UpdateAddrReg。
- [废弃接口](../../../../appendix/deprecated_interface.md)（`related`）：废弃汇总提供替代建议和版本状态。
- [寄存器数据类型](reg_data_types.md)（`same_topic`）：类型总页给出 IterReg 的废弃状态和当前寄存器类型。
<!-- cannbot:related:end -->
