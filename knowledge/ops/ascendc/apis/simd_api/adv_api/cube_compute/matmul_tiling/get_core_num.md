---
type: API
title: GetCoreNum
description: 获得多核切分所使用的NumBlocks参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetCoreNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCoreNum

获得多核切分所使用的NumBlocks参数。

参数：
- dim（输出）：获取计算时所需要的核数， dim = mDim * nDim
- mDim（输出）：获取计算时M方向所需要的核数
- nDim（输出）：获取计算时N方向所需要的核数
- batchCoreM（输出）：获取计算时batch M方向所需要的核数，仅BatchMatmulTiling类支持
- batchCoreN（输出）：获取计算时batch N方向所需要的核数，仅BatchMatmulTiling类支持

返回值：-1表示获取失败； 0表示获取成功。
