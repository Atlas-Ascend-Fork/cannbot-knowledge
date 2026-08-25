---
type: API
title: 数据通路（概述）
description: AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/data_path.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 数据通路（概述）

AI Core 含 Cube/Vector/Scalar 计算单元和分层存储：GM→L1 Buffer→L0A/L0B/L0C Buffer→UB→BiasTable/Fixpipe Buffer。搬运引擎：MTE2（GM→Local）、MTE3（Local→GM）、MTE1（L1→L0）、FixPipe（L0C→GM 带随路量化/激活）。同一物理内存可映射多个 TPosition（如 UB 映射 VECIN/VECCALC/VECOUT）。

NPU 架构版本 3510（950）变化：新增 L0C→UB 和 UB→L1 通路；删除 GM→L0A/L0B 和 L1→GM 直连通路。

<!-- cannbot:related:start -->
## 相关

- [GmUbDataMove](../gm_ub_data_move.md)（`related`）：GmUbDataMove 与《数据通路（概述）》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [L1OrL0CUbDataMove](../l1_or_l0_c_ub_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《数据通路（概述）》说明AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [L1与BiasTable Buffer数据搬运](../l1_bias_table_data_move.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《数据通路（概述）》说明AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [数据搬运导览](../data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《数据通路（概述）》说明AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [数据搬运概念（概述）](data_move_concept.md)（`same_topic`）：数据路径说明给出 GM、UB、L1、L0 与 Fixpipe 的可达通路，是按搬运概念选 API 的第一层约束。
- [普通矩阵计算流程（概述）](../../cube_compute/overview/cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《数据通路（概述）》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [概览](overview.md)（`same_topic`）：“数据通路（概述）”处理AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：；“概览”明确数据搬运导览，介绍AI Core分层存储架构中的数据通路、TPosition映射、搬运功能分类及通用约束等核心概念。。实质衔接：数据搬运概览把这里的 GM/L1/L0/UB/Fixpipe 硬件通路组织成入口，正文用于解释路径选择，而不是连接每个具体搬运成员。
<!-- cannbot:related:end -->
