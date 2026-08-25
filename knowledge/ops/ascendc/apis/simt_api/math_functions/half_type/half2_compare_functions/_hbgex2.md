---
type: API
title: __hbgex2
description: 比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbgex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbgex2

功能：比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。

函数原型：bool __hbgex2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入各分量是否均满足第一个数大于或等于第二个数的结果。特殊值：任一分量为nan→false；((±0, ±0),(±0, ±0))→true；((inf, inf),(正常值, 正常值))→true；((-inf, -inf),(正常值, 正常值))→false；((正常值, 正常值),(inf, inf))→false；((正常值, 正常值),(-inf, -inf))→true；((inf, inf),(inf, inf))→true；((inf, inf),(-inf, -inf))→true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbgeux2](_hbgeux2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hbgeux2》明确“比较两个half2类型数据的两个分量，当两个分量均满足第一个数大于或等于第二个数时返回true。若任一输入的分量为nan，该分量的比较结果为true。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
- [__hbgex2](../../bfloat16_type/bfloat16x2_compare_functions/_hbgex2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hbgex2》明确“比较两个bfloat16x2_t类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时，返回true。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
- [__hblex2](_hblex2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hblex2》明确“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数小于或等于第二个数时返回true。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
- [__hgex2](_hgex2.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hgex2》明确“比较两个half2类型数据的两个分量，如果分量满足第一个数大于或等于第二个数，则对应比较结果为1.0，否则为0.0。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：《__hbgex2》处理“比较两个half2类型数据的两个分量，仅当两个分量均满足第一个数大于或等于第二个数时返回true。”。《__hgex2_mask》明确“比较两个half2类型数据的两个分量，结果以unsigned int形式返回，低16位为第一个分量的掩码结果，高16位为第二个分量的掩码结果。如果分量满足第一个数大于或等于第二个数，则对应16位掩码为0xFFFF，否则为0x0。”，可直接用于核对bfloat16x2 大于等于谓词的有序/无序、mask 与相反比较合同。
<!-- cannbot:related:end -->
