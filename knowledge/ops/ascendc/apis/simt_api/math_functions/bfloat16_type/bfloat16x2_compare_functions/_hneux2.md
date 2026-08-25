---
type: API
title: __hneux2
description: 比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hneux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hneux2

功能：比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0。

函数原型：bfloat16x2_t __hneux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否不相等的结果：满足时对应结果为1.0，不满足时对应结果为0.0。特殊值：任一分量含nan→1.0；±0→0；inf→0；-inf→0；inf→1.0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbneux2](_hbneux2.md)（`related`）：两者都采用 unordered not-equal 的 NaN 规则，但 focal 聚合两个 lane 为 bool，目标逐 lane 返回 1.0/0.0，覆盖分支判定与向量结果两种需求。
- [__hequx2](_hequx2.md)（`same_topic`）：__hequx2 与《__hneux2》的实质衔接是：hequx2 是 unordered equality（NaN 也为真）；mask、half2、ordered equality 与 unordered not-equal 入口直接界定返回形态和 NaN 分支。
- [__hleux2](_hleux2.md)（`same_topic`）：__hleux2 与《__hneux2》的实质衔接是：__hleux2 返回 unordered ≤ 的双 lane 数值结果；mask 版本、ordered 版本、反向 ≥/> 与 isnan 共同限定 NaN 时 true 的语义及返回形态。
- [__hneux2](../../half_type/half2_compare_functions/_hneux2.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hneux2正文界定“比较两个bfloat16x2_t类型数据的两个分量，如果分量不相等，则对应比较结果为1.0，否则为0.0。若任一输入的分量为nan，该分量的比较结果为1.0”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hnex2](_hnex2.md)（`same_topic`）：__hneux2 与 __hnex2 都逐分量返回 bfloat16x2 不等结果，差异是 NaN 时 unordered 版本为 1、ordered 版本为 0。
<!-- cannbot:related:end -->
