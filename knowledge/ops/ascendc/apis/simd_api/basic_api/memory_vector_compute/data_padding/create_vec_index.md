---
type: API
title: CreateVecIndex
description: 创建指定起始值的向量索引接口，支持前n个数据计算和高维切分计算两种方式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_padding/CreateVecIndex.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# CreateVecIndex

创建指定起始值的向量索引，用于 Gather、Scatter 等需要索引的操作。头文件为 basic_api/kernel_operator_vec_createvecindex_intf.h。
支持前 n 个数据计算与高维切分计算两种方式。前 n 个数据计算时，从 firstValue 开始按递增步长 1 生成 count 个索引值。
高维切分计算支持 mask 连续模式与逐 bit 模式，通过 dstBlkStride 与 dstRepStride 控制数据写入步长。
参数 firstValue 为索引起始值，数据类型需与 dst 中元素类型一致；dst 的 TPosition 支持 VECIN、VECCALC、VECOUT，起始地址需 32 字节对齐。
支持 Ascend 950PR/950DT、Atlas A2、Atlas A3、Atlas 200I/500 A2 推理产品以及 Atlas 推理系列产品 AI Core。

<!-- cannbot:related:start -->
## 相关

- [Gather](../scatter_gather/gather.md)（`related`）：CreateVecIndex 生成从 firstValue 递增的索引 Tensor，可直接作为 Gather 的索引输入。
- [Scatter](../scatter_gather/scatter_isasi.md)（`related`）：同一索引向量也可驱动 Scatter 写入，形成索引生产到离散存储的任务链。
<!-- cannbot:related:end -->
