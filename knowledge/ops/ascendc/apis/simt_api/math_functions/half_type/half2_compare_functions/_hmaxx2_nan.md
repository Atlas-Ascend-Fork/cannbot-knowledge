---
type: API
title: __hmaxx2_nan
description: 获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hmaxx2_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmaxx2_nan

功能：获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。

函数原型：half2 __hmaxx2_nan(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最大值。特殊值：±0→0；x或y为nan→nan；x或y为inf→inf；-inf→有限值；(有限值,-inf)→有限值；x=y=-inf→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmax_nan](../half_compare_functions/_hmax_nan.md)（`related`）：“__hmaxx2_nan”处理获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。；“__hmax_nan”明确获取两个输入数据中的最大值。任一输入为nan时结果为nan。。实质衔接：这些函数分别去掉 NaN 传播、切换 max/min、缩为标量或显式检测 NaN，直接刻画 half2 最大值的边界语义。
- [__hminx2_nan](_hminx2_nan.md)（`related`）：__hmaxx2_nan 与 focal 使用相同 half2 双分量和 NaN 传播策略，但一个取最大值、一个取最小值，适合成对实现上下界钳制。
- [__isnanx2](_isnanx2.md)（`related`）：“__hmaxx2_nan”处理获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。；“__isnanx2”明确判断half2类型数据的两个分量是否为nan。。实质衔接：这些函数分别去掉 NaN 传播、切换 max/min、缩为标量或显式检测 NaN，直接刻画 half2 最大值的边界语义。
- [__hmaxx2](_hmaxx2.md)（`same_topic`）：“__hmaxx2_nan”处理获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。；“__hmaxx2”明确获取两个half2类型数据各分量的最大值。。实质衔接：这些函数分别去掉 NaN 传播、切换 max/min、缩为标量或显式检测 NaN，直接刻画 half2 最大值的边界语义。
<!-- cannbot:related:end -->
