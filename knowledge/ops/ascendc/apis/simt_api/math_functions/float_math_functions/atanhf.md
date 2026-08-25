---
type: API
title: Atanhf
description: 获取输入数据的反双曲正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/atanhf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Atanhf

功能：获取输入数据的反双曲正切值，等价于0.5*ln((1+x)/(1-x))。

函数原型：float atanhf(float x)

参数：x（输入）源操作数，取值范围为(-1, 1)。

返回值：输入数据的反双曲正切值。特殊值：nan→nan。

约束：无。需包含头文件 simt_api/math_functions.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [GetAtanhMaxMinTmpSize](../../../simd_api/adv_api/math_compute/atanh_interface/get_atanh_max_min_tmp_size.md)（`related`）：Atanhf 负责“获取输入数据的反双曲正切值”；GetAtanhMaxMinTmpSize 负责“在host侧获取Atanh接口预留临时空间的最大和最小值，用于Tiling参数选择”。
- [GetAtanhTmpBufferFactorSize](../../../simd_api/adv_api/math_compute/atanh_interface/get_atanh_tmp_buffer_factor_size.md)（`related`）：《GetAtanhTmpBufferFactorSize》处理“获取Atanh接口的maxLiveNodeCount和extraBuffer，用于推算固定空间下单次最大计算元素数”。《Atanhf》明确“获取输入数据的反双曲正切值。”，可直接用于核对Atanh 高阶 Kernel 的临时空间系数、上下界估算和对应标量实现。
- [Tanhf](tanhf.md)（`related`）：Tanhf 与《Atanhf》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
- [Atanh](../../../simd_api/adv_api/math_compute/atanh_interface/atanh.md)（`same_topic`）：《Atanh》处理“按元素做反双曲正切函数计算，输入值域需在指定区间内”。《Atanhf》提供“获取输入数据的反双曲正切值。”，其具体合同或探针直接接入Atanh Kernel 调用、临时空间推导和 SIMT 对应实现。
- [Atanh接口](../../../simd_api/adv_api/math_compute/atanh_interface/atanh_interface.md)（`same_topic`）：Atanhf 的核心契约是“获取输入数据的反双曲正切值”；Atanh接口 补充“提供Atanh反双曲正切计算接口及其Tiling临时空间大小查询接口，包含Atanh、GetAtanhMaxMinTmpSize等”。
<!-- cannbot:related:end -->
