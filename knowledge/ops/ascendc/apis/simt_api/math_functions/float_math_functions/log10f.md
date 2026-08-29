---
type: API
title: Log10f
description: 获取以10为底输入数据的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log10f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Log10f

功能：获取以10为底，输入数据的对数。

函数原型：float log10f(float x)

参数：x（输入）源操作数。

返回值：以10为底的x的对数。特殊值：inf→inf；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachLog10 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_log10_950.md)（`related`）：获取以10为底，输入数据的对数；R-001 FLOAT `log10f`；950 ForeachLog10 的 FLOAT route 直接消费该 SIMT 函数。
<!-- cannbot:related:end -->
