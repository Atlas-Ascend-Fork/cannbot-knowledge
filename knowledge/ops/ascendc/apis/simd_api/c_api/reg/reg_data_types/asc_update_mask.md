---
type: API
title: AscUpdateMask
description: 根据元素个数生成mask并自动扣减当前向量处理单元元素数，支持b8、b16、b32位宽模式
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_data_types/asc_update_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscUpdateMask

根据元素个数value生成mask，并自动将value减去当前向量处理单元的元素个数。支持b8、b16、b32三种位宽模式，由于VL=256B，各模式的向量处理单元元素个数为： 图1  asc_update_mask更新流程
函数原型：vector_bool asc_update_mask_b8(uint32_t& value)
返回值：vector_bool，掩码寄存器。
约束：掩码寄存器的数量上限为8，超过上限的掩码寄存器会写入预留的8K UB内存中，可能引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若两者均可用，优先复用寄存器。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
