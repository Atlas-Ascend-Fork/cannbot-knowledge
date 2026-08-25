---
type: API
title: AscFma
description: 按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_fma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscFma

按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，计算公式如下：
函数原型：void asc_fma(__ubuf__ half* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：AscFma 定义“按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，”；MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差 以“dav-3510 VF MulAddDst 走 FMA（a*b+c 无限精度后一次舍入），golden 的 Mul+Add 是两次独立舍入；当 addend 含 -round(a*b) 抵消项且 x==save_mean 时两者偏差 1 ULP 量级，须把 VF 改 Mul+LoadAlign(dst)+Add 分离舍入匹配 golden”给出可观测实例，可直接用于复现或验证该契约。
- [AscFma](../reg/compound_compute/asc_fma.md)（`same_topic`）：AscFma 的核心契约是“按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，”；AscFma 补充“完成src0与src1逐元素相乘再加dst的融合乘加运算，根据mask将结果写回dst”。
- [Fma](../../adv_api/math_compute/fma_interface/fma.md)（`same_topic`）：AscFma 的核心契约是“按元素将src0和src1相乘并和dst相加，将最终结果存放进dst中，”；Fma 补充“按元素计算两个输入相乘后与第三个输入相加的结果”。
- [Fma接口](../../adv_api/math_compute/fma_interface/fma_interface.md)（`same_topic`）：Fma接口 与《AscFma》的实质衔接是：Fma 接口页直接包含 Fma、最大最小空间和 factor 查询，C Reg/Vector 入口执行同一融合乘加；舍入案例说明 FMA 单次舍入不能拆成 Mul+Add。
<!-- cannbot:related:end -->
