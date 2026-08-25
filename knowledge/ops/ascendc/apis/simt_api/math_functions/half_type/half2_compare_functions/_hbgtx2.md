---
type: API
title: __hbgtx2
description: 比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于第二个数时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbgtx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgtx2

功能：比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于第二个数时返回true。

函数原型：bool __hbgtx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于第二个数的结果。特殊值：各分量x>y→true；任一分量x=y→false；任一分量x<y→false；任一分量为nan→false；±0→false；inf→true；(有限值,inf)→false；(有限值,-inf)→true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hgtx2](_hgtx2.md)（`related`）：__hgtx2 按分量返回 half2 的 1/0，而 __hbgtx2 将两个分量合并为单个 bool；后续需要逐 lane 掩码还是整体条件决定选择。
- [__hbgtux2](_hbgtux2.md)（`same_topic`）：两接口都要求两个 half2 lane 均满足 x>y 才返回 bool，差异是 NaN 时 unordered 版本视该 lane 为 true、ordered 版本为 false。
- [__hbgtx2](../../bfloat16_type/bfloat16x2_compare_functions/_hbgtx2.md)（`same_topic`）：__hbgtx2说明比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于第二个数时返回true。
<!-- cannbot:related:end -->
