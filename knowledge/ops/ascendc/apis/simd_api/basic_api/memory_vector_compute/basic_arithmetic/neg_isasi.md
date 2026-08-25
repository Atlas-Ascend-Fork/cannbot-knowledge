---
type: API
title: Neg
description: 单目矢量计算接口，对输入tensor按元素取相反数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Neg_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Neg

单目矢量计算接口，对输入 Tensor 按元素取相反数。头文件为 basic_api/kernel_operator_vec_binary_scalar_intf.h。
函数签名为 template <typename T> void Neg(const LocalTensor<T>& dst, const LocalTensor<T>& src, const uint32_t count)，参数 count 为参与计算的元素个数。
支持 Tensor 前 n 个数据计算模式，TPosition 支持 VECIN、VECCALC、VECOUT。
支持 int8_t、int16_t、half、int32_t、float、int64_t 数据类型。
约束：操作数地址对齐与重叠约束参考通用约束文档。
针对 Ascend 950PR/950DT，该接口为软仿接口，通过 VF 调用 Reg 矢量计算 API 实现兼容。仅 Ascend 950PR/950DT 支持。
