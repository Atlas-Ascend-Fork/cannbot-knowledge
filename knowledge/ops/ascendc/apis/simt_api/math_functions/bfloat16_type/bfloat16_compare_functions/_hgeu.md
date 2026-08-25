---
type: API
title: __hgeu
description: 比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hgeu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hgeu

比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。
函数原型：bool __hgeu(bfloat16_t x, bfloat16_t y)
返回值：比较输入的第一个数是否大于或等于第二个数的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__hgtu](_hgtu.md)（`related`）：__hgeu 共享 unordered NaN=true 语义，但包含相等边界；与 __hgtu 对照可精确选择 > 或 >=。
- [__hge](_hge.md)（`same_topic`）：《__hgeu》处理“比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。”。《__hge》提供“比较两个bfloat16类型数据，仅当第一个数据大于或等于第二个数据时，返回true。”，其具体合同或探针直接接入无序大于等于的 NaN 语义、有序对应项和 half/bfloat16 对应实现。
- [__hgeu](../../half_type/half_compare_functions/_hgeu.md)（`same_topic`）：《__hgeu》处理“比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。”。《__hgeu》提供“比较两个half类型数据，当第一个数大于或等于第二个数时，返回true。若任一输入为nan，返回true。”，其具体合同或探针直接接入无序大于等于的 NaN 语义、有序对应项和 half/bfloat16 对应实现。
- [__hleu](_hleu.md)（`same_topic`）：《__hgeu》处理“比较两个bfloat16类型数据，当第一个数据大于或等于第二个数据时，返回true。若任一输入为nan，返回true。”。《__hleu》提供“比较两个bfloat16类型的数据，当第一个数据小于或等于第二个数据时，返回true。若任一输入为nan，返回true。”，其具体合同或探针直接接入无序大于等于的 NaN 语义、有序对应项和 half/bfloat16 对应实现。
<!-- cannbot:related:end -->
