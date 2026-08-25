---
type: API
title: MmadWithSparse
description: 4:2结构化稀疏矩阵乘加接口，左矩阵为稀疏矩阵，右矩阵为稠密矩阵，完成稀疏矩阵的稠密化与乘加计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/MmadWithSparse.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# MmadWithSparse

4:2 结构化稀疏矩阵乘加接口，实现 C=A×B+C。左矩阵 A 为稀疏矩阵（L0A，M×K，Zz，int8_t），右矩阵 B 为经 4:2 稀疏过滤后的稠密矩阵（L0B，K/2×N，Zn，int8_t），结果 C 位于 L0C（M×N，Nz，int32_t）。头文件 `basic_api/kernel_operator_mm_intf.h`。

B 矩阵需通过 LoadDataWithSparse 载入并同时加载索引矩阵（uint8，分形(32,16)，每个元素含 4 个 uint2 索引）。计算时根据索引矩阵对 A 矩阵进行 4 选 2 稠密化，再执行普通 Mmad 运算。索引矩阵布局与 B 相同，存储于 Cube 内置专用 buffer。

参数：dst（L0C/CO1，1024B 对齐）、fm（L0A/A2，512B 对齐）、filter（L0B/B2，512B 对齐）、mmadParams 为 MmadParams。仅 Atlas A2/A3 训练推理系列产品支持。

<!-- cannbot:related:start -->
## 相关

- [4:2稀疏矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/4_2_sparse_matmul.md)（`explains`）：4:2稀疏矩阵乘 与《MmadWithSparse》的实质衔接是：4:2 稀疏 Matmul 实现直接依赖 SetSparse/SetSparseIndex 和 sparse Mmad 两层接口传递稠密化索引。
- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《MmadWithSparse》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [LoadDataWithSparse](../cube_compute_load/load_data_with_sparse.md)（`related`）：LoadDataWithSparse 把稀疏 B 矩阵及索引搬入 L0B，正是 MmadWithSparse 随后进行稀疏矩阵乘所消费的输入。
- [Mmad](mmad.md)（`related`）：MmadWithSparse 在左矩阵为 4:2 结构化稀疏时替代普通 Mmad，并额外消费稀疏索引，属于输入契约驱动的直接选型。
- [AscMmadSparse](../../../c_api/cube_compute/asc_mmad_sparse.md)（`same_topic`）：AscMmadSparse说明完成稀疏矩阵乘加计算，左矩阵A为稠密矩阵、右矩阵B为稀疏矩阵，B在输入前按稠密算法完成稠密化并生成索引矩阵用于A的稠密化。
- [SetSparse](../../../adv_api/cube_compute/matmul_tiling/set_sparse.md)（`same_topic`）：SetSparse说明设置Matmul的使用场景是否为Sparse Matmul场景。
- [SetSparseIndex](../../../adv_api/cube_compute/matmul_kernel/set_sparse_index.md)（`same_topic`）：SetSparseIndex说明设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。
<!-- cannbot:related:end -->
