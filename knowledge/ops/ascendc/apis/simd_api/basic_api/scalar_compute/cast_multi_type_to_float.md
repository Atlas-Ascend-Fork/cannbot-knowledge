---
type: API
title: CastMultiTypeToFloat
description: 将bfloat16_t、fp8、fp4等多种类型标量数据转换为float类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/Cast_multi_type_to_float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CastMultiTypeToFloat

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

该接口将输入数据转换为float类型。

在使用该接口之前，用户需要先了解内置数据类型和精度转换。

参数：T: 操作数数据类型。；U: 返回值数据类型。；bVal(输入): 待转换的标量数据。

约束：输入参数为立即数时，需要使用显式类型转换，例如

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。
