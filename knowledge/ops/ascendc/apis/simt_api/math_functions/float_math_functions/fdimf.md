---
type: API
title: Fdimf
description: 获取两个输入数据的差值，差值小于0时返回0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/fdimf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Fdimf

功能：获取两个输入数据的差值，差值小于0时，返回0。

函数原型：float fdimf(float x, float y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据的差值，差值小于0时，返回0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Fmaxf](fmaxf.md)（`related`）：《Fdimf》处理“获取两个输入数据的差值，差值小于0时返回0。”。《Fmaxf》提供“获取两个输入数据中的最大值。”，其具体合同或探针直接接入Fdimf 的 max(x-y,0) 定义与 Fmaxf 组成关系。
<!-- cannbot:related:end -->
