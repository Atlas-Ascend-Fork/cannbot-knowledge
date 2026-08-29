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

- [LoadDataWithSparse](../cube_compute_load/load_data_with_sparse.md)（`related`）：将稀疏矩阵数据从L1 Buffer搬运到L0A或L0B Buffer，支持稀疏数据的压缩搬运。；B 矩阵需通过 LoadDataWithSparse 载入并同时加载索引矩阵（uint8，分形(32,16)，每个元素含 4 个 uint2 索引）。。前者提供稀疏数据从 L1 到 L0A/L0B 的解压搬运，后者把 LoadDataWithSparse 明确规定为 MmadWithSparse 的 B 矩阵与索引矩阵装载前置，组成稀疏矩阵乘的直接数据通路。
- [SetSparseIndex](../../../adv_api/cube_compute/matmul_kernel/set_sparse_index.md)（`related`）：设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。；4:2 结构化稀疏矩阵乘加接口，实现 C=A×B+C。左矩阵 A 为稀疏矩阵（L0A，M×K，Zz，int8_t），右矩阵 B 为经 4:2 稀疏过滤后的稠密矩阵（L0B，K/2×N，Zn，int8_t），结果 C 位于 L0C（M×N，Nz，int32_t）。头文件 `basic_api/kernel_operator_mm_intf.h`。；SetSparseIndex 提供 MmadWithSparse 稠密化阶段消费的索引矩阵，连接索引配置与 4:2 稀疏矩阵乘加。
<!-- cannbot:related:end -->
