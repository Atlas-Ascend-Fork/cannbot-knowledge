---
type: API
title: __hequx2
description: 比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hequx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hequx2

功能：比较两个half2类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：half2 __hequx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应结果为1，不满足时对应结果为0。特殊值：±0→1；x[i]=nan或y[i]=nan→1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__isnanx2](_isnanx2.md)（`related`）：__hequx2 与《__isnanx2》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
- [__hequx2](../../bfloat16_type/bfloat16x2_compare_functions/_hequx2.md)（`same_topic`）：__hequx2 与《__hequx2》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：__hequx2 与《__hequx2_mask》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
- [__heqx2](_heqx2.md)（`same_topic`）：__hequx2 与《__heqx2》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：__hequx2 与《__heqx2_mask》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
<!-- cannbot:related:end -->
