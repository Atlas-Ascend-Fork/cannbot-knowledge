---
type: API
title: Normcdfinvf
description: 获取输入数据x的标准正态累积分布的逆函数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/normcdfinvf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Normcdfinvf

功能：获取输入数据x的标准正态累积分布的逆函数。

函数原型：float normcdfinvf(float x)

参数：x（输入）源操作数。

返回值：获取输入数据x的标准正态累积分布的逆函数。特殊值：0→-inf；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Normcdff](normcdff.md)（`related`）：功能：获取输入数据x的标准正态分布的累积分布函数值。；功能：获取输入数据x的标准正态累积分布的逆函数。两页提供标准正态 CDF 的正向与逆向变换，是概率值和分位点互相转换的同一任务链。
<!-- cannbot:related:end -->
