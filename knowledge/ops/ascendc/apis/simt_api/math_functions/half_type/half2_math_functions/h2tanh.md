---
type: API
title: H2Tanh
description: 获取输入数据各元素的三角函数双曲正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2tanh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Tanh

功能：获取输入数据各元素的三角函数双曲正切值。

函数原型：half2 h2tanh(half2 x)

参数：x（输入）源操作数。

返回值：输入数据各元素的双曲正切值。特殊值：±0→0；nan→0；inf→1；-inf→-1；ASCRT_MAX_NORMAL_FP16→1；-ASCRT_MAX_NORMAL_FP16→-1。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Exp](h2exp.md)（`related`）：tanh 可由 exp 组合，但 h2tanh 提供直接实现；拆解路径需单独验证溢出和精度。
- [H2Tanh](../../bfloat16_type/bfloat16x2_math_functions/h2tanh.md)（`related`）：H2Tanh 与《H2Tanh》的实质衔接是：bfloat16x2、half2、bfloat16 标量和 float 的 tanh 变体实现同一函数，可据输入载体选择并核对特殊值。
- [Htanh](../../bfloat16_type/bfloat16_math_functions/htanh.md)（`related`）：《Htanh》说明计算bfloat16_t输入数据的双曲正切值。；《H2Tanh》说明获取输入数据各元素的三角函数双曲正切值。。二者在不同标量/双分量dtype的tanh接口共享双曲正切语义；Reg缺少Tanh封装的故障决定何时不能直接换用Reg层接口上存在可执行的直接衔接。
- [Tanhf](../../float_math_functions/tanhf.md)（`same_topic`）：Tanhf 与《H2Tanh》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
<!-- cannbot:related:end -->
