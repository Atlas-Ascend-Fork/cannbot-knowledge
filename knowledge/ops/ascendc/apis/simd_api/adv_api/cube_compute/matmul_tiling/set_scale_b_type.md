---
type: API
title: SetScaleBType
description: MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetScaleBType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetScaleBType

MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。

参数：
- scalePos（输入）：scaleB矩阵的内存逻辑位置。
- scaleType（输入）：scaleB矩阵的物理排布格式。
- isScaleTrans（输入）：scaleB矩阵是否转置。参数支持的取值如下：true：默认值，scaleB矩阵转置；/false：scaleB矩阵不转置。

返回值：-1表示设置失败； 0表示设置成功。
