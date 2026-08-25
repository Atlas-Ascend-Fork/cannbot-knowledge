---
type: API
title: Tanhf
description: 获取输入数据的双曲正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/tanhf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Tanhf

功能：获取输入数据的三角函数双曲正切值。

函数原型：float tanhf(float x)

参数：x（输入）源操作数。

返回值：输入数据的双曲正切值。特殊值：inf→1.0；-inf→-1.0；nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 命名空间无 Erf/Tanh 封装](../../../../runbooks/compilation/ascend950_reg_erf_tanh.md)（`exemplifies`）：Tanhf 与《Ascend950 Reg 命名空间无 Erf/Tanh 封装》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
- [Atanhf](atanhf.md)（`related`）：Tanhf 与《Atanhf》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
- [Htanh](../half_type/half_math_functions/htanh.md)（`related`）：Htanh 与《Tanhf》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
- [H2Tanh](../bfloat16_type/bfloat16x2_math_functions/h2tanh.md)（`same_topic`）：Tanhf 与《H2Tanh》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
- [H2Tanh](../half_type/half2_math_functions/h2tanh.md)（`same_topic`）：Tanhf 与《H2Tanh》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
- [Htanh](../bfloat16_type/bfloat16_math_functions/htanh.md)（`same_topic`）：Tanhf 与《Htanh》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
- [Tanh接口](../../../simd_api/adv_api/math_compute/tanh_interface/tanh_interface.md)（`same_topic`）：Tanhf 与《Tanh接口》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
<!-- cannbot:related:end -->
