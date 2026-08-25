---
type: API
title: Nearbyintf
description: 获取与输入浮点数最接近的整数，输入浮点数与左右整数的距离相等时，返回偶数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/nearbyintf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Nearbyintf

功能：获取与输入浮点数最接近的整数，输入浮点数与左右整数的距离相等时，返回偶数。

函数原型：float nearbyintf(float x)

参数：x（输入）源操作数。

返回值：最接近浮点数的整数。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Llrintf](llrintf.md)（`related`）：llrintf 把最近整数结果写为 long long，适合需要更宽整数范围而非保持 float 的场景。
- [Lrintf](lrintf.md)（`related`）：lrintf 采用相同最近整数规则但把结果转换为 long，返回类型决定后续溢出和存储语义。
- [Rintf](rintf.md)（`same_topic`）：nearbyintf 与 rintf 都按 ties-to-even 返回最接近的浮点整数值；两卡给出的输入、返回类型和舍入规则相同。
<!-- cannbot:related:end -->
