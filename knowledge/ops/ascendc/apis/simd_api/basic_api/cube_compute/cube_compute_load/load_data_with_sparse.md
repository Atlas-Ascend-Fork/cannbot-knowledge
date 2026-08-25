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

- [AscMmadSparse](../../../c_api/cube_compute/asc_mmad_sparse.md)（`related`）：LoadDataWithSparse 把稠密化权重与索引搬入 L0B/专用 buffer，随后由 AscMmadSparse 执行矩阵乘。
- [MmadWithSparse](../mmad_compute/mmad_with_sparse.md)（`related`）：LoadDataWithSparse 把稀疏 B 矩阵及索引搬入 L0B，正是 MmadWithSparse 随后进行稀疏矩阵乘所消费的输入。
- [SetSparseIndex](../../../adv_api/cube_compute/matmul_kernel/set_sparse_index.md)（`same_topic`）：LoadDataWithSparse说明从L1 Buffer搬运稠密权重矩阵到L0B Buffer，同时搬运索引矩阵到专用buffer空间，供后续MmadWithSparse接口读取。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《LoadDataWithSparse》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
