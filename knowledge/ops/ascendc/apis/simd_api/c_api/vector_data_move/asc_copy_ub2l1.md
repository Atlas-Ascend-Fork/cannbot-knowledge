---
type: API
title: AscCopyUb2l1
description: 将数据从Unified Buffer搬运到L1 Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_ub2l1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscCopyUb2l1

将数据从Unified Buffer (UB)搬运到L1 Buffer。
函数原型：void asc_copy_ub2l1(__cbuf__ void* dst, __ubuf__ void* src, uint32_t size)
约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；如果需要执行多条asc_copy_ub2l1指令，且asc_copy_ub2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_ub2l1指令的串行化，防止出现异常数据。；同步计算包含同步等待。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscCopyGm2Ub](asc_copy_gm2ub/asc_copy_gm2ub.md)（`related`）：GM→UB 与 UB→L1 组成 GM→UB→L1 数据链。
- [AscCopyUb2Gm](asc_copy_ub2gm/asc_copy_ub2gm.md)（`related`）：UB→GM 写回与 UB→L1 服务不同下游存储层。
- [AscCopyUb2ub](asc_copy_ub2ub.md)（`related`）：UB 内部搬运不离开向量存储。
- [CopyL1ToL0A](../../basic_api/cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_a.md)（`related`）：进入 L1 后可继续搬入 L0A 给 Cube 消费。
<!-- cannbot:related:end -->
