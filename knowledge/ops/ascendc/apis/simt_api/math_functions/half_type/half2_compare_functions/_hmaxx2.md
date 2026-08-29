---
type: API
title: __hmaxx2
description: 获取两个half2类型数据各分量的最大值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hmaxx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmaxx2

功能：获取两个half2类型数据各分量的最大值。

函数原型：half2 __hmaxx2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最大值。该接口受全局饱和寄存器影响，。特殊值：(0,-0,0)→0；(-0,0,0)→0；(-0,-0,-0)→-0；(任一分量为inf,inf)→ASCRT_MAX_NORMAL_FP16；(-inf,-inf,-inf)→-ASCRT_MAX_NORMAL_FP16；(任一分量为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmaxx2_nan](_hmaxx2_nan.md)（`same_topic`）：功能：获取两个half2类型数据各分量的最大值。；功能：获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。。两接口都计算 half2 两分量最大值，目标变体额外固定任一输入为 NaN 时传播 NaN 的边界。
<!-- cannbot:related:end -->
