---
type: API
title: __hbneux2
description: 比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbneux2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbneux2

功能：比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。

函数原型：bool __hbneux2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均不相等的结果。特殊值：nan→true；±0→false；±inf→false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbneux2](../../bfloat16_type/bfloat16x2_compare_functions/_hbneux2.md)（`related`）：两接口有相同 unordered 双 lane != 语义，分别作用于 half2 和 bfloat16x2。
- [__hbequx2](_hbequx2.md)（`same_topic`）：《__hbequx2》处理“比较两个half2类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。”。《__hbneux2》提供“比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。”，其具体合同或探针直接接入half2 全 lane 无序相等、其有序版本和无序不等补集。
- [__hbnex2](_hbnex2.md)（`same_topic`）：__hbneux2 与 __hbnex2 都把两个 half2 分量的“不等”归约为 bool；区别是前者把 NaN 分量视为 true，后者遇 NaN 返回 false。
- [__hneux2](_hneux2.md)（`same_topic`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__hbneux2正文界定“比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hbneux2正文说明“比较两个half2类型数据的两个分量是否不相等，当两个分量均不相等时返回true。若任一输入的分量为nan，该分量的比较结果为true”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
<!-- cannbot:related:end -->
