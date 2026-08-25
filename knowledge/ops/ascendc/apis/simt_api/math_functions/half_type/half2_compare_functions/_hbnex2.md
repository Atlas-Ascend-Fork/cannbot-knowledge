---
type: API
title: __hbnex2
description: 比较两个half2类型数据的两个分量是否不相等，仅当两个分量均不相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbnex2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbnex2

功能：比较两个half2类型数据的两个分量是否不相等，仅当两个分量均不相等时返回true。

函数原型：bool __hbnex2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均不相等的结果。任一输入为nan时返回false。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbnex2](../../bfloat16_type/bfloat16x2_compare_functions/_hbnex2.md)（`related`）：bfloat16x2 __hbnex2 保持“两个分量均不等才为 true”的归约规则，仅替换数值格式。
- [__hnex2](_hnex2.md)（`related`）：__hnex2 保留每个分量的比较结果为 half2，而 __hbnex2 再把两个分量归约成一个 bool；两者适用于不同的后续分支粒度。
- [__hbneux2](_hbneux2.md)（`same_topic`）：__hbneux2 与 __hbnex2 都把两个 half2 分量的“不等”归约为 bool；区别是前者把 NaN 分量视为 true，后者遇 NaN 返回 false。
- [__hnex2_mask](_hnex2_mask.md)（`same_topic`）：焦点处理half2 not-equal mask 的 ordered/unordered 与 bool/数值返回形态；__hbnex2正文说明“比较两个half2类型数据的两个分量是否不相等，仅当两个分量均不相等时返回true”。候选只改变 NaN unordered 规则或结果编码形式，能指导选择正确比较契约。
<!-- cannbot:related:end -->
