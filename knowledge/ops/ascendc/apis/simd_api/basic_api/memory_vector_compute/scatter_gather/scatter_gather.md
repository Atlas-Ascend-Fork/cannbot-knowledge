---
type: API
title: 离散与聚合
description: Memory矢量计算离散与聚合接口索引页，包含Gather、Gatherb(ISASI)与Scatter(ISASI)。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/scatter_gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 离散与聚合

Memory矢量计算离散与聚合接口索引页，包含Gather、Gatherb(ISASI)与Scatter(ISASI)。

Gather接口接受输入张量（src）、地址偏移张量（srcOffset）和基地址（srcBaseAddr），根据基地址和地址偏移量确定输入张量的索引，将输入张量中对应元素收集到结果张量（dst）中。 接口支持使用前n个数据计算和高维切分计算的方式，前n个数据计算原理和参考伪代码如下： 完整示例请参考：Gather真值计算。

本接口组包含 Gather, Gatherb(ISASI), Scatter(ISASI)。

本接口属于 UB 矢量计算 Scatter/Gather 接口。

约束：操作数地址对齐要求请参见Unified Buffer地址对齐约束。；不支持源操作数与目的操作数使用同一块内存地址。；srcOffset的取值要求如下：；取值应保证src元素类型位宽对齐。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
