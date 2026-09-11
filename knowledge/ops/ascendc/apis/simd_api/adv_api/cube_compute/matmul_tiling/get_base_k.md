---
type: API
title: GetBaseK
description: 获取Tiling计算得到的baseK值。baseK参数的说明请参考表1。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/GetBaseK.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# GetBaseK

## 功能说明

获取Tiling计算得到的baseK值。baseK参数的说明请参考[表1](t_cube_tiling_struct.md#tcubetiling-struct)。

## 函数原型

```
int32_t GetBaseK() const
```

## 参数说明

无

## 返回值说明

返回值为Tiling计算得到的baseK值。

## 约束说明

使用创建的Tiling对象调用该接口，且需在完成Tiling计算（[GetTiling](get_tiling.md)）后调用。

## 调用示例

```
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
matmul_tiling::MatmulApiTiling tiling(ascendcPlatform);
tiling.SetAType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);
tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);
tiling.SetCType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);
tiling.SetBiasType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);
tiling.SetShape(1024, 1024, 1024);
tiling.SetOrgShape(1024, 1024, 1024);
tiling.SetBias(true);
tiling.SetBufferSpace(-1, -1, -1);

optiling::TCubeTiling tilingData;
int ret = tiling.GetTiling(tilingData);
int baseK = tiling.GetBaseK(); // 获取Tiling计算得到的baseK
```



<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：“约束：必须使用已创建的 MatmulApiTiling 对象调用，且需在完成 GetTiling 计算后再获取 baseK，否则返回值无效。”；“返回值：如果返回值不为-1，则代表Tiling计算成功，用户可以使用该Tiling结构的值。如果返回值为-1，则代表Tiling计算失败，该Tiling结果无法使用。”。GetTiling 成功是 GetBaseK 返回有效 baseK 的明确前置条件，调用方需先检查失败码再读取基本块。
<!-- cannbot:related:end -->
