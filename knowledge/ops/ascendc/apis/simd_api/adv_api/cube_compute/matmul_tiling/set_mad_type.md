---
type: API
title: SetMadType
description: 设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetMadType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# SetMadType

设置是否开启HF32模式。当前版本暂不支持。 对于Ascend 950PR/Ascend 950DT，本接口可用于设置是否开启HF32模式（当前版本暂不支持）、设置是否开启MxMatmul场景。在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景，从而保证该场景下正确计算并返回Tiling参数。

参数：
- madType（输入）：设置Matmul模式。MatrixMadType类型，定义如下方代码所示，其中参数的含义为： MatrixMadType::NORMAL：普通模式，即非HF32模式、非MxMatmul场景。。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [MxMatmul场景](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/mx_matmul_scenario.md)（`explains`）：MxMatmul（全称Microscaling Matmul）为带有量化系数的矩阵乘法；在MxMatmul场景，必须调用该接口并配置为开启MxMatmul场景。场景卡定义带 scaleA/scaleB 的 MxMatmul 语义，SetMadType 卡给出该场景生成正确 Tiling 的强制开关；实现 MxMatmul 时必须把场景识别落实到该 Host Tiling 调用。
<!-- cannbot:related:end -->
