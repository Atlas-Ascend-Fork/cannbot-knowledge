---
type: API
title: SetShape
description: 设置Matmul计算的形状m、n、k，可为完整矩阵或局部矩阵，支持传入-1按原始形状计算
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetShape

设置Matmul计算的形状m、n、k，该形状可以为原始完整矩阵或其局部矩阵，单位为元素。该形状的矩阵乘可以由单核或多核计算完成。 使用本接口时，有两种参数传入方式： - 传入Matmul计算的形状m、n、k，调用GetTiling接口时，按照m、n、k计算并返回Tiling参数。

参数：
- m：输入设置Matmul计算的M方向大小，单位为元素。
- n：输入设置Matmul计算的N方向大小，单位为元素。
- k：输入设置Matmul计算的K方向大小，单位为元素。

返回值：-1表示设置失败；0表示设置成功。
