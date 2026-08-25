---
type: API
title: 矩阵计算单元（概述）
description: Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer用于存储左矩阵，L0B Buffer用于存储右矩阵，L0C
  Buffer则用于存储初始化累加值和矩阵计算结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/overview/cube_compute_unit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵计算单元（概述）

Cube 计算单元专用于矩阵运算，直接访问的专用缓存：L0A Buffer 存储左矩阵、L0B Buffer 存储右矩阵、L0C Buffer 存储累加初始化值和计算结果。关联存储单元含 L1 Buffer（输入数据缓存，从 GM 搬入）、Fixpipe Buffer（Fixpipe 量化参数）、BiasTable Buffer（偏置数据）。数据流为 GM→L1→L0A/L0B→（Mmad）→L0C→（Fixpipe）→GM。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《矩阵计算单元（概述）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)（`explains`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《矩阵计算单元（概述）》说明Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer用于存储左矩阵，L0B Buffer用于存储右矩阵，L0C Buffer则用于存储初始化累加值和矩阵计算结果。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [矩阵计算（ISASI）](../cube_compute_overview.md)（`related`）：CubeComputeUnit 说明 L0A/L0B/L0C 的角色和可直访缓存，为总览中的搬入与搬出通路为何受特定 Buffer 约束提供机制解释。
- [普通矩阵计算流程（概述）](cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《矩阵计算单元（概述）》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算单元（概述）》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算单元（概述）》明确“Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer用于存储左矩阵，L0B Buffer用于存储右矩阵，L0C Buffer则用于存储初始化累加值和矩阵计算结果。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
<!-- cannbot:related:end -->
