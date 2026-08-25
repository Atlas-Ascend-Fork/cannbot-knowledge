---
type: Guide
title: Cube矩阵计算编程
description: 本文介绍基于Ascend C语言扩展API，依托L1 Buffer、L0系列片上缓存实现矩阵计算的开发方法，该方式是Ascend C中最基础、通用的矩阵编程方案。AI
  Core中的Cube单元部署在AIC核，负责矩阵计算，拥有专属片上缓存：L0A Buffer存放左矩阵、L0B Buffer存放右矩阵、L0C Buffer用于保存初始累加值与矩阵运算结果。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Cube矩阵计算编程

本文介绍基于Ascend C语言扩展API，依托L1 Buffer、L0系列片上缓存实现矩阵计算的开发方法，该方式是Ascend C中最基础、通用的矩阵编程方案。AI Core中的Cube单元部署在AIC核，负责矩阵计算，拥有专属片上缓存：L0A Buffer存放左矩阵、L0B Buffer存放右矩阵、L0C Buffer用于保存初始累加值与矩阵运算结果。
## Cube矩阵计算核心步骤
Cube矩阵计算整体分为数据搬入、数据加载、矩阵计算、数据搬出四个阶段，完整流程如下：
1. 通过DMA将数据从Global Memory搬运至L1 Buffer；
2. 将L1 Buffer中的数据加载至L0A Buffer、L0B Buffer；
3. 执行矩阵计算，结果存入L0C Buffer；
4. 通过DMA将计算结果从L0C Buffer搬运回Global Memory。
## 矩阵计算内存管理
### 矩阵计算内存申请
矩阵计算主要依托L0 Buffer完成运算。开发者需要先将输入数据从Global Memory搬运至L1 Buffer，再加载到L0 Buffer，最后调用Cube计算指令完成运算。L1 Buffer与L0 Buffer均通过数组形式声明，本指南主要介绍静态内存申请方式。
- 静态申请：分配一段指定大小的内存空间，空间大小在编译时确定，不可动态修改。
### 矩阵计算内存布局
Cube单元采用分块计算逻辑，硬件最小计算粒度为分形块，可并行处理多个分形。分形块大小取决于数据类型：对于half类型，分形形状为16×16（32B/sizeof(half)=16）；对于int8类型，分形形状为16×32或32×16（32B/sizeof(int8)=32）。传统行主序、列主序等线性存储模式下，读取分形块时会产生大量非连续内存访问，大幅降低访存效率。
为解决该问题，昇腾引入矩阵分形存储格式。软件层会对数据重新排布，让每个分形块在物理内存中连续存储，硬件单次读取即可加载整块数据，消除零散寻址带来的开销，有效提升数据吞吐能力。
分形粒度是Cube单元的基础计算规范，NPU架构版本2201、NPU架构版本3510全系列产品均遵循该规范，但具体分形形状因数据类型而异。昇腾Cube单元为极致发挥算力，采用不同于通用CPU的存储规则，输入、输出数据都需要匹配指定分形格式。使用Ascend C的Mmad接口开发算子时，掌握各类分形格式，是保证数据搬运、分块逻辑正确以及性能优化的关键。
为便于理解与记忆，文档采用“大Y小x”的直观命名法：
- 大Y（Z/N）：表示分形矩阵之间的排列顺序（Z为行主序，N为列主序）。
- 小x（z/n）：表示分形矩阵内部元素的排列顺序（z为行主序，n为列主序）。
### 关键分形格式详解
矩阵分形格式用于定义多维张量在内存中的排布规则。受硬件读取逻辑影响，不同产品型号对矩阵乘法 C = A × B 的格式要求存在差异：
- 针对NPU架构版本2201，矩阵乘法C = A × B要求：左矩阵A使用Zz格式，右矩阵B使用Zn格式，结果矩阵C使用Nz格式。

<!-- cannbot:related:start -->
## 相关

- [AscMmad](../../../../../apis/simd_api/c_api/cube_compute/asc_mmad.md)（`explains`）：Cube矩阵计算编程 与《AscMmad》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [GmL1OrL0DataMove](../../../../../apis/simd_api/basic_api/data_move_guide/gm_l1_or_l0_data_move.md)（`explains`）：Cube矩阵计算编程 与《GmL1OrL0DataMove》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [L1与L0数据搬运](../../../../../apis/simd_api/basic_api/data_move_guide/l1_l0_data_move.md)（`explains`）：L1与L0数据搬运 与《Cube矩阵计算编程》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [Mmad](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute/mmad.md)（`explains`）：Cube矩阵计算编程 与《Mmad》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Mmad接口边界值汇总](../../../../../apis/appendix/mmad_interface_boundary_value_summary.md)（`explains`）：Cube矩阵计算编程 与《Mmad接口边界值汇总》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Mmad计算关键特性说明](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute_key_features/mmad_compute_key_features.md)（`explains`）：Cube矩阵计算编程 与《Mmad计算关键特性说明》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Mmad辅助配置说明](../../../../../apis/simd_api/basic_api/cube_compute/mmad_compute_aux_config/mmad_compute_aux_config.md)（`explains`）：Cube矩阵计算编程 与《Mmad辅助配置说明》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [SetFmatrix](../../../../../apis/simd_api/basic_api/cube_compute/cube_load_aux_config/set_fmatrix.md)（`explains`）：Cube矩阵计算编程 与《SetFmatrix》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [SetFmatrixBitMode](../../../../../apis/simd_api/basic_api/cube_compute/cube_load_aux_config/set_fmatrix_bit_mode.md)（`explains`）：Cube矩阵计算编程 与《SetFmatrixBitMode》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [普通矩阵计算流程（概述）](../../../../../apis/simd_api/basic_api/cube_compute/overview/cube_compute_flow.md)（`explains`）：Cube矩阵计算编程 与《普通矩阵计算流程（概述）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [矩阵计算分形介绍](../../../../../apis/simd_api/basic_api/cube_compute/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`explains`）：矩阵计算分形介绍 与《Cube矩阵计算编程》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算单元（概述）](../../../../../apis/simd_api/basic_api/cube_compute/overview/cube_compute_unit.md)（`explains`）：Cube矩阵计算编程 与《矩阵计算单元（概述）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [AI Core SIMD编程模型概述](../overview.md)（`related`）：Cube矩阵计算编程 与《AI Core SIMD编程模型概述》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Cube tile k/n 超 L1/L0 上限报 INVALID_TILE](../../../../../runbooks/compilation/cube_tile_k_n_l1_l0_invalid_tile.md)（`related`）：Cube矩阵计算编程 与《Cube tile k/n 超 L1/L0 上限报 INVALID_TILE》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [抽象硬件架构（AI Core SIMD编程）](../abstract_hardware_architecture.md)（`related`）：Cube矩阵计算编程 与《抽象硬件架构（AI Core SIMD编程）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [核函数（AI Core SIMD编程）](../kernel_function.md)（`related`）：Cube矩阵计算编程 与《核函数（AI Core SIMD编程）》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [Cube矩阵计算编程](../cpp_tensor_programming/cube_matrix_computation.md)（`same_topic`）：《Cube矩阵计算编程》说明本文介绍如何在Ascend C中使用C++ Tensor编程API编写基于L1 Buffer、L0A Buffer等片上存储的矩阵计算代码。；《Cube矩阵计算编程》说明本文介绍基于Ascend C语言扩展API，依托L1 Buffer、L0系列片上缓存实现矩阵计算的开发方法，该方式是Ascend C中最基础、通用的矩阵编程方案。AI Core中的Cube单元部署在AIC核，负责矩阵计算，拥有专属片上缓存：L0A Buffer存放左矩阵、L0B Buffer存放右矩阵、L0C Buffer用于保存初始累加值与矩阵运算结果。。二者在C++ Tensor Cube编程把GM到L1/L0搬入、分形布局、Mmad计算和L0C搬出连接为完整矩阵流水上存在可执行的直接衔接。
- [C语言编程概述](c_programming_overview.md)（`same_topic`）：Cube矩阵计算编程 与《C语言编程概述》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
<!-- cannbot:related:end -->
