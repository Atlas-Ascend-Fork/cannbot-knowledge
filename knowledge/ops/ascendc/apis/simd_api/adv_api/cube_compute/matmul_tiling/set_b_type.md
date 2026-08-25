---
type: API
title: SetBType
description: 设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetBType

设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：B矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。
- type（输入）：B矩阵的数据格式，可设置为：CubeFormat::ND，CubeFormat::NZ。
- dataType（输入）：B矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_BFLOAT16 、DataType::DT_INT8、DataType::DT_INT4、DataType::DT_FLOAT8_E4M3FN、DataType::DT_FLOAT8_E5M2、DataType::DT_HIFLOAT8。
- isTrans（输入）：B矩阵是否转置。 参数取值：true：B矩阵转置；false：B矩阵不转置。

返回值：-1表示设置失败；0表示设置成功。
