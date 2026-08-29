---
type: API
title: Isnan
description: 判断浮点数是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/isnan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Isnan

功能：判断浮点数是否为nan。

函数原型：bool isnan(float x)

参数：x（输入）源操作数。

返回值：false：输入非nan；true：输入为nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Dilation2D 950 Direct Invoke 算子知识](../../../../operators/direct/nn/pooling/dilation_2d_950.md)（`related`）：isnan API 的功能是“判断浮点数是否为nan。”；Dilation2D 950 的 SIMT 规则明确“if isnan(val): return NaN”。算子实现直接调用该判定保持 NaN 传播。
<!-- cannbot:related:end -->
