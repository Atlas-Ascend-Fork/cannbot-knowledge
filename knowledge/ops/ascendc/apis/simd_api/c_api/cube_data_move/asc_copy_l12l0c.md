---
type: API
title: AscCopyL12l0c
description: 将矩阵由L1 Buffer搬运到L0C Buffer中。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0c.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyL12l0c

将矩阵由L1 Buffer搬运到L0C Buffer中。该搬运支持的数据类型
- bfloat16_t->bfloat16_t
- half->half
- float->half
- float->bfloat16_t
- float->float
- int32_t->int32_t
- uint32_t->uint32_t

参数：dst(输出): 目的操作数的起始地址。；src(输入): 源操作数的起始地址。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为32个字节。取值范围：[1, 65535]。；src_gap(输入): 表示相邻迭代间，源操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。；dst_gap(输入): 表示相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。

约束：- 各存储单元的空间大小和对齐要求
- 如果需要执行多条asc_copy_l12l0c指令，且asc_copy_l12l0c指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_l12l0c指令的串行化，防止出现异常数据。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
