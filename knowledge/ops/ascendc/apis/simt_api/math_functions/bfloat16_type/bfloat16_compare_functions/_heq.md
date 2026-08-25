---
type: API
title: __heq
description: 比较两个bfloat16类型数据是否相等，相等时返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__heq.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __heq

比较两个bfloat16类型数据是否相等，相等时返回true。
函数原型：bool __heq(bfloat16_t x, bfloat16_t y)
返回值：输入数据是否相等的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__heq](../../half_type/half_compare_functions/_heq.md)（`related`）：《__heq》处理“比较两个bfloat16类型数据是否相等，相等时返回true。”。《__heq》明确提供“比较两个half类型数据是否相等，相等时返回true。”，其参数、调用或验证步骤直接接入bfloat16x2 相等比较的有序/无序语义、互补关系和 half2 对应实现。
- [__hne](_hne.md)（`related`）：《__heq》处理“比较两个bfloat16类型数据是否相等，相等时返回true。”。《__hne》明确提供“比较两个bfloat16类型数据是否不相等，不相等时返回true。”，其参数、调用或验证步骤直接接入bfloat16x2 相等比较的有序/无序语义、互补关系和 half2 对应实现。
- [__hneu](_hneu.md)（`related`）：《__heq》处理“比较两个bfloat16类型数据是否相等，相等时返回true。”。《__hneu》明确提供“比较两个bfloat16类型数据是否不相等，不相等时返回true。若任一输入为nan，返回true。”，其参数、调用或验证步骤直接接入bfloat16x2 相等比较的有序/无序语义、互补关系和 half2 对应实现。
- [__hequ](_hequ.md)（`same_topic`）：《__heq》处理“比较两个bfloat16类型数据是否相等，相等时返回true。”。《__hequ》明确提供“比较两个bfloat16类型数据是否相等，相等时返回true。若任一输入为nan，返回true。”，其参数、调用或验证步骤直接接入bfloat16x2 相等比较的有序/无序语义、互补关系和 half2 对应实现。
<!-- cannbot:related:end -->
