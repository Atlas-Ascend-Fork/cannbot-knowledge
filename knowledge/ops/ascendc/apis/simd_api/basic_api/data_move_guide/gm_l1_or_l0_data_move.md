---
type: API
title: GmL1OrL0DataMove
description: 提供Global Memory与L1 Buffer及L0 Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及矩阵计算结果搬出等场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/GM_L1_or_L0_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GmL1OrL0DataMove

Global Memory 与 L1 Buffer/L0 Buffer 间数据搬运接口概述。GM↔L1 支持 DataCopy（连续/高维切分/ND2NZ/DN2NZ 随路转换）、DataCopyPad（非对齐）、LoadData（2D/2DV2 矩阵搬运）。GM→L0A/L0B 支持 LoadData（2D 分形搬运）。L0C→GM 支持 DataCopy 和 Fixpipe（随路量化/ReLU/格式转换）。DataBlock（32B）为基本寻址粒度，count×sizeof(T) 须 32B 对齐。具体接口详见 cube_compute_ISASI 章节。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《GmL1OrL0DataMove》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [中级性能优化](../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《GmL1OrL0DataMove》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [L1与L0数据搬运](l1_l0_data_move.md)（`related`）：L1与L0数据搬运 与《GmL1OrL0DataMove》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [数据搬运导览](data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《GmL1OrL0DataMove》说明提供Global Memory与L1 Buffer及L0 Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及矩阵计算结果搬出等场景。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
<!-- cannbot:related:end -->
