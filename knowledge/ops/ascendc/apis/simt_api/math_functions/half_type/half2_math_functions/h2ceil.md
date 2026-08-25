---
type: API
title: H2Ceil
description: 获取大于或等于输入数据各元素的最小整数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2ceil.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# H2Ceil

功能：获取大于或等于输入数据各元素的最小整数值。

函数原型：half2 h2ceil(half2 x)

参数：x（输入）源操作数。

返回值：大于或等于输入数据各元素的最小整数值。本接口受全局饱和寄存器影响，。特殊值：±0→0；ASCRT_MIN_DENORM_FP16→1；nan→0；inf→ASCRT_MAX_NORMAL_FP16；-inf→-ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Floor](h2floor.md)（`related`）：“H2Ceil”定义：获取大于或等于输入数据各元素的最小整数值。；“H2Floor”定义：获取小于或等于输入数据各元素的最大整数值。。实质衔接：bfloat16x2 版保持双分量向上取整；H2Floor 是同 half2 输入的向下取整边界，二者用于明确舍入方向。
- [Hceil](../half_math_functions/hceil.md)（`related`）：H2ceil 是 Hceil 的 two-lane half2 对应形式，连接单值与 packed 两元素处理。
- [H2Ceil](../../bfloat16_type/bfloat16x2_math_functions/h2ceil.md)（`same_topic`）：“H2Ceil”定义：获取大于或等于输入数据各元素的最小整数值。；“H2Ceil”定义：获取大于或等于输入数据各元素的最小整数值。。实质衔接：bfloat16x2 版保持双分量向上取整；H2Floor 是同 half2 输入的向下取整边界，二者用于明确舍入方向。
- [H2Rint](h2rint.md)（`same_topic`）：H2Rint 取最近偶数，H2Ceil 向正无穷取整；两者处理同一 half2 输入并受同一饱和寄存器影响，是精确的舍入语义选择。
<!-- cannbot:related:end -->
