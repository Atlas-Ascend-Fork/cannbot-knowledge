---
type: API
title: Frexpf
description: 将x分解为归一化尾数和2的整数次幂，指数存入exp参数中。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/frexpf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Frexpf

功能：将x转换为归一化1/2, 1)的有符号数乘以2的积分幂。返回归一化的有符号数，指数存储在exp中。
函数原型：float frexpf(float x, int *exp)

参数：x（输入）源操作数，exp（输出）Unified Buffer、Global Memory或栈空间的地址，用于存储以2为底的指数。

返回值：将x转换为归一化[1/2, 1)的有符号数乘以2的积分幂时，返回该有符号数。特殊值：inf→inf，exp为0；-inf→-inf，exp为0；nan→nan，exp为0。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Ldexpf](ldexpf.md)（`related`）：功能：获取输入x乘以2的exp次幂的结果。；功能：将x转换为归一化1/2, 1)的有符号数乘以2的积分幂。返回归一化的有符号数，指数存储在exp中。Ldexpf 用尾数和指数合成数值，Frexpf 把数值分解为同一表示，构成二进制指数表示的正反任务链。
<!-- cannbot:related:end -->
