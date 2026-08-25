---
type: API
title: L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍
description: 为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank
  Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/L1_L0A_B_memory_structure_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---


# L1/L0A/L0B内存结构简介

介绍Cube计算中L1 Buffer、L0A Buffer和L0B Buffer的内存结构和数据排布方式。L1 Buffer以NZ/ZN格式存储矩阵数据，L0A和L0B以Fractal格式存储，L0C以Fractal格式存储计算结果。

各Buffer的容量和访问特性因产品型号而异。理解内存结构对于正确配置LoadData参数和优化数据搬运策略至关重要。

<!-- cannbot:related:start -->
## 相关

- [Cube tile k/n 超 L1/L0 上限报 INVALID_TILE](../../../../../runbooks/compilation/cube_tile_k_n_l1_l0_invalid_tile.md)（`exemplifies`）：The INVALID_TILE runbook shows how exceeding L1/L0 tile capacity manifests at build time and how to clamp k/n to the memory limits.
- [L1/L0 tensor 须用 TPosition 构造非 SetAddr](../../../../../runbooks/compilation/l1_l0_tensor_tposition_setaddr.md)（`exemplifies`）：The runbook shows that L1/L0 tensors must encode their position in LocalTensor construction rather than attaching an address with SetAddr.
- [L1与L0数据搬运](../../data_move_guide/l1_l0_data_move.md)（`related`）：L1与L0数据搬运 与《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [LoadData](load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》具体提供“为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》明确提供“为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadDataWithTranspose](load_data_with_transpose.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》提供“为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [矩阵计算的搬入总体说明](../../cube_compute_tensor_api/cube_compute_load/overall_description.md)（`related`）：矩阵计算的搬入总体说明 与《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》的实质衔接是：Cube Load 总体说明用于选择 GM→L1 与 L1→各 L0/Bias/Fixpipe 通路；分形格式、缓存位置和搬入约束决定 Copy 路径。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
