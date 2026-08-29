---
type: API
title: LoadDataWithSparse
description: 从L1 Buffer搬运稠密权重矩阵到L0B Buffer，同时搬运索引矩阵到专用buffer空间，供后续MmadWithSparse接口读取。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadDataWithSparse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# LoadDataWithSparse

将稀疏矩阵数据从L1 Buffer搬运到L0A或L0B Buffer，支持稀疏数据的压缩搬运。在搬运过程中解压稀疏数据，恢复为完整的Fractal格式存储在L0A/L0B中。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、loadDataParams、sparseParams（含稀疏格式信息）。约束：遵循Cube计算地址对齐和稀疏数据格式约束。

<!-- cannbot:related:start -->
## 相关

- [MmadWithSparse](../mmad_compute/mmad_with_sparse.md)（`related`）：将稀疏矩阵数据从L1 Buffer搬运到L0A或L0B Buffer，支持稀疏数据的压缩搬运。；B 矩阵需通过 LoadDataWithSparse 载入并同时加载索引矩阵（uint8，分形(32,16)，每个元素含 4 个 uint2 索引）。。前者提供稀疏数据从 L1 到 L0A/L0B 的解压搬运，后者把 LoadDataWithSparse 明确规定为 MmadWithSparse 的 B 矩阵与索引矩阵装载前置，组成稀疏矩阵乘的直接数据通路。
<!-- cannbot:related:end -->
