---
type: API
title: AscSetL13dSize
description: 设置3D搬运接口在L1 Buffer的边界值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l13d_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscSetL13dSize

设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口在L1 Buffer的边界值。

参数：value(输入): 用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口在L1 Buffer的边界值，单位是字节。非0场景的边界值不能小于。

约束：- 需配合asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口使用。
- 如果使用asc_set_l13d_size接口设置了边界值，asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的L1 Buffer初始地址要在设置的边界内（value）。
- 如果asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的源操作数在L1 Buffer上的地址超出设置的边界值（value），则会从L1 Buffer起始地址开始读取数据。
- 操作数地址对齐约束

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
