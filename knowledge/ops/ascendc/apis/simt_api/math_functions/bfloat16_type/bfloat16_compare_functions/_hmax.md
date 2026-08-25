---
type: API
title: __hmax
description: 获取两个输入数据中的最大值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hmax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmax

获取两个输入数据中的最大值。
函数原型：bfloat16_t __hmax(bfloat16_t x, bfloat16_t y)
返回值：两个输入数据中的最大值。本接口不受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hmax_nan](_hmax_nan.md)（`same_topic`）：__hmax 与《__hmax_nan》的实质衔接是：hmax_nan 与 hmax 的差异在 NaN 选择，hmin/min_nan 提供同一极值契约的相反操作和特殊值对照。
- [__hmin](_hmin.md)（`same_topic`）：__hmax 与《__hmin》的实质衔接是：hmax_nan 与 hmax 的差异在 NaN 选择，hmin/min_nan 提供同一极值契约的相反操作和特殊值对照。
- [__hmin_nan](_hmin_nan.md)（`same_topic`）：__hmax 与《__hmin_nan》的实质衔接是：hmax_nan 与 hmax 的差异在 NaN 选择，hmin/min_nan 提供同一极值契约的相反操作和特殊值对照。
<!-- cannbot:related:end -->
