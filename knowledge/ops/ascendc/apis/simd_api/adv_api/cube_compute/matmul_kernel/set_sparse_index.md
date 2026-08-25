---
type: API
title: SetSparseIndex
description: 设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSparseIndex.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# SetSparseIndex

设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。

函数原型：__aicore__ inline void SetSparseIndex(const GlobalTensor<uint8_t>& indexGlobal)

参数：
- indexGlobal（输入）：索引矩阵在Global Memory上的首地址，类型为GlobalTensor。 索引矩阵的数据类型为uint2，需要由用户拼成uint8的数据类型，再传入本接口。索引矩阵的Format格式只支持NZ格式。

约束：
- 索引矩阵的Format格式要求为NZ格式。
- 本接口仅支持在纯Cube模式（只有矩阵计算）且MDL模板的场景使用。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [4:2稀疏矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/4_2_sparse_matmul.md)（`explains`）：4:2稀疏矩阵乘 与《SetSparseIndex》的实质衔接是：4:2 稀疏 Matmul 实现直接依赖 SetSparse/SetSparseIndex 和 sparse Mmad 两层接口传递稠密化索引。
- [AscMmadSparse](../../../c_api/cube_compute/asc_mmad_sparse.md)（`related`）：AscMmadSparse 消费稀疏权重的索引矩阵，SetSparseIndex 负责在 Matmul 对象中绑定该索引。
- [LoadDataWithSparse](../../../basic_api/cube_compute/cube_compute_load/load_data_with_sparse.md)（`same_topic`）：LoadDataWithSparse说明从L1 Buffer搬运稠密权重矩阵到L0B Buffer，同时搬运索引矩阵到专用buffer空间，供后续MmadWithSparse接口读取。
- [MmadWithSparse](../../../basic_api/cube_compute/mmad_compute/mmad_with_sparse.md)（`same_topic`）：SetSparseIndex说明设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。
- [SetSparse](../matmul_tiling/set_sparse.md)（`same_topic`）：SetSparse说明设置Matmul的使用场景是否为Sparse Matmul场景。
<!-- cannbot:related:end -->
