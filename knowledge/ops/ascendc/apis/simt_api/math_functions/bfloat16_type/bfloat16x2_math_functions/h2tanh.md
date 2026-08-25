---
type: API
title: H2Tanh
description: 获取输入数据各元素的三角函数双曲正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16x2_math_functions/h2tanh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Tanh

功能：获取输入数据各元素的三角函数双曲正切值。

函数原型：bfloat16x2_t h2tanh(bfloat16x2_t x)

参数：x（输入）源操作数。

返回值：输入数据各元素的双曲正切值。本接口受全局饱和模式影响，。特殊值：0→0；-0→-0；nan→0；inf→1.0；-inf→-1.0。

约束：无。需包含头文件 simt_api/asc_bf16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Tanh](../../half_type/half2_math_functions/h2tanh.md)（`related`）：H2Tanh 与《H2Tanh》的实质衔接是：bfloat16x2、half2、bfloat16 标量和 float 的 tanh 变体实现同一函数，可据输入载体选择并核对特殊值。
- [Htanh](../../half_type/half_math_functions/htanh.md)（`related`）：Htanh 与《H2Tanh》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
- [Htanh](../bfloat16_math_functions/htanh.md)（`same_topic`）：Htanh 与 H2Tanh 都计算 bfloat16 双曲正切，后者把相同操作应用到 bfloat16x2 的两个分量。
- [Tanhf](../../float_math_functions/tanhf.md)（`same_topic`）：Tanhf 与《H2Tanh》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
<!-- cannbot:related:end -->
