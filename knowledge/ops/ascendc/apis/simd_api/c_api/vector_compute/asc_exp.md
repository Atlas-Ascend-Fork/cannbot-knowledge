---
type: API
title: AscExp
description: asc_exp（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_exp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscExp

按元素取自然指数，计算公式如下。
函数原型：void asc_exp(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Ascend950 向量管 FTZ 刷新次正规 exp 为零](../../../../runbooks/precision/ascend950_ftz_exp.md)（`exemplifies`）：Ascend950 向量管 FTZ 刷新次正规 exp 为零 与《AscExp》的实质衔接是：该卡锁定 Ascend950 Exp 次正规输出 FTZ；Exp 接口、clamp/overflow/subnormal 姊妹故障和 softplus 极值用例共同验证硬件边界与可修软件因素。
- [arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0](../../../../runbooks/precision/arch35_sigmoid_z_exp_inf_sig_0.md)（`exemplifies`）：arch35 sigmoid 大负 z 下 exp 溢出 inf 致 sig=0 与《AscExp》的实质衔接是：该 sigmoid 失败由 exp(-z) 溢出和 subnormal FTZ 共同造成；Exp/Reciprocal/Clamp 接口及同类数值故障分别提供溢出阈值、稳定式和直接除法验证边界。
- [AscExp](../reg/arithmetic_compute/asc_exp.md)（`same_topic`）：AscExp 与《AscExp》的实质衔接是：这些入口都执行逐元素自然指数；高阶/Memory/Reg/C Vector 对应接口给出不同数据承载方式，FTZ 与 sigmoid 溢出卡直接验证次正规和大指数边界。
- [Exp](../../adv_api/math_compute/exp_interface/exp.md)（`same_topic`）：Exp 与《AscExp》的实质衔接是：这些卡直接给出 Exp 的高阶、基础、Reg 与 C 入口及其临时空间契约；所连排障卡均以 Exp 的溢出、下溢、FTZ 或 clamp 行为作为精度根因和修复对象。
<!-- cannbot:related:end -->
