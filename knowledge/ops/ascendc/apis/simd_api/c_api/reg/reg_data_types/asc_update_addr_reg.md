---
type: API
title: AscUpdateAddrReg
description: 更新地址寄存器用于迭代寻址，支持1至4维偏移量和b8、b16、b32三种位宽模式
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_update_addr_reg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscUpdateAddrReg

更新地址寄存器（addr_reg），用于迭代寻址。支持1~4维偏移量设置，位宽支持b8、b16、b32三种模式：

- b8模式：每次迭代地址偏移量以1字节为单位，适用于int8_t、uint8_t等类型的操作。
- b16模式：每次迭代地址偏移量以2字节为单位，适用于half、int16_t等类型的操作。
- b32模式：每次迭代地址偏移量以4字节为单位，适用于float、int32_t等类型的操作。

每次迭代时的地址偏移量计算公式为：offset = index0×stride0 + index1×stride1 + index2×stride2 + index3×stride3，其中index_i为各维度的循环迭代变量，stride_i为各维度的步长。例如在4维场景（N, C, H, W）中，offset0对应W维（最内层），offset1对应H×W，offset2对应C×H×W，offset3对应N×C×H×W。addr_reg更新后配合asc_loadalign/asc_storealign等接口使用，在循环中按设定的偏移量自动递增UB地址。

>旧接口 asc_create_iter_reg_ 已废弃，请使用 asc_update_addr_reg_ 替代。旧接口返回类型 iter_reg 也已更名为 addr_reg。
约束：请勿在循环内使用if/else。；addr_reg必须在最内层循环体内赋值使用。；不同步长的操作数，建议使用多个addr_reg，避免地址被覆盖。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
