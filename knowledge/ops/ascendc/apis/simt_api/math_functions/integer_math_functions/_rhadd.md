---
type: API
title: __rhadd（整数数学函数）
description: 获取int32类型数据x和y的向上取整平均值，避免中间求和溢出。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.arithmetic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__rhadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __rhadd

int32 向上取整平均值函数。获取 int32 类型数据 x 和 y 的向上取整平均值，避免中间求和溢出。

函数原型：int __rhadd(int x, int y)

参数 x、y 为源操作数。返回输入数据的向上取整平均值。仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。无约束。需包含头文件 "simt_api/device_functions.h"。支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [__hadd（整数数学函数）](_hadd.md)（`related`）：__rhadd 同样计算 int32 无溢出平均值，但在奇数和时向上取整；与 __hadd 的向下取整形成成对选择。
- [__uhadd（整数数学函数）](_uhadd.md)（`related`）：“__uhadd（整数数学函数）”定义：获取uint32类型数据x和y的平均值，避免中间求和溢出。；“__rhadd（整数数学函数）”定义：获取int32类型数据x和y的向上取整平均值，避免中间求和溢出。。实质衔接：__urhadd 保持 uint32 防溢出平均但向上取整；__rhadd 改为有符号且向上取整，明确符号与舍入选择。
- [__urhadd](_urhadd.md)（`related`）：__urhadd 对 uint32 做同样的向上取整平均且避免中间溢出，是无符号类型对应物。
<!-- cannbot:related:end -->
