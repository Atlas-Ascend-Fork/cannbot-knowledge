---
type: API
title: AscDiv
description: 根据mask对源操作数src0、src1按元素求商，将结果写入目的操作数dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/arithmetic_compute/asc_div.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscDiv

该接口根据mask，对源操作数src0、src1进行按元素求商操作，将结果写入目的操作数dst。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

- 注意除零错误，结果

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reciprocal 低精度致 sigmoid 比对失败](../../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《AscDiv》说明根据mask对源操作数src0、src1按元素求商，将结果写入目的操作数dst。。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [AscDiv](../../vector_compute/asc_div.md)（`same_topic`）：AscDiv 与《AscDiv》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
- [Div](../../../basic_api/memory_vector_compute/basic_arithmetic/div.md)（`same_topic`）：Div 与《AscDiv》的实质衔接是：这些入口执行同一逐元素除法语义，分别落在 memory、Reg、C Reg/C Vector 层；灵活标量 Divs 补充标量位于任一操作数时的调用选择。
- [Div](../../../basic_api/reg_vector_compute/basic_arithmetic/div.md)（`same_topic`）：Div 与《AscDiv》的实质衔接是：这些入口执行相同逐元素除法，分别位于 Reg、Memory、C Reg/C Vector 层；Divs 补充一个操作数为标量时的调用契约。
<!-- cannbot:related:end -->
