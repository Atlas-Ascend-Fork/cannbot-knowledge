---
type: API
title: Log1pf
description: 获取以e为底输入数据加1的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log1pf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Log1pf

功能：获取以e为底，输入数据加1的对数（即ln(x+1)），可避免x接近0时的精度损失。

函数原型：float log1pf(float x)

参数：x（输入）源操作数。

返回值：以e为底的x+1的对数。特殊值：nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [数学函数logf](logf.md)（`related`）：《数学函数logf》说明获取以e为底，输入数据的对数。；《Log1pf》说明计算ln(1+x)，在x接近0时比直接log(1+x)保持更高精度。。二者在logf是直接自然对数，而log1pf在x接近0时实现同一数学量的稳定形式上存在可执行的直接衔接。
- [Expm1f](expm1f.md)（`same_topic`）：Log1pf 与《Expm1f》的实质衔接是：Log1pf 计算 ln(1+x) 并保留 x 近零精度；logf 是直接但近零易损的等价表达，expm1f 是配套的稳定逆向公式。
<!-- cannbot:related:end -->
