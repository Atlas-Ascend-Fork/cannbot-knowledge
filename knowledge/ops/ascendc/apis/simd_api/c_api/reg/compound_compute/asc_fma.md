---
type: API
title: AscFma
description: 完成src0与src1逐元素相乘再加dst的融合乘加运算，根据mask将结果写回dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compound_compute/asc_fma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscFma

完成src0与src1逐元素相乘再加dst的融合乘加运算，根据mask将计算结果写回dst。

参数：dst(输入/输出): 目的操作数（矢量数据寄存器）。；src0(输入): 源操作数（矢量数据寄存器）。；src1(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、half。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：该卡用抵消输入证明 FMA 一次舍入与 Mul+Add 两次舍入可相差 ULP，提供选择 asc_fma 或分离运算的验证方法。
- [AscMadd](asc_madd.md)（`related`）：asc_madd 是非融合/不同累加语义的相邻复合操作；精度需要逐步舍入时不能与 FMA 混用。
- [AscFma](../../vector_compute/asc_fma.md)（`same_topic`）：AscFma 的核心契约是“按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，”；AscFma 补充“完成src0与src1逐元素相乘再加dst的融合乘加运算，根据mask将结果写回dst”。
- [Fma](../../../adv_api/math_compute/fma_interface/fma.md)（`same_topic`）：高阶 Fma 在 LocalTensor 上封装同一融合乘加语义，连接 C Reg 实现与 Tensor API。
- [Fma接口](../../../adv_api/math_compute/fma_interface/fma_interface.md)（`same_topic`）：Fma接口 与《AscFma》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
<!-- cannbot:related:end -->
