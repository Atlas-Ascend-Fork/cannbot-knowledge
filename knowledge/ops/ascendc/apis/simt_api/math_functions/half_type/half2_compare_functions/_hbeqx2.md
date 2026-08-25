---
type: API
title: __hbeqx2
description: 比较两个half2类型数据的两个分量是否相等，仅当两个分量均相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hbeqx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hbeqx2

功能：比较两个half2类型数据的两个分量是否相等，仅当两个分量均相等时返回true。

函数原型：bool __hbeqx2(half2 x, half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：比较输入数据各分量是否均相等的结果。特殊值：0→true；任一分量为nan→false；inf→true；-inf→true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hbeqx2](../../bfloat16_type/bfloat16x2_compare_functions/_hbeqx2.md)（`related`）：half2 同名函数也要求两个分量都相等才返回 true，是跨 dtype 对应物。
- [__heqx2](_heqx2.md)（`related`）：__heqx2 返回逐 lane 的 half2 0/1 结果，而 focal 把两 lane 归约为单个 bool；输出形态差异决定后续分支或向量计算选型。
- [__hbequx2](_hbequx2.md)（`same_topic`）：《__hbequx2》处理“比较两个half2类型数据的两个分量是否相等，当两个分量均相等时返回true。若任一输入的分量为nan，该分量的比较结果为true。”。《__hbeqx2》提供“比较两个half2类型数据的两个分量是否相等，仅当两个分量均相等时返回true。”，其具体合同或探针直接接入half2 全 lane 无序相等、其有序版本和无序不等补集。
<!-- cannbot:related:end -->
