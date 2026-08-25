---
type: API
title: Coshf
description: 获取输入数据的双曲余弦值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/coshf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Coshf

功能：获取输入数据的双曲余弦值。

函数原型：float coshf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲余弦值。特殊值：inf→inf；-inf→inf；nan→nan；0→1。

约束：本接口支持的输入数据为[-89.4, 89.4]范围内的数据。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Acoshf](acoshf.md)（`same_topic`）：Acoshf 与《Coshf》的实质衔接是：Acoshf 是标量双曲反余弦；Acosh 高阶接口及空间查询是 tensor 版本，Coshf 是其反函数，可用于定义域和往返验证。
<!-- cannbot:related:end -->
