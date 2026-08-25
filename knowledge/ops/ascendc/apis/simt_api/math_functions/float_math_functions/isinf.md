---
type: API
title: Isinf
description: 判断浮点数是否为无穷。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/isinf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Isinf

功能：判断浮点数是否为无穷。

函数原型：bool isinf(float x)

参数：x（输入）源操作数。

返回值：false：输入不是无穷；true：输入为inf、-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [IsInf](../../../simd_api/adv_api/math_compute/is_inf_interface/is_inf.md)（`related`）：Isinf 与《IsInf》的实质衔接是：SIMT Isinf 与张量 IsInf、half/bfloat16 __hisinf 执行同一无穷判定，可按数据载体切换并核对返回语义。
- [IsInf接口](../../../simd_api/adv_api/math_compute/is_inf_interface/is_inf_interface.md)（`related`）：《Isinf》明确“判断浮点数是否为无穷。”；它与《IsInf接口》的“按元素判断浮点数是否为±INF，并提供临时空间大小获取接口。”在实际调用参数、数据流或结果校验上直接衔接。
- [__hisinf](../bfloat16_type/bfloat16_compare_functions/_hisinf.md)（`related`）：Isinf 与《__hisinf》的实质衔接是：SIMT Isinf 与张量 IsInf、half/bfloat16 __hisinf 执行同一无穷判定，可按数据载体切换并核对返回语义。
- [__hisinf](../half_type/half_compare_functions/_hisinf.md)（`related`）：Isinf 与《__hisinf》的实质衔接是：SIMT Isinf 与张量 IsInf、half/bfloat16 __hisinf 执行同一无穷判定，可按数据载体切换并核对返回语义。
<!-- cannbot:related:end -->
