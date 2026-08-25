---
type: API
title: __hbgtux2
description: 比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbgtux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgtux2

功能：比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbgtux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于第二个数的结果。特殊值：((nan, nan),(nan, nan))→true；((nan, 正常值),(正常值, nan))→true；((inf, inf),(有限值, 有限值))→true；((-inf, -inf),(有限正数, 有限正数))→false；((有限正数, 有限正数),(inf, inf))→true；((inf, inf),(-inf, -inf))→true；((±0, ±0),(±0, ±0))→false；((有限值, 有限值),(有限值, 有限值))→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgeux2](_hbgeux2.md)（`related`）：__hbgeux2 将严格大于扩展为大于等于，同时保持 unordered NaN 语义；等值边界决定接口选型。
- [__hbgtux2](../../bfloat16_type/bfloat16x2_compare_functions/_hbgtux2.md)（`related`）：bfloat16x2 版本保持 unordered、两个 lane 全大于才为 true 的谓词，可用于 half2 与 bfloat16x2 路径对应。
- [__hgtux2](_hgtux2.md)（`related`）：Hbgtux2 将两个 lane 的 unordered greater-than 再做全真归约返回 bool，适合组级分支而非逐 lane 结果。
- [__hgtux2_mask](_hgtux2_mask.md)（`related`）：__hgtux2_mask 与《__hbgtux2》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hbgtx2](_hbgtx2.md)（`same_topic`）：两接口都要求两个 half2 lane 均满足 x>y 才返回 bool，差异是 NaN 时 unordered 版本视该 lane 为 true、ordered 版本为 false。
<!-- cannbot:related:end -->
