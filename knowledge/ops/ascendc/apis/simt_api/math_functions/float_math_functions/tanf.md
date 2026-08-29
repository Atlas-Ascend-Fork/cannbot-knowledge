---
type: API
title: 数学函数tanf
description: 获取输入数据的三角函数正切值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/tanf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数tanf

功能：获取输入数据的三角函数正切值。

函数原型：float tanf(float x)

参数：x（输入）源操作数。

返回值：输入数据的正切值。特殊值：inf→nan；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“950 FP32 路线直接执行 `tanf(float)`；FP16/BF16 路线严格按 source 顺序执行低精度→FP32、`tanf`、FP32→低精度。”明确三条 950 route 的共同计算 primitive；“函数原型：float tanf(float x)”给出该 primitive 的标量签名。
<!-- cannbot:related:end -->
