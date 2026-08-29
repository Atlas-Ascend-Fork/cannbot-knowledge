---
type: API
title: AscCopyUb2ub
description: 将数据从Unified Buffer搬运到Unified Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_ub2ub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscCopyUb2ub

将数据从Unified Buffer搬运到Unified Buffer。
函数原型：void asc_copy_ub2ub(__ubuf__ void* dst, __ubuf__ void* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_ub2ub指令，且asc_copy_ub2ub指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_ub2ub指令的串行化，防止出现异常数据。；同步计算包含同步等待。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
