---
type: API
title: Mull
description: 双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mull_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Mull

双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。

本接口组包含 地址对齐约束, 地址对齐约束, 连续计算, 通用地址对齐约束, 通用地址重叠约束。

本接口属于 UB 矢量计算基础算术接口，操作 Unified Buffer 上的 LocalTensor 数据。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscMull](../../../c_api/reg/arithmetic_compute/asc_mull.md)（`same_topic`）：《AscMull》说明根据mask对源操作数src0、src1按元素相乘，将乘法结果的低位部分写入dst0，高位（溢出）部分写入dst1。；《Mull》说明双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。。二者在AscMull同时产生乘积高低位，只有同样保留溢出位的Mull接口可视为同一运算合同上存在可执行的直接衔接。
- [Mull](../../reg_vector_compute/basic_arithmetic/mull.md)（`same_topic`）：《Mull》说明根据mask对源操作数srcReg0、srcReg1按元素相乘，将乘法结果的低位部分写入dstReg0，溢出（高位）部分写入dstReg1。；《Mull》说明双目矢量计算接口，对前count个数据按元素相乘，结果写入dst0，溢出部分写入dst1。。二者在Mull在Memory、Reg C接口中都产生双字宽乘积，普通Mul用于核对仅保留原字宽的不同结果合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
