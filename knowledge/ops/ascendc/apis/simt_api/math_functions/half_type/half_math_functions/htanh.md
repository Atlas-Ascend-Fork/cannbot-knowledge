---
type: API
title: Htanh
description: 计算half输入数据的双曲正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_math_functions/htanh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Htanh

功能：获取输入数据的三角函数双曲正切值。

函数原型：half htanh(half x)

参数：x（输入）源操作数。

返回值：输入数据的双曲正切值。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→0；inf→1；-inf→-1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 命名空间无 Erf/Tanh 封装](../../../../../runbooks/compilation/ascend950_reg_erf_tanh.md)（`exemplifies`）：Htanh 与《Ascend950 Reg 命名空间无 Erf/Tanh 封装》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
- [H2Tanh](../../bfloat16_type/bfloat16x2_math_functions/h2tanh.md)（`related`）：Htanh 与《H2Tanh》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
- [Htanh](../../bfloat16_type/bfloat16_math_functions/htanh.md)（`related`）：Htanh 与《Htanh》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
- [Tanhf](../../float_math_functions/tanhf.md)（`related`）：Htanh 与《Tanhf》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
<!-- cannbot:related:end -->
