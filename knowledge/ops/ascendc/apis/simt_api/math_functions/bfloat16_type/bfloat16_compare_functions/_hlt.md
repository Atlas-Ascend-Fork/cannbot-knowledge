---
type: API
title: __hlt
description: 比较两个bfloat16类型数据，仅当第一个数据小于第二个数据时，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hlt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hlt

比较两个bfloat16类型数据，仅当第一个数据小于第二个数据时，返回true。
函数原型：bool __hlt(bfloat16_t x, bfloat16_t y)
返回值：输入的第一个数是否小于第二个数的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hge](_hge.md)（`related`）：在无 NaN 前提下，__hge(x,y) 是 __hlt(x,y) 的逻辑补集；组合可构造互斥分支并检查边界相等行为。
- [__hle](_hle.md)（`related`）：__hlt 把 <= 收紧为 < 且同为 ordered，比边界相等元素是否命中时可直接对照。
- [__hltu](_hltu.md)（`same_topic`）：__hlt 与 __hltu 都比较 bfloat16 的 a<b；前者为有序比较，后者在 NaN 时采用 unordered 语义，是同一故障边界的直接选型。
<!-- cannbot:related:end -->
