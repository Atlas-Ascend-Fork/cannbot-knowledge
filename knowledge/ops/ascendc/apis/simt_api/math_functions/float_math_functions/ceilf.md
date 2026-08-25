---
type: API
title: Ceilf
description: 获取大于或等于输入数据的最小整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/ceilf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Ceilf

功能：获取大于或等于输入数据的最小整数值。

函数原型：float ceilf(float x)

参数：x（输入）源操作数。

返回值：大于或等于输入数据的最小整数值。特殊值：nan→nan；inf→inf；-inf→-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [AscCeil](../../../simd_api/c_api/reg/data_type_convert/asc_ceil.md)（`same_topic`）：AscCeil 将向正无穷取整映射到带 mask 的 Reg C API，结果仍保持浮点类型，与标量 ceilf 语义一致。
- [Ceil接口](../../../simd_api/adv_api/math_compute/ceil_interface/ceil_interface.md)（`same_topic`）：Ceilf 是 float 标量 SIMT 入口，Ceil 高阶接口对 LocalTensor 逐元素向正无穷取整并定义临时空间合同。
<!-- cannbot:related:end -->
