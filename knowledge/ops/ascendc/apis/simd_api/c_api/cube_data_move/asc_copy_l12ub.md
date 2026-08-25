---
type: API
title: AscCopyL12ub
description: 将数据从L1 Buffer搬运到Unified Buffer中。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12ub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscCopyL12ub

将数据从L1 Buffer搬运到Unified Buffer中。

参数：dst_addr(输出): 目的操作数起始地址。；src_addr(输入): 源操作数起始地址。；sub_blockid(输入): 使用的子块ID。；n_burst(输入): 待搬运的连续传输数据块个数。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为DataBlock（32字节）。；src_gap(输入): 源操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。；dst_gap(输入): 目的操作数相邻连续数据块的间隔（前面一个数据块的尾与后面一个数据块的头的间隔）。 单位为DataBlock（32字节）。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束
- 由于此接口实现了Cube核与Vector核间的数据搬运，所以如果核函数调用了该接口，则不能使用__cube__或__vector__的执行空间修饰符，否则会导致执行失败。

仅 Ascend 950PR/Ascend 950DT 支持。
