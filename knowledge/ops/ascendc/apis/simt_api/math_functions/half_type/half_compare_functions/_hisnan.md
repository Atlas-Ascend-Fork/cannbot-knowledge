---
type: API
title: __hisnan
description: 判断浮点数是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hisnan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hisnan

功能：判断浮点数是否为nan。

函数原型：bool __hisnan(half x)

参数：x（输入）源操作数。

返回值：返回是否为nan的结果。输入为非nan返回false，输入为nan返回true。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachMinimumList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_minimum_list_950.md)（`related`）：y［idx］=(__hisnan(a) ｜｜ a<b) ? a : b；功能：判断浮点数是否为nan。；950 ForeachMinimumList 的 FP16 SIMT 路线直接调用该 helper 决定 NaN 传播分支。
<!-- cannbot:related:end -->
