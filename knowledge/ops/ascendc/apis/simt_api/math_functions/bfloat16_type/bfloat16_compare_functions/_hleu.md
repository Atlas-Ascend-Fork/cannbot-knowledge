---
type: API
title: __hleu
description: 比较两个bfloat16类型的数据，当第一个数据小于或等于第二个数据时，返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hleu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hleu

比较两个bfloat16类型的数据，当第一个数据小于或等于第二个数据时，返回true。若任一输入为nan，返回true。
函数原型：bool __hleu(bfloat16_t x, bfloat16_t y)
返回值：比较输入的第一个数是否小于或等于第二个数的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hgeu](_hgeu.md)（`same_topic`）：《__hgeu》处理“比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。”。《__hleu》提供“比较两个bfloat16类型的数据，当第一个数据小于或等于第二个数据时，返回true。若任一输入为nan，返回true。”，其具体合同或探针直接接入无序大于等于的 NaN 语义、有序对应项和 half/bfloat16 对应实现。
- [__hisnan](_hisnan.md)（`same_topic`）：__hleu 与《__hisnan》的实质衔接是：bfloat16 unordered LE 需与 ordered LE、GE/LT/GT、isnan 和 neq 对照 NaN 行为。
- [__hle](_hle.md)（`same_topic`）：__hle 与 __hleu 都执行 bfloat16 的 ≤ 比较；区别仅在 NaN 时 ordered 版本返回 false、unordered 版本返回 true，核心谓词合同相同。
<!-- cannbot:related:end -->
