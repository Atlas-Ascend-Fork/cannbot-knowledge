---
type: API
title: Muls（灵活标量位置）
description: 矢量元素与标量做乘法，支持标量在前或在后两种场景，标量可配置为LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Muls_flexible_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Muls（灵活标量位置）

双目矢量计算接口，矢量内每个元素与标量做乘法，支持标量在前或在后两种场景，标量可配置为 LocalTensor 单点元素。头文件为 basic_api/kernel_operator_vec_binary_scalar_intf.h。
通过 BinaryConfig 的 scalarTensorIndex 指定标量位置：0 表示左操作数，1 表示右操作数（默认）。支持 Tensor 前 n 个数据计算与高维切分计算两种模式，高维切分又分 mask 连续与逐 bit 模式。
支持 int16_t、half、bfloat16_t、int32_t、float 等数据类型，其中 complex32、int64_t、uint64_t、complex64 仅支持前 n 个数据计算接口。
约束：左右操作数必须有一个为矢量；LocalTensor 单点元素作为标量时 idx 需为编译期常量；源操作数为单点元素时不支持与目的操作数地址重叠。
针对 Ascend 950PR/950DT，该接口通过 VF 调用 Reg 矢量计算 API 实现兼容，高维切分计算占用 8KB Unified Buffer。仅 Ascend 950PR/950DT 支持。
