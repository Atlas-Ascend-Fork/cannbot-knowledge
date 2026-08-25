---
type: API
title: Asinf
description: 获取输入数据的反正弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/asinf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Asinf

功能：获取输入数据的反正弦值。  arcsin(x)为反正弦函数的计算。

函数原型：float asinf(float x)

参数：x（输入）源操作数。

返回值：输入数据的反正弦值。特殊值：inf→nan；-inf→nan；nan→nan；0→0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Asin](../../../simd_api/adv_api/math_compute/asin_interface/asin.md)（`related`）：Asinf 是 SIMT 标量 float 入口，Asin 是 LocalTensor 高阶向量入口并要求 sharedTmpBuffer；二者都实现反正弦且共享 [-1,1] 有效值域。
<!-- cannbot:related:end -->
