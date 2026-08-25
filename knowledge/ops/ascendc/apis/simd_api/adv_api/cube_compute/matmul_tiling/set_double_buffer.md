---
type: API
title: SetDoubleBuffer
description: 设置A/B/C/Bias是否开启double buffer功能，以及是否需要做ND2NZ或者NZ2ND的转换，主要用于Tiling函数内部调优。
  该接口为预留接口，当前版本暂不支持。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetDoubleBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetDoubleBuffer

设置A/B/C/Bias是否开启double buffer功能，以及是否需要做ND2NZ或者NZ2ND的转换，主要用于Tiling函数内部调优。 该接口为预留接口，当前版本暂不支持。

参数：
- a：输入设置A矩阵是否开启double buffer。
- b：输入设置B矩阵是否开启double buffer。
- c：输入设置C矩阵是否开启double buffer。
- bias（输入）：设置Bias矩阵是否开启double buffer。
- transND2NZ（输入）：设置是否需要ND2NZ。

返回值：-1表示设置失败； 0表示设置成功。
