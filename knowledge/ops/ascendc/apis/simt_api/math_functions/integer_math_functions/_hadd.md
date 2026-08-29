---
type: API
title: __hadd（整数数学函数）
description: 获取int32类型数据x和y的平均值，避免中间求和溢出。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__hadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hadd

int32 有符号平均值函数。获取 int32 类型数据 x 和 y 的平均值，计算过程避免中间求和溢出（向下取整）。

函数原型：int __hadd(int x, int y)

参数 x、y 为源操作数。返回输入数据的平均值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__rhadd（整数数学函数）](_rhadd.md)（`related`）：int32 向上取整平均值函数。获取 int32 类型数据 x 和 y 的向上取整平均值，避免中间求和溢出。；int32 有符号平均值函数。获取 int32 类型数据 x 和 y 的平均值，计算过程避免中间求和溢出（向下取整）。。两接口都避免中间求和溢出，唯一区别是奇数和的向上或向下取整，直接支撑整数平均值舍入选型。
<!-- cannbot:related:end -->
