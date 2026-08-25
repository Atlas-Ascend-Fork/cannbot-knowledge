---
type: API
title: Tgammaf
description: 获取输入数据x的伽马函数值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/tgammaf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Tgammaf

功能：获取输入数据x的伽马函数值。

函数原型：float tgammaf(float x)

参数：x（输入）源操作数。

返回值：输入数据的伽马函数值。特殊值：-0→-inf；inf→inf；-inf→nan；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [BF16 gamma Cast 分阶段编排导致随机 NaN](../../../../runbooks/precision/bf16_gamma_cast_must_share_ordered_compute_stage.md)（`exemplifies`）：该卡说明低精度 gamma 参数 cast 与消费需要同一有序阶段，提供 gamma 类计算链的同步验证实例。
- [Digamma](../../../simd_api/adv_api/math_compute/digamma_interface/digamma.md)（`related`）：Digamma 是 log-gamma 的导数，适用于梯度/特殊函数链而非替代 Gamma 值。
- [Lgamma](../../../simd_api/adv_api/math_compute/lgamma_interface/lgamma.md)（`related`）：高阶 LocalTensor Lgamma 与 SIMT lgammaf 同为 log-gamma，可按数据路径选择稳定替代。
- [Lgammaf](lgammaf.md)（`related`）：lgammaf 返回 log|Gamma(x)|，可在 tgammaf 易溢出时用于范围稳定计算，但输出语义不同。
<!-- cannbot:related:end -->
