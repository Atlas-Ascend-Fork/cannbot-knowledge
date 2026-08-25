---
type: API
title: CastFloatToBfloat16
description: 将float类型标量数据转换为bfloat16_t类型标量数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/Cast_float_to_bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CastFloatToBfloat16

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

float类型标量数据转换成bfloat16_t类型标量数据。

在使用该接口之前，用户需要先了解内置数据类型和精度转换。

参数：fVal(输入): float类型标量数据。

约束：- float到bfloat16_t转换采用CAST_RINT舍入。
- 输入参数为立即数时，需要使用显式类型转换后输入，例如

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [CastFloatToHalfInt32](cast_float_to_half_int32.md)（`related`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《CastFloatToBfloat16》说明将float类型标量数据转换为bfloat16_t类型标量数据。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
