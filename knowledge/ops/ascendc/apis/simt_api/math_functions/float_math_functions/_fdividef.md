---
type: API
title: __fdividef
description: 获取两个输入数据相除的结果。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/__fdividef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __fdividef

功能：获取两个输入数据相除的结果。

函数原型：float __fdividef(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：两个输入数据相除的结果。特殊值：0→+inf；0→-inf；0→nan；nan→nan。

约束：针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。需包含头文件 simt_api/device_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [CeilDivision](../../../simd_api/basic_api/scalar_compute/ceil_division.md)（`related`）：CeilDivision 与《__fdividef》的实质衔接是：CeilDivision 与 CeilDiv 执行整数向上整除，快速除法与 SIMT divide 接口提供实现和舍入边界，标量计算页说明 device 使用域。
- [Fdividef](fdividef.md)（`same_topic`）：__fdividef 与《Fdividef》的实质衔接是：__fdividef 与 Fdividef 是 float 快速除法入口，half/half2 对应接口用于在降精度时保持相除语义和 lane 形态。
- [__hdiv](../bfloat16_type/bfloat16_arithmetic_functions/_hdiv.md)（`same_topic`）：__fdividef 与《__hdiv》的实质衔接是：__fdividef 与 Fdividef 是 float 快速除法入口，half/half2 对应接口用于在降精度时保持相除语义和 lane 形态。
- [__hdivx2](../bfloat16_type/bfloat16x2_arithmetic_functions/_hdivx2.md)（`same_topic`）：__fdividef 与《__hdivx2》的实质衔接是：__fdividef 与 Fdividef 是 float 快速除法入口，half/half2 对应接口用于在降精度时保持相除语义和 lane 形态。
<!-- cannbot:related:end -->
