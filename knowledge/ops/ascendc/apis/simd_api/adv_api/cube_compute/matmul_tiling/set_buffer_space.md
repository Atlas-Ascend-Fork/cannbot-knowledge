---
type: API
title: SetBufferSpace
description: 设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBufferSpace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetBufferSpace

设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer/BiasTable Buffer空间大小，单位为字节。

参数：
- l1Size（输入）：设置Matmul计算时，能够使用的L1 Buffer大小，单位为字节。默认值-1，表示使用AI处理器L1 Buffer大小。
- l0CSize（输入）：设置Matmul计算时，能够使用的L0C Buffer大小，单位为字节。默认值-1，表示使用AI处理器L0C Buffer大小。
- ubSize（输入）：设置Matmul计算时，能够使用的UB Buffer大小，单位为字节。默认值-1，表示使用AI处理器UB Buffer大小。
- btSize（输入）：设置Matmul计算时，能够使用的BiasTable Buffer大小，单位为字节。默认值-1，表示使用AI处理器BiasTable Buffer大小。

返回值：-1表示设置失败； 0表示设置成功。
