---
type: API
title: 普通矩阵计算流程（概述）
description: Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/overview/cube_compute_flow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 普通矩阵计算流程（概述）

Ascend C 矩阵计算编程模型包含三类流程。普通矩阵计算：DataCopy（GM→L1）搬运 A/B 矩阵和 Bias/量化参数 → LoadData（L1→L0A/L0B）加载计算数据 → Mmad（L0A/L0B→L0C）执行矩阵乘加 → Fixpipe（L0C→GM）搬出并执行随路量化/ReLU。

Mx 矩阵计算（仅 950）：额外搬运 scaleA/scaleB 系数矩阵，通过 LoadData（MX）加载到 L0A_MX/L0B_MX Buffer，MmadMx 执行带量化系数的矩阵乘，Fixpipe 搬出。

4 选 2 稀疏矩阵计算（仅 a2/a3）：离线生成稠密矩阵 B 和索引矩阵，LoadDataWithSparse 加载 B 和索引到 L0B/IDX Buffer，MmadWithSparse 根据 4 选 2 索引对 A 稀疏化后执行矩阵乘加，Fixpipe 搬出。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《普通矩阵计算流程（概述）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《普通矩阵计算流程（概述）》说明Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《普通矩阵计算流程（概述）》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [L1与L0数据搬运](../../data_move_guide/l1_l0_data_move.md)（`related`）：L1与L0数据搬运 与《普通矩阵计算流程（概述）》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [矩阵计算（ISASI）](../cube_compute_overview.md)（`related`）：总览列出接口，而 CubeComputeFlow 明确把搬入、Mmad、搬出和辅助配置放入一条执行链，可用于从接口清单推导正确调用顺序。
- [LoadData](../cube_compute_load/load_data_2_d.md)（`same_topic`）：普通矩阵计算流程（概述） 与《LoadData》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [Mmad](../mmad_compute/mmad.md)（`same_topic`）：普通矩阵计算流程（概述） 与《Mmad》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [Mmad计算关键特性说明](../mmad_compute_key_features/mmad_compute_key_features.md)（`same_topic`）：普通矩阵计算流程（概述） 与《Mmad计算关键特性说明》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [数据通路（概述）](../../data_move_guide/overview/data_path.md)（`same_topic`）：普通矩阵计算流程（概述） 与《数据通路（概述）》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：普通矩阵计算流程（概述） 与《矩阵计算分形介绍》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算分形介绍](../../cube_compute_tensor_api/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《普通矩阵计算流程（概述）》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算单元（概述）](cube_compute_unit.md)（`same_topic`）：普通矩阵计算流程（概述） 与《矩阵计算单元（概述）》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算的搬入](../cube_compute_load/cube_compute_load.md)（`same_topic`）：普通矩阵计算流程（概述） 与《矩阵计算的搬入》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《普通矩阵计算流程（概述）》明确“Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵计算输入搬运约束](../cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《普通矩阵计算流程（概述）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
