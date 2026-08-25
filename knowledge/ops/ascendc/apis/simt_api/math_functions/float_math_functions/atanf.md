---
type: API
title: Atanf
description: 获取输入数据的反正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/atanf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Atanf

功能：获取输入数据的反正切值。

函数原型：float atanf(float x)

参数：x（输入）源操作数。

返回值：输入数据的反正切值。特殊值：inf→π/2；-inf→-π/2；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Atan接口](../../../simd_api/adv_api/math_compute/atan_interface/atan_interface.md)（`related`）：《Atan接口》处理“提供Atan反正切计算接口及其Tiling临时空间大小查询接口，包含Atan、GetAtanMaxMinTmpSize等。”。《Atanf》明确提供“获取输入数据的反正切值。”，其参数、调用或验证步骤直接接入Atan Kernel 调用、临时空间查询和 SIMT 对应实现。
<!-- cannbot:related:end -->
