---
type: API
title: AscCopyGm2UbAlign
description: 提供数据非对齐搬运功能，将数据从GM搬运到UB，支持8位/16位/32位数据类型搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_copy_gm2ub_align/asc_copy_gm2ub_align_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscCopyGm2UbAlign

提供数据非对齐搬运的功能，将数据从Global Memory (GM)搬运到Unified Buffer (UB)，并支持8位/16位/32位数据类型搬运。 本接口支持以下两种数据搬运方式： 若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐，支持以下两种填充方式：
约束：本接口在非AIV上调用直接返回。；各存储单元的空间大小和对齐要求请参考存储单元说明。；如果本指令与其他指令的目的地址存在重叠，需要插入同步指令（asc_sync_notify和asc_sync_wait），保证多个指令的串行化，防止出现异常数据。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetCopyPadVal](../asc_set_copy_pad_val.md)（`related`）：“若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐”产生填充区，“设置连续搬运数据块左右两侧需要填补的数据值”定义该填充区的值，二者是配套调用。
- [asc_copy_gm2ub](../asc_copy_gm2ub/asc_copy_gm2ub_arch_3510.md)（`related`）：“如果需要执行多条asc_copy_gm2ub指令，且asc_copy_gm2ub指令的目的地址存在重叠，需要插入同步指令”给出常规 3510 GM→UB 搬运的覆盖同步约束，“若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐”说明非对齐变体会扩张实际写入范围，二者联读可判断重叠。
- [AscCopyGm2UbAlign](asc_copy_gm2ub_align_arch_2201.md)（`same_topic`）：“提供数据非对齐搬运的功能，将数据从Global Memory (GM)搬运到Unified Buffer (UB)，并支持8位/16位/32位数据类型搬运。 本接口支持以下两种数据搬运方式： 若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐，支持以下两种填充方式：”与“提供数据非对齐搬运的功能，将数据从Global Memory (GM)搬运到Unified Buffer (UB)，并支持8位/16位/32位数据类型搬运。 本接口支持以下两种数据搬运方式： 若搬运数据长度非32字节对齐，搬运数据会补齐至32字节对齐，支持以下两种填充方式： 约束：本接口在非AIV上调用直接返回。；各存储单元的空间大小和对齐要求请参考存储单元说明。；如果本指令与其他指令的目的地址存在重叠，需要插入同步指令（asc_sync_notify和asc_sync_wait），保证多个指令的串行化，防止出现异常数据。”分别来自双方当前正文。两卡都定义非对齐 GM→UB 搬运；3510 额外规定非 AIV 返回和重叠地址通知等待，2201 则规定零长度 NOP，关系用于迁移时选择正确边界。
<!-- cannbot:related:end -->
