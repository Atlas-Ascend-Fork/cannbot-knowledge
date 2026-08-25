---
type: API
title: AscDiv
description: asc_div（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_div.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscDiv

执行矢量除法运算。计算公式如下：
函数原型：void asc_div(__ubuf__ half* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。；注意除0错误。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Reciprocal 低精度致 sigmoid 比对失败](../../../../runbooks/precision/reciprocal_sigmoid.md)（`exemplifies`）：《Reciprocal 低精度致 sigmoid 比对失败》说明AscendC::Reciprocal 为低精度查表近似指令（相对误差约 1e-3），sigmoid 的 1/(1+exp(-x)) 用其求倒数会让 verify_result.py 报 max_diff≈0.00179、16384/16384 全 mismatch；判别方法：把最后一步 Reciprocal 换成 Duplicate+Div 高精度除法后 max_diff 降为 0，即可单点归因到 Reciprocal 的低精度近似。；《AscDiv》说明asc_div（矢量计算）。二者在该失败由Reciprocal近似误差进入sigmoid末步；高精度Div替换及Exp溢出/FTZ变体用于单点归因上存在可执行的直接衔接。
- [arch35 后端 64 位 div/mod 报 bitwidth>32](../../../../runbooks/compilation/arch35_64_div_mod_bitwidth_32.md)（`exemplifies`）：AscDiv 与《arch35 后端 64 位 div/mod 报 bitwidth>32》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
- [AscDiv](../reg/arithmetic_compute/asc_div.md)（`same_topic`）：AscDiv 与《AscDiv》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
- [Div](../../basic_api/memory_vector_compute/basic_arithmetic/div.md)（`same_topic`）：AscDiv 与《Div》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
- [Div](../../basic_api/reg_vector_compute/basic_arithmetic/div.md)（`same_topic`）：AscDiv 与《Div》的实质衔接是：这些是 AscDiv 在 C Vector、C Reg、memory 与 Reg 执行层的同一逐元素除法；64 位 div/mod 后端错误卡限定不可扩展的数据位宽。
<!-- cannbot:related:end -->
