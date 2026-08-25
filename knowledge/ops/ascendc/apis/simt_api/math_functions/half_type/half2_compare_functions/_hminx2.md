---
type: API
title: __hminx2
description: 获取两个half2类型数据各分量的最小值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hminx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hminx2

功能：获取两个half2类型数据各分量的最小值。

函数原型：half2 __hminx2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最小值。特殊值：(0,-0,-0)→-0；(-0,0,-0)→-0；(-0,-0,-0)→-0；(0,0,0)→0；(nan,nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmaxx2](_hmaxx2.md)（`related`）：__hmaxx2 与 __hminx2 共享 half2 双分量输入、饱和寄存器和特殊值边界，但选择相反最值，适合成对实现或测试 clamp。
- [half2类型比较函数](half2_compare_functions.md)（`related`）：half2 比较函数总览把 __hminx2、__hmaxx2、NaN 变体及布尔/掩码比较放在同一接口族中，便于按返回语义选型。
- [__hminx2_nan](_hminx2_nan.md)（`same_topic`）：__hminx2 与 focal 都逐分量返回 half2 最小值；唯一关键决策是普通版本遇到 NaN 返回 0，而 _nan 版本传播 NaN。
<!-- cannbot:related:end -->
