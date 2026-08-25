---
type: API
title: __hbgtux2
description: 比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_compare_functions/__hbgtux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgtux2

功能：比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbgtux2(bfloat16x2_t x, bfloat16x2_t y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于第二个数的结果。特殊值：nan→true；(正常值,nan)→true；nan→true；inf→true；-inf→false；inf→false；0→false。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgtux2](../../half_type/half2_compare_functions/_hbgtux2.md)（`related`）：bfloat16x2 版本保持 unordered、两个 lane 全大于才为 true 的谓词，可用于 half2 与 bfloat16x2 路径对应。
- [__hbgtx2](_hbgtx2.md)（`same_topic`）：__hbgtux2说明比较两个bfloat16x2_t类型数据的两个分量，当两个分量均满足第一个数大于第二个数时，返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hgtux2](_hgtux2.md)（`same_topic`）：hgtux2 返回逐分量 bfloat16x2 结果，而 hbgtux2 把两个分量合并为单 bool，按输出粒度选型。
<!-- cannbot:related:end -->
