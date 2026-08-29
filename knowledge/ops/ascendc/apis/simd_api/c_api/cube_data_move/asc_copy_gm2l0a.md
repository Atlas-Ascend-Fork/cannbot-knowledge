---
type: API
title: AscCopyGm2l0a
description: 将数据从GM搬运到L0A Buffer。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_gm2l0a.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyGm2l0a

将数据从GM搬运到L0A Buffer。

参数：dst(输出): 目的操作数起始地址。；src(输入): 源操作数起始地址。；base_idx(输入): 分形矩阵ID，搬运起始位置为源操作数的第几个分形（0为源操作数中第1个分形矩阵）。取值范围：[0, 65535]。；repeat(输入): 迭代次数，每个迭代可以处理512B数据。取值范围：[1, 255]。；src_stride(输入): 相邻迭代间，源操作数前一个分形与后一个分形起始地址的间隔，单位：512B。取值范围：[0, 65535]。；dst_gap(输入): 相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。单位：512B。取值范围：[0, 65535]。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
