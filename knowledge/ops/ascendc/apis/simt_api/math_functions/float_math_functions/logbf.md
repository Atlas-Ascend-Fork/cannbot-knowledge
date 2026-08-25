---
type: API
title: Logbf
description: 计算以2为底输入数据的对数，对结果向下取整返回浮点数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/logbf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Logbf

功能：计算以2为底，输入数据的对数，并对结果向下取整，返回浮点数。

函数原型：float logbf(float x)

参数：x（输入）源操作数。

返回值：以2为底的x的对数，并向下取整后的值。特殊值：inf→inf；-inf→inf；nan→nan；0→-inf。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Ilogbf](ilogbf.md)（`same_topic`）：Logbf 与《Ilogbf》的实质衔接是：Logbf 返回浮点形式的二进制指数，Ilogbf 返回整数形式的同一指数任务，两者特殊值契约可直接对照。
<!-- cannbot:related:end -->
