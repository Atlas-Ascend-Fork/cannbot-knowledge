---
type: API
title: Lgammaf
description: 获取输入数据x伽马值的绝对值并求自然对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/lgammaf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Lgammaf

功能：获取输入数据x伽马值的绝对值并求自然对数。

函数原型：float lgammaf(float x)

参数：x（输入）源操作数。

返回值：输入数据的伽马值的绝对值并求自然对数。特殊值：0→inf；inf→inf；-inf→inf；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Digamma](../../../simd_api/adv_api/math_compute/digamma_interface/digamma.md)（`related`）：Lgammaf 与《Digamma》的实质衔接是：Lgammaf 与向量 Lgamma 是同一 log-gamma 任务，Tgamma 给出非对数对应量，Digamma 则给出其导数语义。
- [Tgammaf](tgammaf.md)（`related`）：lgammaf 返回 log|Gamma(x)|，可在 tgammaf 易溢出时用于范围稳定计算，但输出语义不同。
- [Lgamma](../../../simd_api/adv_api/math_compute/lgamma_interface/lgamma.md)（`same_topic`）：《Lgamma》处理“按元素计算x的gamma函数的绝对值并求自然对数”。《Lgammaf》明确“获取输入数据x伽马值的绝对值并求自然对数。”，可直接用于核对Lgamma Kernel、临时空间查询与标量 lgammaf 的同一计算合同。
<!-- cannbot:related:end -->
