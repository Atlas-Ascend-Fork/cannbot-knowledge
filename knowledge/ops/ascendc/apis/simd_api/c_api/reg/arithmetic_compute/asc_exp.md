---
type: API
title: AscExp
description: 根据mask对源操作数src按元素求自然指数，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscExp

该接口根据mask，对源操作数src进行按元素求自然指数操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../../../../../runbooks/precision/ascend950_ftz_exp.md)（`exemplifies`）：Ascend950 向量管 FTZ 刷新次正规 exp 为零 与《AscExp》的实质衔接是：该卡锁定 Ascend950 Exp 次正规输出 FTZ；Exp 接口、clamp/overflow/subnormal 姊妹故障和 softplus 极值用例共同验证硬件边界与可修软件因素。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0 与《AscExp》的实质衔接是：该 sigmoid 失败由 exp(-z) 溢出和 subnormal FTZ 共同造成；Exp/Reciprocal/Clamp 接口及同类数值故障分别提供溢出阈值、稳定式和直接除法验证边界。
- [AscExp](../../vector_compute/asc_exp.md)（`same_topic`）：AscExp 与《AscExp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
- [Exp](../../../adv_api/math_compute/exp_interface/exp.md)（`same_topic`）：AscExp 与《Exp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
- [Exp](../../../basic_api/memory_vector_compute/basic_arithmetic/exp.md)（`same_topic`）：AscExp 与《Exp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
- [Exp](../../../basic_api/reg_vector_compute/basic_arithmetic/exp.md)（`same_topic`）：AscExp 与《Exp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
<!-- cannbot:related:end -->
