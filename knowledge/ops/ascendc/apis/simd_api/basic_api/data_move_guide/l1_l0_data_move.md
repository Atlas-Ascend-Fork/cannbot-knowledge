---
type: API
title: L1与L0数据搬运
description: L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_L0_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1与L0数据搬运

L1 Buffer 与 L0 Buffer 间数据搬运接口概述。L1→L0A/L0B 支持 LoadData（2D 矩阵搬运/卷积数据搬运/BitMode/MX）、LoadDataWithTranspose（转置搬运）、LoadDataWithSparse（稀疏搬运）。L0C→L1 支持 DataCopy 和 Fixpipe（随路量化/ReLU）。L1→BiasTable/Fixpipe 支持参数搬运。LoadData 以 512B 分形为单位，L0A/L0B 地址需 512B 对齐。具体接口详见 cube_compute_ISASI 章节。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：L1与L0数据搬运 与《Cube矩阵计算编程》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [中级性能优化](../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《L1与L0数据搬运》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [Cube计算(ISASI)总体说明](../cube_compute/cube_compute_load/overall_description.md)（`related`）：L1与L0数据搬运 与《Cube计算(ISASI)总体说明》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [GmL1OrL0DataMove](gm_l1_or_l0_data_move.md)（`related`）：L1与L0数据搬运 与《GmL1OrL0DataMove》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍](../cube_compute/cube_compute_load/l1_l0_a_b_memory_structure_intro.md)（`related`）：L1与L0数据搬运 与《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [L1OrL0CUbDataMove](l1_or_l0_c_ub_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《L1与L0数据搬运》说明L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [LoadDataWithTranspose](../cube_compute/cube_compute_load/load_data_with_transpose.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《L1与L0数据搬运》提供“L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [数据搬运导览](data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《L1与L0数据搬运》说明L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [普通矩阵计算流程（概述）](../cube_compute/overview/cube_compute_flow.md)（`related`）：L1与L0数据搬运 与《普通矩阵计算流程（概述）》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [矩阵计算输入搬运约束](../cube_compute/cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《L1与L0数据搬运》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
