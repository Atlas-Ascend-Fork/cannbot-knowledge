---
type: API
title: BilinearInterpolation
description: 双目矢量计算接口，通过水平+垂直双层循环完成乘累加，适用于非规则数据访问+权重乘加场景。软仿接口。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/BilinearInterpolation_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# BilinearInterpolation

双目矢量计算接口，通过水平迭代与垂直迭代的双层循环完成乘累加运算，适用于非规则数据访问加权重乘加的向量运算场景。头文件为 basic_api/kernel_operator_vec_bilinearinterpolation_intf.h。
该接口为兼容旧款产品而添加的软仿接口。计算流程分为四步：通过 Gatherb 按 DataBlock 粒度收集 src0 到临时 Buffer；通过 Brcb 广播填充 src1；通过 Mul 执行逐元素乘法；通过 Add 完成水平迭代累加输出到 dst。
支持 mask 连续模式与逐 bit 模式，通过 repeatMode 参数控制 src0 的每个 DataBlock 与 src1 的对应关系。
仅支持 half 数据类型。Ascend 950PR/950DT 无需临时空间，Atlas A2 与 A3 需分配 src0.GetSize()*32 + src1.GetSize()*32 字节。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品以及 Atlas 推理系列产品 AI Core。
