---
type: API
title: AscCopyL12Bt
description: L1到Bt Buffer数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12bt/asc_copy_l12bt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscCopyL12Bt

L1到Bt Buffer数据搬运接口集合，包含不同架构版本。

将数据从L1 Buffer搬运到BiasTable Buffer中，BiasTable Buffer用于存放矩阵计算中的Bias。

本接口组包含 asc_copy_l12bt_arch_2201, asc_copy_l12bt_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；操作数地址重叠约束请参考通用地址重叠约束。；当采用前n个数据搬运接口时，搬运数据大小要求32字节对齐。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
