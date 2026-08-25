---
type: API
title: Htanh
description: 计算bfloat16_t输入数据的双曲正切值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_math_functions/htanh.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Htanh

获取输入数据的三角函数双曲正切值。
函数原型：bfloat16_t htanh(bfloat16_t x)
返回值：输入数据的双曲正切值。本接口受全局饱和模式影响，特殊值如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 命名空间无 Erf/Tanh 封装](../../../../../runbooks/compilation/ascend950_reg_erf_tanh.md)（`exemplifies`）：《Htanh》说明计算bfloat16_t输入数据的双曲正切值。；《Ascend950 Reg 命名空间无 Erf/Tanh 封装》说明Ascend950/dav-3510 的 AscendC::Reg 一元运算头文件仅声明 Abs/Relu/Exp/Sqrt/Ln/Log/Log2/Log10/Neg/Not 十种操作，不含 Erf/Tanh/Sigmoid 等超越函数；在 Reg API 策略下实现 GELU exact 模式需将 erf 分解为多项式 + Exp + Mul + Add 组合。。二者在不同标量/双分量dtype的tanh接口共享双曲正切语义；Reg缺少Tanh封装的故障决定何时不能直接换用Reg层接口上存在可执行的直接衔接。
- [H2Tanh](../../half_type/half2_math_functions/h2tanh.md)（`related`）：《Htanh》说明计算bfloat16_t输入数据的双曲正切值。；《H2Tanh》说明获取输入数据各元素的三角函数双曲正切值。。二者在不同标量/双分量dtype的tanh接口共享双曲正切语义；Reg缺少Tanh封装的故障决定何时不能直接换用Reg层接口上存在可执行的直接衔接。
- [Htanh](../../half_type/half_math_functions/htanh.md)（`related`）：Htanh 与《Htanh》的实质衔接是：half、bfloat16、half2 和 float Tanh 是同一函数的载体变体；Reg 缺少 Tanh 的故障卡明确了不能跨层照搬的边界。
- [H2Tanh](../bfloat16x2_math_functions/h2tanh.md)（`same_topic`）：Htanh 与 H2Tanh 都计算 bfloat16 双曲正切，后者把相同操作应用到 bfloat16x2 的两个分量。
- [Tanhf](../../float_math_functions/tanhf.md)（`same_topic`）：Tanhf 与《Htanh》的实质衔接是：Tanhf 与半精度/bfloat16、SIMD Tanh 入口实现同一双曲正切语义，Atanhf 是其反函数；Reg 缺少 Tanh 封装的案例明确需要选择这些现有入口而非虚构 Reg API。
<!-- cannbot:related:end -->
