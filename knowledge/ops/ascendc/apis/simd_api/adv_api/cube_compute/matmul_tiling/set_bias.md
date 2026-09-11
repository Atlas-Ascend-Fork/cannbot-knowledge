---
type: API
title: SetBias
description: EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetBias.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# SetBias

## 功能说明

[EnableBias](enable_bias.md)接口功能与该接口相同，建议使用[EnableBias](enable_bias.md)。

设置Bias是否参与运算。

## 函数原型

```
int32_t SetBias(bool isBiasIn = false)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| isBiasIn | 输入 | 设置是否有Bias参与运算 |

## 返回值说明

-1表示设置失败； 0表示设置成功。

## 约束说明

无

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
tiling.SetBias(true); // 设置Bias是否参与运算
tiling.SetBufferSpace(-1, -1, -1);
optiling::TCubeTiling tilingData;
int ret = tiling.GetTiling(tilingData);
```


<!-- cannbot:related:start -->
## 相关

- [SetBias](../matmul_kernel/set_bias.md)（`related`）：在Matmul Tiling计算中，必须配置TCubeTiling结构中的isBias参数为1，即启用Bias后，才能调用本接口设置Bias矩阵。；EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。；Kernel 侧 SetBias 的合法调用以前置 Tiling 启用 isBias 为硬条件，Tiling 侧 SetBias 或推荐的 EnableBias 正是设置该参与标志的入口。
- [EnableBias](enable_bias.md)（`same_topic`）：“EnableBias接口功能与该接口相同，建议使用EnableBias。 设置Bias是否参与运算。”明确旧接口的等价替代；“设置Bias是否参与运算，设置的信息必须与Kernel侧保持一致。”补充新接口的 Kernel 一致性合同，二者是同一配置决策的迁移前后版本。
<!-- cannbot:related:end -->
