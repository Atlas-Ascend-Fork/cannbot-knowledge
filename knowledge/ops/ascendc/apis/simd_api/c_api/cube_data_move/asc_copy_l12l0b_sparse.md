---
type: API
title: AscCopyL12l0bSparse
description: 将L1 Buffer中的稠密权重矩阵搬运到L0B Buffer，同时读取索引矩阵用于稠密矩阵稀疏化。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0b_sparse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyL12l0bSparse

用于搬运存放在L1 Buffer里的512B大小的稠密权重矩阵到L0B Buffer里，同时读取128B大小的索引矩阵用于稠密矩阵的稀疏化。

索引矩阵在一个int8_t的地址中的排布是逆序排布的，例如：索引矩阵1 2 0 1 0 2 1 0，在地址中的排布为1 0 2 1 0 1 2 0，其中1 0 2 1（对应索引矩阵前四位1 2 0 1）拼成一个int8_t数据，0 1 2 0（对应索引矩阵后四位0 2 1 0）拼成一个int8_t数据。

参数：dst(输出): 目的操作数在L0B Buffer的起始地址。；src(输入): 源操作数在L1 Buffer的起始地址。；index(输入): 索引矩阵在L1 Buffer的起始地址。；start_index(输入): 分形矩阵ID，说明搬运起始位置为源操作数中第几个分形（0为源操作数中第1个分形矩阵）。取值范围：[0, 65535]。单位：512B。；repeat(输入): 迭代次数，每个迭代可以处理512B数据。取值范围：[1, 255]。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束
- repeat为0表示不执行。
- start_index不能小于0。
- 不支持转置功能。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
