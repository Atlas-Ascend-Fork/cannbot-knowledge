---
type: API
title: AscMulAdd
description: 执行矢量的乘加运算。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mul_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscMulAdd

执行矢量的乘加运算。计算公式如下：
函数原型：void asc_mul_add(__ubuf__ half* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：该卡实测说明融合乘加单次舍入与分离 Mul+Add 双舍入可差 1 ULP，直接用于判断 AscMulAdd 类融合结果与 golden 的精度偏差。
- [MulAddDst](../../basic_api/memory_vector_compute/composite_compute/mul_add_dst.md)（`related`）：MulAddDst 明确给出 dst=src0*src1+dst 的累加语义，是理解 AscMulAdd 目的缓冲既作输入又作输出的对应接口。
- [AscMulAddRelu](asc_mul_add_relu.md)（`same_topic`）：AscMulAddRelu 与《AscMulAdd》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [MulAddDst](../../basic_api/reg_vector_compute/composite_compute/mul_add_dst.md)（`same_topic`）：AscMulAdd说明执行矢量的乘加运算。
<!-- cannbot:related:end -->
