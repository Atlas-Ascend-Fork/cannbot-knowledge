---
type: API
title: AscFillL1
description: 将标量值赋值给目的操作数，对L1 Buffer进行初始化。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_fill_l1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscFillL1

将value的二进制值赋值给dst，对L1 Buffer的Local Memory进行初始化。

参数：dst(输出): 目的操作数（矩阵）的起始地址。；value(输入): 源操作数（标量）。；config(输入): 使用的初始化相关参数，详细说明请参考asc_fill_value_config。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束
- 若dst和value的数据类型不相同，则需要根据dst的数据类型对value的值进行转换，具体

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
