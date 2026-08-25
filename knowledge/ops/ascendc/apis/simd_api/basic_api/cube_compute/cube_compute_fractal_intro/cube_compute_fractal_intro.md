---
type: API
title: 矩阵计算分形介绍
description: 矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/cube_compute_fractal_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算分形介绍

矩阵计算单元采用 16×16 分块计算，传统线性存储在读取矩形数据块时需访问不连续地址，效率低。分形存储格式通过软件重排使每个 16×16 计算块在物理内存中连续存放，硬件一次连续读取即可加载整个数据块。

文档采用"大Y小x"命名法：大Y（Z/N）表示分形矩阵间排列顺序（Z 行主序、N 列主序），小x（z/n）表示分形矩阵内部元素排列顺序。矩阵乘法 A×B=C 的格式组合：多数产品使用 Zz×Zn=Nz，Ascend 950PR/950DT 使用 Nz×Zn=Nz。常见格式包括 ND（线性连续）、Nz、Zz、Zn，以及 NC1HWC0 等。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：矩阵计算分形介绍 与《Cube矩阵计算编程》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《矩阵计算分形介绍》说明矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [关键分形格式详解](key_fractal_format_details.md)（`same_topic`）：矩阵计算分形介绍 与《关键分形格式详解》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《矩阵计算分形介绍》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算分形介绍](../../cube_compute_tensor_api/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算分形介绍》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算单元（概述）](../overview/cube_compute_unit.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算单元（概述）》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算的搬入](../cube_compute_load/cube_compute_load.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算的搬入》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算分形介绍》明确“矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵计算输入搬运约束](../cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算输入搬运约束》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [背景与核心概念](background_and_core_concepts.md)（`same_topic`）：矩阵计算分形介绍 与《背景与核心概念》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [辅助矩阵分形格式详解](aux_cube_fractal_format_details.md)（`same_topic`）：矩阵计算分形介绍 与《辅助矩阵分形格式详解》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
<!-- cannbot:related:end -->
