---
type: API
title: SetBiasType
description: 设置Bias的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBiasType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetBiasType

设置Bias的位置，数据格式，数据类型等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：Bias矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。
- type（输入）：Bias矩阵的数据格式，可设置为：CubeFormat::ND。
- dataType（输入）：Bias矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_INT32、DataType::DT_BFLOAT16。

返回值：-1表示设置失败； 0表示设置成功。
