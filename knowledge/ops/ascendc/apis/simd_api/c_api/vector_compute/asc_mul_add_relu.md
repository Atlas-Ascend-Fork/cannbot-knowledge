---
type: API
title: AscMulAddRelu
description: 按元素将src0和dst相乘并加上src1，再进行Relu计算（结果和0对比取较大值），最终结果存放进dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_mul_add_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscMulAddRelu

按元素将src0和dst相乘并加上src1，再进行Relu计算（结果和0对比取较大值），最终结果存放进dst中。计算公式如下：
函数原型：void asc_mul_add_relu(__ubuf__ half* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差](../../../../runbooks/precision/muladddst_fma_golden_mul_add.md)（`exemplifies`）：AscMulAddRelu 与《MulAddDst FMA 单次舍入与 golden Mul+Add 双舍入偏差》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [AddRelu](../../basic_api/memory_vector_compute/composite_compute/add_relu.md)（`related`）：AscMulAddRelu 与《AddRelu》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [AscAddRelu](asc_add_relu.md)（`related`）：AscMulAddRelu 与《AscAddRelu》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [MulAddRelu](../../basic_api/memory_vector_compute/composite_compute/mul_add_relu.md)（`related`）：AscMulAddRelu 与《MulAddRelu》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [随路量化与随路ReLU场景组合](../../basic_api/cube_compute/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：AscMulAddRelu 与《随路量化与随路ReLU场景组合》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [AscMulAdd](asc_mul_add.md)（`same_topic`）：AscMulAddRelu 与《AscMulAdd》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
<!-- cannbot:related:end -->
