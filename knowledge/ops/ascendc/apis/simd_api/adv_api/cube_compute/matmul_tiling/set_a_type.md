---
type: API
title: SetAType
description: 设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetAType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetAType

设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。

参数：
- pos（输入）：A矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。
- type（输入）：A矩阵的数据格式，可设置为：CubeFormat::ND，CubeFormat::NZ，CubeFormat::VECTOR。
- dataType（输入）：A矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_BFLOAT16、DataType::DT_INT8、DataType::DT_INT4、DataType::DT_FLOAT8_E4M3FN、DataType::DT_FLOAT8_E5M2、DataType::DT_HIFLOAT8。
- isTrans（输入）：A矩阵是否转置。 参数取值：true：A矩阵转置；false：A矩阵不转置。

返回值：-1表示设置失败；0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [SetScaleAType](set_scale_a_type.md)（`related`）：设置A矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。；如果不调用本接口，scaleA矩阵的信息将与SetAType中设置的A矩阵的信息保持一致。。SetScaleAType 的缺省描述直接继承 SetAType 的 A 矩阵描述，因此配置 scaleA 时必须理解 SetAType 的位置、格式、类型和转置合同，但两接口仍配置不同操作数。
<!-- cannbot:related:end -->
