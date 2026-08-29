---
type: API
title: Ilogbf
description: 计算以2为底输入数据的对数，对结果向下取整返回整数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/ilogbf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Ilogbf

功能：计算以2为底，输入数据的对数，并对结果向下取整，返回整数。

函数原型：int ilogbf(float x)

参数：x（输入）源操作数。

返回值：对于有限非零值，返回以2为底的x的绝对值的对数，并向下取整后的整数值。特殊值：+0→ASCRT_MIN_VAL_S；-0→ASCRT_MIN_VAL_S；inf→ASCRT_MAX_VAL_S；-inf→ASCRT_MAX_VAL_S；nan→ASCRT_MIN_VAL_S。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Logbf](logbf.md)（`related`）：功能：计算以2为底，输入数据的对数，并对结果向下取整，返回整数。；功能：计算以2为底，输入数据的对数，并对结果向下取整，返回浮点数。。两接口共享有限非零输入的指数提取语义，但返回类型和零、无穷、NaN 的特殊值合同不同，选型时需成对比较。
<!-- cannbot:related:end -->
