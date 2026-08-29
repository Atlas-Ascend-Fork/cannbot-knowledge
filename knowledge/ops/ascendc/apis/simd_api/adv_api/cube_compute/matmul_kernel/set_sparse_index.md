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

- [4:2稀疏矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/4_2_sparse_matmul.md)（`explains`）：通过SetSparseIndex接口传入稠密化过程中生成的索引矩阵。；设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。。实践指南把 SetSparseIndex 放到 4:2 稀疏 Matmul 的索引生成与传入步骤中，说明该接口在完整 Kernel 流程中的使用位置。
- [MmadWithSparse](../../../basic_api/cube_compute/mmad_compute/mmad_with_sparse.md)（`related`）：设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。；4:2 结构化稀疏矩阵乘加接口，实现 C=A×B+C。左矩阵 A 为稀疏矩阵（L0A，M×K，Zz，int8_t），右矩阵 B 为经 4:2 稀疏过滤后的稠密矩阵（L0B，K/2×N，Zn，int8_t），结果 C 位于 L0C（M×N，Nz，int32_t）。头文件 `basic_api/kernel_operator_mm_intf.h`。；SetSparseIndex 提供 MmadWithSparse 稠密化阶段消费的索引矩阵，连接索引配置与 4:2 稀疏矩阵乘加。
<!-- cannbot:related:end -->
