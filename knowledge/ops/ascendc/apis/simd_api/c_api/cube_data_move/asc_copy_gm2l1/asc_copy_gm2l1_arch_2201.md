---
type: API
title: asc_copy_gm2l1
description: 将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l1/asc_copy_gm2l1_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_gm2l1

将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数的起始地址。；size(输入): 搬运数据大小（字节）。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为DataBlock（32字节）。取值范围：[1, 65535]。；src_gap(输入): 源操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst_gap(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst(输出): 目的操作数（矢量）的起始地址。

约束：- 各存储单元的空间大小和对齐要求
- 如果需要执行多条asc_copy_gm2l1指令，且asc_copy_gm2l1指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_gm2l1指令的串行化，防止出现异常数据。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
