---
type: API
title: __hequx2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hequx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hequx2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：bfloat16x2_t __hequx2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否相等的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→1.0；inf→1.0；-inf→1.0；inf→0；±0→1.0；ASCRT_MAX_NORMAL_BF16→1.0；-ASCRT_MAX_NORMAL_BF16→1.0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbequx2](_hbequx2.md)（`related`）：“__hbequx2”定义：比较两个bfloat16x2_t类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。；“__hequx2”定义：比较两个bfloat16x2_t类型数据的两个分量，如果分量相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。。实质衔接：half2 版保持 unordered 双分量全等布尔语义；__hequx2 改为逐分量数值结果，__hbeqx2 改为 NaN 不视为相等，选择时必须区分。
- [__hequx2](../../half_type/half2_compare_functions/_hequx2.md)（`same_topic`）：__hequx2 与《__hequx2》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：__hequx2 与《__hequx2_mask》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__heqx2](_heqx2.md)（`same_topic`）：__hequx2 与《__heqx2》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__heqx2_mask](_heqx2_mask.md)（`same_topic`）：__hequx2 与《__heqx2_mask》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hequx2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hneux2](_hneux2.md)（`same_topic`）：__hequx2 与《__hneux2》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：__hequx2 与《__hneux2_mask》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
<!-- cannbot:related:end -->
