---
type: API
title: asc_copy_l12fb
description: 将数据从L1 Buffer搬运到Fixpipe Buffer中，Fixpipe Buffer用于存放量化参数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12fb/asc_copy_l12fb_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# asc_copy_l12fb

将数据从L1 Buffer搬运到Fixpipe Buffer中，Fixpipe Buffer用于存放量化参数。

参数：dst(输出): 目的操作数起始地址。；src(输入): 源操作数起始地址。；size(输入): 搬运数据大小（字节）。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为DataBlock（32字节）。取值范围：[1, 65535]。；src_gap_size(输入): 源操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst_gap_size(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束
- 当采用前n个数据搬运接口时，搬运数据大小要求32字节对齐。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
