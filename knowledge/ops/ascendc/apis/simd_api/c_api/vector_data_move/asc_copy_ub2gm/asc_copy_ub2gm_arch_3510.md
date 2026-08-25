---
type: API
title: asc_copy_ub2gm
description: 将数据从Unified Buffer (UB) 搬运到 Global Memory (GM)。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_ub2gm/asc_copy_ub2gm_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_copy_ub2gm

将数据从Unified Buffer (UB) 搬运到 Global Memory (GM)。
函数原型：void asc_copy_ub2gm(__gm__ void* dst, __ubuf__ void* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_ub2gm指令，且asc_copy_ub2gm指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_ub2gm指令的串行化，防止出现异常数据。；同步计算包含同步等待。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
