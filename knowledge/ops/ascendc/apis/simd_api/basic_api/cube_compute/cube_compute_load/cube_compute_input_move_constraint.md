---
type: API
title: 矩阵计算输入搬运约束
description: 具体可见表数据通路和存储层级。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/cube_compute_input_move_constraint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Cube计算输入搬运约束

描述Cube计算输入数据搬运的各种约束条件，涵盖GM到L1、L1到L0A/L0B、UB到L1等各通路的地址对齐、数据长度、格式转换、Batch搬运等约束。约束因数据类型、源/目的格式、产品型号而异。

关键约束包括：地址对齐要求（32B/64B等）、数据长度限制、格式转换支持矩阵、Batch搬运条件、Scale数据搬运约束等。开发者在调用LoadData/DataCopy接口前需确认满足相应约束。

<!-- cannbot:related:start -->
## 相关

- [BroadCastVecToMMISASI](broad_cast_vec_to_mm_isasi.md)（`related`）：广播搬入仍需满足 Cube 输入对齐和分形约束。
- [CopyL1ToL0ScaleB](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_scale_b.md)（`related`）：CopyL1ToL0ScaleB 是 MX Matmul 的 Scale 数据搬运，输入搬运约束专门列出 Scale 通路的对齐和格式限制，可用于验证 Layout 推导结果。
- [DataCopy](data_copy_gm_to_l1_highdim_split.md)（`related`）：高维切分 GM→L1 搬运的各维长度、stride 和分段必须满足 Cube 输入通路的地址对齐、数据长度及格式转换矩阵。
- [DataCopy](data_copy_l1_to_bias_table.md)（`related`）：DataCopy 与《矩阵计算输入搬运约束》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《矩阵计算输入搬运约束》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [LoadData](load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《矩阵计算输入搬运约束》具体提供“具体可见表数据通路和存储层级。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《矩阵计算输入搬运约束》明确提供“具体可见表数据通路和存储层级。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadDataWithTranspose](load_data_with_transpose.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《矩阵计算输入搬运约束》提供“具体可见表数据通路和存储层级。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [CopyGmToL1](../../cube_compute_tensor_api/cube_compute_load/copy_gm_to_l1.md)（`same_topic`）：矩阵计算输入搬运约束 与《CopyGmToL1》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [CopyL1ToL0A](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_a.md)（`same_topic`）：矩阵计算输入搬运约束 与《CopyL1ToL0A》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [CopyL1ToL0B](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_b.md)（`same_topic`）：矩阵计算输入搬运约束 与《CopyL1ToL0B》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [DataCopyPad（GMToL1非对齐数据搬运）](data_copy_pad_gm_to_l1.md)（`same_topic`）：矩阵计算输入搬运约束 与《DataCopyPad（GMToL1非对齐数据搬运）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [DataCopyPad（UBToL1非对齐数据搬运）](data_copy_pad_ub_to_l1.md)（`same_topic`）：矩阵计算输入搬运约束 与《DataCopyPad（UBToL1非对齐数据搬运）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍](l1_l0_a_b_memory_structure_intro.md)（`same_topic`）：矩阵计算输入搬运约束 与《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [L1与L0数据搬运](../../data_move_guide/l1_l0_data_move.md)（`same_topic`）：矩阵计算输入搬运约束 与《L1与L0数据搬运》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [LoadData](load_data_2_d_mx.md)（`same_topic`）：矩阵计算输入搬运约束 与《LoadData》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [LoadDataWithSparse](load_data_with_sparse.md)（`same_topic`）：矩阵计算输入搬运约束 与《LoadDataWithSparse》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [LoadDataWithStride](load_data_with_stride.md)（`same_topic`）：矩阵计算输入搬运约束 与《LoadDataWithStride》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [数据搬运概念（概述）](../../data_move_guide/overview/data_move_concept.md)（`same_topic`）：矩阵计算输入搬运约束 与《数据搬运概念（概述）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：矩阵计算输入搬运约束 与《普通矩阵计算流程（概述）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算输入搬运约束》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算的搬入](cube_compute_load.md)（`same_topic`）：矩阵计算输入搬运约束 与《矩阵计算的搬入》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
- [矩阵计算的搬入总体说明](../../cube_compute_tensor_api/cube_compute_load/overall_description.md)（`same_topic`）：矩阵计算输入搬运约束 与《矩阵计算的搬入总体说明》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
