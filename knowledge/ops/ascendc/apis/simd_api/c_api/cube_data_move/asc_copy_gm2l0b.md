---
type: API
title: AscCopyGm2l0b
description: 将矩阵数据从GM搬运到L0B Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l0b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyGm2l0b

将矩阵数据从Global Memory搬运到L0B Buffer。

参数：dst(输出): 目的操作数（矢量）的起始地址。；src(输入): 源操作数（矢量）的起始地址。；base_idx(输入): 以16*16个数对矩阵进行分块，搬运的起始分块ID。；repeat(输入): 迭代次数。；src_stride(输入): 相邻迭代间，源操作数前一个分形与后一个分形起始地址的间隔。；dst_gap(输入): 相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。

约束：- 各存储单元的空间大小和对齐要求

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
