---
type: API
title: __hge
description: 比较两个bfloat16类型数据，仅当第一个数据大于或等于第二个数据时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hge

比较两个bfloat16类型数据，仅当第一个数据大于或等于第二个数据时，返回true。
函数原型：bool __hge(bfloat16_t x, bfloat16_t y)
返回值：输入的第一个数是否大于或等于第二个数的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hgt](_hgt.md)（`related`）：__hge 将严格大于扩展为大于等于，帮助根据边界相等时的预期选择比较谓词。
- [__hlt](_hlt.md)（`related`）：在无 NaN 前提下，__hge(x,y) 是 __hlt(x,y) 的逻辑补集；组合可构造互斥分支并检查边界相等行为。
- [__hgeu](_hgeu.md)（`same_topic`）：《__hgeu》处理“比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。”。《__hge》提供“比较两个bfloat16类型数据，仅当第一个数据大于或等于第二个数据时，返回true。”，其具体合同或探针直接接入无序大于等于的 NaN 语义、有序对应项和 half/bfloat16 对应实现。
<!-- cannbot:related:end -->
