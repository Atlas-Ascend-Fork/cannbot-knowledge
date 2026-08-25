---
type: API
title: Normcdff
description: 获取输入数据x的标准正态分布的累积分布函数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/normcdff.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Normcdff

功能：获取输入数据x的标准正态分布的累积分布函数值。

函数原型：float normcdff(float x)

参数：x（输入）源操作数。

返回值：输入数据的标准正态分布的累积分布函数值。特殊值：-inf→0；inf→1；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Normcdfinvf](normcdfinvf.md)（`related`）：Normcdff 计算标准正态 CDF，而 Normcdfinvf 计算其逆映射；二者的 0/1 与 ±inf 边界互相校验，可直接组成正向—逆向验证。
<!-- cannbot:related:end -->
