---
type: Guide
title: 4:2稀疏矩阵乘
description: 对稀疏矩阵B进行4:2稠密化后调用Matmul API完成矩阵乘，跳过零元素以减少内存占用和计算量。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/4_2_sparse_matmul.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 4:2稀疏矩阵乘

## 功能介绍
4:2稀疏矩阵乘，又称Sparse Matmul。该场景下输入的原始左矩阵A、右矩阵B为稀疏矩阵，稀疏矩阵B中每4个元素中至少有2个为零元素；在进行Matmul计算前，用户需要自行对B矩阵进行4：2稠密化，即基于原始稀疏矩阵B在每4个元素中过滤掉2个零元素，使B矩阵稠密化为稠密矩阵；Sparse Matmul场景调用Matmul API完成A矩阵与4:2稠密化后的B矩阵的矩阵乘计算。Sparse Matmul可以跳过稀疏矩阵B中的零元素，仅对非零元素进行数据搬运存储和计算，从而减少矩阵乘计算时的内存占用和计算量，提升性能。
## 实现流程
1.  数据预处理
在计算前的数据准备阶段，用户自行对原始为稀疏矩阵的B矩阵完成稠密化，稠密过程请参考稠密算法说明。稠密化过程结束后，得到4:2稠密化后的右矩阵B和索引矩阵index，稠密化后的右矩阵B和索引矩阵index将作为Sparse Matmul场景的计算输入。
稠密化过程对于稀疏矩阵B的每4个元素，在索引矩阵index中生成2个2位索引，每个索引分别指向对应非零元素的相对位置，具体规则可参考稠密算法说明。稠密化过程生成的索引矩阵的数据类型为int2，索引矩阵在加载入Matmul前，需要拼成int8的数据类型。索引矩阵在一个int8的地址中的排布是逆序排布的，例如：索引矩阵1 2 0 1 0 2 1 0，在地址中的排布为1 0 2 1 0 1 2 0，其中1 0 2 1（对应索引矩阵前四位1 2 0 1）为一个int8，0 1 2 0（对应索引矩阵后四位0 2 1 0）为一个int8。
2.  设置Sparse Matmul场景
在Host侧，获取Tiling前需要通过SetSparse接口设置Sparse Matmul场景。
3.  创建Matmul对象
在Kernel侧创建Matmul对象时，通过MatmulType定义A、C、Bias的参数类型信息，包括：内存逻辑位置、数据格式、数据类型。通过SparseMatmulType类型定义B矩阵的参数类型，包括：B矩阵的内存逻辑位置、索引矩阵的内存逻辑位置、数据格式、数据类型等。
4.  设置索引矩阵
通过SetSparseIndex接口传入稠密化过程中生成的索引矩阵。
5.  完成矩阵乘操作
在Kernel侧，基于步骤4加载的索引矩阵，完成矩阵乘操作。Matmul API内部完成对A矩阵的稠密化，即根据索引矩阵从A矩阵的每4个元素中，选择2个对应位置元素参与计算。
## 参数说明
SparseMatmulType类型参数说明
## 使用场景
左矩阵A为稀疏矩阵、右矩阵B为4:2稠密化后的矩阵的Matmul计算场景。
## 约束说明
-   该场景仅支持MDL模板下的纯Cube模式（只有矩阵计算）。
-   通过SetSparseIndex接口传入的索引矩阵只支持int8数据类型和NZ数据排布格式。
-   原始稀疏矩阵B中每4个元素中应保证最多2个非零元素（即最少2个零元素），如果存在3个或更多非零元素，则仅使用前2个非零元素。
-   M、K、N中的任意一个值不能为0。

<!-- cannbot:related:start -->
## 相关

- [SetSparse](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_sparse.md)（`explains`）：在Host侧，获取Tiling前需要通过SetSparse接口设置Sparse Matmul场景。；设置Matmul的使用场景是否为Sparse Matmul场景。。实践指南明确在获取 Tiling 前调用 SetSparse，把接口的布尔场景开关放入 Host 侧稀疏 Matmul 配置顺序。
- [SetSparseIndex](../../../../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_sparse_index.md)（`explains`）：通过SetSparseIndex接口传入稠密化过程中生成的索引矩阵。；设置稀疏矩阵稠密化过程生成的索引矩阵。 索引矩阵在稠密化中的作用请参考MmadWithSparse。。实践指南把 SetSparseIndex 放到 4:2 稀疏 Matmul 的索引生成与传入步骤中，说明该接口在完整 Kernel 流程中的使用位置。
<!-- cannbot:related:end -->
