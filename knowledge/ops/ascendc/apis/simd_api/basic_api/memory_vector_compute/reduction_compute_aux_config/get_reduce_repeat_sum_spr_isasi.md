---
type: API
title: GetReduceRepeatSumSpr
description: 获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute_aux_config/GetReduceRepeatSumSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetReduceRepeatSumSpr

获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储。

ReduceSum接口对所有输入数据进行求和，计算过程如下。 图1 ReduceSum计算示意图

本接口组包含 ReduceSum。

本接口属于 UB 矢量计算归约接口。

约束：源操作数及sharedTmpBuffer的地址对齐约束请参考通用地址对齐约束，起始地址需要32字节对齐；目的操作数的起始地址对齐约束请参考ReduceRepeat-表3。；操作数地址重叠约束请参考通用地址重叠约束。；需要使用sharedTmpBuffer的情况下，支持dst与sharedTmpBuffer地址重叠（通常情况下dst比sharedTmpBuffer所需的空间要小），此时sharedTmpBuffer必须满足所需空间要求，详情请参考关键特性说明。；当参数count或repeatTime取值为0时，该接口的行为如下：

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ReduceSum](../reduction_compute/reduce_sum.md)（`related`）：对所有输入数据进行求和操作。；获取ReduceSum接口前n个数据连续计算的结果，以全局变量形式存储。。ReduceSum 执行求和，辅助接口读取其前 n 个连续数据计算结果并以全局变量暴露，形成计算到结果检查的配套链。
<!-- cannbot:related:end -->
