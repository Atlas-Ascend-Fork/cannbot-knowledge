---
type: API
title: __hgex2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hgex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgex2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。

函数原型：bfloat16x2_t __hgex2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否满足第一个数大于或等于第二个数的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→0；inf→1.0；-inf→0；±0→1.0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hleux2](_hleux2.md)（`related`）：__hgex2 与《__hleux2》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hbgex2](_hbgex2.md)（`same_topic`）：__hbgex2：__hbgex2返回“两分量均>=”的 bool；half2同名卡核对类型变体，__hbgeux2核对 unordered NaN语义，__hgex2则对照逐分量向量结果而非 bool 汇总。 目标卡《__hgex2》补充：比较两个bfloat16x2_t类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hgex2 与《__hgeux2》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hgeux2_mask](_hgeux2_mask.md)（`same_topic`）：__hgex2 与《__hgeux2_mask》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hgex2](../../half_type/half2_compare_functions/_hgex2.md)（`same_topic`）：__hgex2 与《__hgex2》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hgex2 与《__hgex2_mask》的实质衔接是：__hgex2 返回 bfloat16x2 两个 lane 的 ordered ≥ 结果；mask 版本、half 对应入口及 unordered ≥/≤ 用于区分返回形态和 NaN 行为。
- [__hgtux2_mask](_hgtux2_mask.md)（`same_topic`）：__hgtux2_mask 与《__hgex2》的实质衔接是：__hgtux2_mask 返回 unordered 大于的双 lane 16-bit mask；ordered/unordered、反向比较、值返回和 isnan 入口共同限定 NaN 与返回布局。
<!-- cannbot:related:end -->
