---
type: API
title: __urhadd
description: 获取uint32类型数据x和y的向上取整平均值，避免中间求和溢出。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__urhadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __urhadd

uint32 向上取整平均值函数。获取 uint32 类型数据 x 和 y 的向上取整平均值，避免中间求和溢出。

函数原型：unsigned int __urhadd(unsigned int x, unsigned int y)

参数 x、y 为源操作数。返回输入数据的向上取整平均值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__hadd（整数数学函数）](_hadd.md)（`related`）：__urhadd 同时切换为 uint32 和向上取整，补全有/无符号与上下取整的平均值组合。
- [__rhadd（整数数学函数）](_rhadd.md)（`related`）：__urhadd 对 uint32 做同样的向上取整平均且避免中间溢出，是无符号类型对应物。
- [__uhadd（整数数学函数）](_uhadd.md)（`same_topic`）：uhadd 与 urhadd 同为 uint32 防溢出平均，区别是普通取整与向上取整。
<!-- cannbot:related:end -->
