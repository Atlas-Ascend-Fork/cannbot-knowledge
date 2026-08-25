---
type: API
title: __hminx2_nan
description: 获取两个half2类型数据各分量的最小值。任一分量为nan时对应结果为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hminx2_nan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hminx2_nan

功能：获取两个half2类型数据各分量的最小值。任一分量为nan时对应结果为nan。

函数原型：half2 __hminx2_nan(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最小值。特殊值：±0→0；0→-0；-0→-0；-0→-0；nan→nan；(任意值,nan)→nan；-inf→-inf；(非nan,-inf)→-inf。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmaxx2_nan](_hmaxx2_nan.md)（`related`）：__hmaxx2_nan 与 focal 使用相同 half2 双分量和 NaN 传播策略，但一个取最大值、一个取最小值，适合成对实现上下界钳制。
- [__hminx2_nan](../../bfloat16_type/bfloat16x2_compare_functions/_hminx2_nan.md)（`related`）：bfloat16x2 的同名 __hminx2_nan 保留逐分量最小值和 NaN 传播语义，但输入输出类型与头文件不同，可防止按名称误用 half2 重载。
- [__hminx2](_hminx2.md)（`same_topic`）：__hminx2 与 focal 都逐分量返回 half2 最小值；唯一关键决策是普通版本遇到 NaN 返回 0，而 _nan 版本传播 NaN。
- [half2类型比较函数](half2_compare_functions.md)（`same_topic`）：half2 比较函数入口把 __hminx2_nan 与普通 min、max、NaN 判断和有序/无序比较组织在同一选择表中，可定位 focal 的 NaN 传播版本。
<!-- cannbot:related:end -->
