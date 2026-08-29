---
type: API
title: CopyL1ToBiasTable
description: 通过Tensor API的Copy接口将L1 Buffer中的bias数据搬运到BiasTable Buffer，作为Mmad计算的bias输入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToBiasTable.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到BiasTable数据搬运）

通过统一Copy接口将L1 Buffer数据搬运到BiasTable，用于矩阵计算的bias输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [L1与BiasTable Buffer数据搬运](../../data_move_guide/l1_bias_table_data_move.md)（`related`）：通过统一Copy接口将L1 Buffer数据搬运到BiasTable，用于矩阵计算的bias输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。；DataCopy 实现 L1 Buffer 到 BiasTable Buffer 的连续数据搬运，格式和内容保持不变。用于将矩阵计算的 bias 参数从 L1 搬运至 BiasTable Buffer。BiasTable Buffer 地址需 64B 对齐，L1 Buffer 地址需 32B 对齐。；指南为该 Copy 接口补齐两端地址对齐和连续搬运条件。
<!-- cannbot:related:end -->
