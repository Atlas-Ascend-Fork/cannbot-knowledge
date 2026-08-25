---
type: API
title: 矩阵计算的搬入总体说明
description: 矩阵计算的搬入接口主要实现Global Memory到L1 Buffer和L1 Buffer到L0A Buffer/L0B Buffer/L0ScaleA
  Buffer/L0ScaleB Buffer/BiasTable Buffer/Fixpipe Buffer的数据高效传输。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/overall_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Cube Load总体说明

Cube计算Load操作通过统一Copy接口实现不同存储层次间的数据搬运，搬运参数由Tensor Layout自动推导。支持GM到L1、L1到L0A/L0B/L0ScaleA/L0ScaleB/BiasTable/Fixpipe等通路。

各通路支持的数据格式转换场景因源/目的位置和数据类型而异，包括连续搬运、格式转换（ND/NZ/ZN/Fractal等）、Batch多矩阵搬运、Scale数据搬运、卷积特征图搬运等。

<!-- cannbot:related:start -->
## 相关

- [Cube计算(ISASI)总体说明](../../cube_compute/cube_compute_load/overall_description.md)（`related`）：矩阵计算的搬入总体说明 与《Cube计算(ISASI)总体说明》的实质衔接是：Cube Load 总体说明用于选择 GM→L1 与 L1→各 L0/Bias/Fixpipe 通路；分形格式、缓存位置和搬入约束决定 Copy 路径。
- [DataCopy](../../cube_compute/cube_compute_load/data_copy_l1_to_bias_table.md)（`related`）：DataCopy 与《矩阵计算的搬入总体说明》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍](../../cube_compute/cube_compute_load/l1_l0_a_b_memory_structure_intro.md)（`related`）：矩阵计算的搬入总体说明 与《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》的实质衔接是：Cube Load 总体说明用于选择 GM→L1 与 L1→各 L0/Bias/Fixpipe 通路；分形格式、缓存位置和搬入约束决定 Copy 路径。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`related`）：矩阵计算的搬入总体说明 与《矩阵计算分形介绍》的实质衔接是：Cube Load 总体说明用于选择 GM→L1 与 L1→各 L0/Bias/Fixpipe 通路；分形格式、缓存位置和搬入约束决定 Copy 路径。
- [CopyL1ToL0B](copy_l1_to_l0_b.md)（`same_topic`）：总页给出 L1→L0B 的格式和对齐约束。
- [矩阵计算输入搬运约束](../../cube_compute/cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《矩阵计算的搬入总体说明》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
