---
type: API
title: __hleux2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hleux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hleux2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：bfloat16x2_t __hleux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数小于或等于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→1.0；x≤y→1.0；x＞y→0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgex2](_hgex2.md)（`related`）：__hgex2 与《__hleux2》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hbgeux2](_hbgeux2.md)（`same_topic`）：__hleux2 与《__hbgeux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hbleux2](_hbleux2.md)（`same_topic`）：__hbleux2：__hbleux2返回两分量unordered <= 的bool；half2同名卡核对类型，__hblex2对照ordered NaN语义，__hleux2及mask版对照逐分量结果。 目标卡《__hleux2》补充：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数小于或等于第二个数，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
- [__hequx2](_hequx2.md)（`same_topic`）：__hleux2 与《__hequx2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hequx2_mask](_hequx2_mask.md)（`same_topic`）：__hleux2 与《__hequx2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hleux2 与《__hgeux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：__hleux2 与《__hgeux2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hleux2 与《__hgex2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hgtux2](_hgtux2.md)（`same_topic`）：__hleux2 与《__hgtux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hleux2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
- [__hleux2](../../half_type/half2_compare_functions/_hleux2.md)（`same_topic`）：__hleux2 与《__hleux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hleux2_mask](_hleux2_mask.md)（`same_topic`）：__hleux2 与《__hleux2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hlex2](_hlex2.md)（`same_topic`）：__hleux2 与《__hlex2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hneux2](_hneux2.md)（`same_topic`）：__hleux2 与《__hneux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hneux2_mask](_hneux2_mask.md)（`same_topic`）：__hleux2 与《__hneux2_mask》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__isnanx2](_isnanx2.md)（`same_topic`）：__hleux2 与《__isnanx2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
<!-- cannbot:related:end -->
