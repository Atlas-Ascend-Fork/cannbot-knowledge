---
type: API
title: asc_copy_gm2ub
description: 将数据从Global Memory (GM)搬运到Unified Buffer (UB)。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub/asc_copy_gm2ub_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# asc_copy_gm2ub

将数据从Global Memory (GM)搬运到Unified Buffer (UB)。
函数原型：void asc_copy_gm2ub(__ubuf__ void* dst, __gm__ void* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_gm2ub指令，且asc_copy_gm2ub指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2ub指令的串行化，防止出现异常数据。；同步计算包含同步等待。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [asc_copy_gm2ub](asc_copy_gm2ub_arch_3510.md)（`same_topic`）：“支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等”与“支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等”分别来自双方当前正文。两卡记录同名 GM→UB C API 在 arch2201 与 arch3510 的互斥产品范围；共同使用时可以按目标硬件选择正确的接口卡，而不会把 A2/A3 合同误用于 950。
<!-- cannbot:related:end -->
