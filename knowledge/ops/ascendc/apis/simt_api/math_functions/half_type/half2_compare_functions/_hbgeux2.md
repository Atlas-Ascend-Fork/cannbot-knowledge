---
type: API
title: __hbgeux2
description: 比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbgeux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgeux2

功能：比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbgeux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于或等于第二个数的结果。特殊值：x或y为nan→true；x、y均为nan→true；inf→true；(有限值,inf)→false；-inf→false；(正有限值,-inf)→true；inf→true；-inf→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgtux2](_hbgtux2.md)（`related`）：__hbgeux2 将严格大于扩展为大于等于，同时保持 unordered NaN 语义；等值边界决定接口选型。
- [__hgeux2](_hgeux2.md)（`related`）：__hgeux2 对每个分量分别返回 1/0 的 half2，而 focal 对两个分量做 all 归约后返回 bool；可据是否需要逐分量 mask 选择。
- [__hgeux2_mask](_hgeux2_mask.md)（`related`）：__hbgeux2 将两分量 predicate 汇总为单 bool，适合整体条件判断而非逐分量 mask。
- [__hbgeux2](../../bfloat16_type/bfloat16x2_compare_functions/_hbgeux2.md)（`same_topic`）：__hbgeux2说明比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。
- [__hbgex2](_hbgex2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hbgeux2》明确“比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
<!-- cannbot:related:end -->
