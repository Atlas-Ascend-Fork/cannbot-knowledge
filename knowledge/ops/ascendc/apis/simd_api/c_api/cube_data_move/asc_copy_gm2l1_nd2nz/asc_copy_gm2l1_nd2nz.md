---
type: API
title: AscCopyGm2L1Nd2Nz
description: GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1_nd2nz/asc_copy_gm2l1_nd2nz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscCopyGm2L1Nd2Nz

GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本。

将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。

本接口组包含 asc_copy_gm2l1_nd2nz_arch_2201, asc_copy_gm2l1_nd2nz_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_gm2l1_nd2nz指令，且asc_copy_gm2l1_nd2nz指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1_nd2nz指令的串行化，防止出现异常数据。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../../basic_api/cube_compute/cube_compute_load/data_copy_gm_to_l1_nd2_nz.md)（`same_topic`）：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。；将Global Memory中的ND格式数据搬运到L1 Buffer并转换为NZ格式。用于矩阵计算输入的随路格式转换搬入。。两卡在 C API 接口组与 C++ Basic API 中描述同一 GM→L1 的 ND 到 NZ 随路转换。
<!-- cannbot:related:end -->
