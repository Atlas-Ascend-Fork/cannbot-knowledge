---
type: API
title: 数学函数j1f
description: 获取输入数据x的1阶第一类贝塞尔函数j1的值。 !
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/j1f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 数学函数j1f

功能：获取输入数据x的1阶第一类贝塞尔函数j1的值。贝塞尔函数常用于波动方程和圆柱坐标系问题的求解。

函数原型：float j1f(float x)

参数：x（输入）源操作数。

返回值：输入数据的1阶第一类贝塞尔函数j1的值。返回值范围为[-1, 1]。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [数学函数jnf](jnf.md)（`same_topic`）：数学函数jnf 与《数学函数j1f》的实质衔接是：jnf 与 ynf 都接受阶数 n，分别计算第一类和第二类 Bessel 函数；j1f 是 n=1 的直接特化，可核对阶数和 subnormal 限制。
<!-- cannbot:related:end -->
