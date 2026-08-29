---
type: API
title: AscCopyGm2L1
description: GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1/asc_copy_gm2l1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscCopyGm2L1

GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。

将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。

本接口组包含 asc_copy_gm2l1_arch_2201, asc_copy_gm2l1_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_gm2l1指令，且asc_copy_gm2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1指令的串行化，防止出现异常数据。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
