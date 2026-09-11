---
type: API
title: SetBType
description: 设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/matmul/matmul_tiling_base.h
---

# SetBType

## 功能说明

设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。

## 函数原型

```
int32_t SetBType(TPosition pos, CubeFormat type, DataType dataType, bool isTrans = false)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| pos | 输入 | B矩阵所在的buffer位置，可设置为：TPosition::GM, TPosition::VECOUT, TPosition::TSCM。 |
| type | 输入 | B矩阵的数据格式，可设置为：CubeFormat::ND，CubeFormat::NZ。 |
| dataType | 输入 | B矩阵的数据类型，可设置为：DataType::DT_FLOAT、DataType::DT_FLOAT16、DataType::DT_BFLOAT16 、DataType::DT_INT8、DataType::DT_INT4、DataType::DT_FLOAT8_E4M3FN、DataType::DT_FLOAT8_E5M2、DataType::DT_HIFLOAT8。 |
| isTrans<a name="p47369411111"></a> | 输入 | B矩阵是否转置。<br><br>参数取值：<br>true：B矩阵转置；false：B矩阵不转置。 |

## 返回值说明

-1表示设置失败；0表示设置成功。

## 约束说明

无



## 调用示例

```
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
matmul_tiling::MatmulApiTiling tiling(ascendcPlatform);
// 设置B矩阵，buffer位置为GM，数据格式为ND，数据类型为bfloat16，默认不转置
tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);
```


<!-- cannbot:related:start -->
## 相关

- [SetScaleBType](set_scale_b_type.md)（`related`）：“MxMatmul场景，设置scaleB矩阵的位置、数据格式、是否转置等信息，这些信息需要和Kernel侧的设置保持一致。如果不调用本接口，scaleB矩阵的信息将与SetBType中设置的B矩阵的信息保持一致。”明确 scaleB 的缺省继承，而“设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。”定义继承来源；联合阅读可确定未显式配置 scaleB 时的真实位置与排布。
- [SetTensorB](../matmul_kernel/set_tensor_b.md)（`related`）：- isTransposeB（输入）：B矩阵是否需要转置。 注意：若B矩阵MatmulType的ISTRANS参数设置为true，该参数可以为true也可以为false，即运行时可以转置和非转置交替使用； 若B矩阵MatmulType的ISTRANS参数设置为false，该参数只能设置为false，若强行设置为true，精度会有异常；对于非half、非bfloat16_t输入类型的场景，为了确保Tiling侧与Kernel侧L1 Buffer空间计算大小保持一致及结果精度正确，该参数取值必须与Kernel侧定义B矩阵MatmulType的ISTRANS参数以及Tiling侧SetBType()接口的isTrans参数保持一致，即上述三个参数必须同时设置为true或同时设置为false。；设置B矩阵的位置，数据格式，数据类型，是否转置等信息，这些信息需要和kernel侧的设置保持一致。；Kernel 侧 SetTensorB 明确要求转置设置与 Tiling 侧 SetBType 一致，SetBType 正是声明 B 矩阵布局和转置的 Host 侧契约。
<!-- cannbot:related:end -->
