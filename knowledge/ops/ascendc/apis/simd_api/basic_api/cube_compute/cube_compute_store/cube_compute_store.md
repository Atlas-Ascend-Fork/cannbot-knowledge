---
type: API
title: 矩阵计算的搬出
description: 矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/cube_compute_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算的搬出

矩阵计算 ISASI 搬出接口集，提供 L0C/L1/UB/GM 之间矩阵结果数据的搬运接口。
DataCopy 和 Fixpipe 是两类核心搬运接口，支持 L0C 到 GM、L0C 到 L1、L0C 到 UB 等路径；另提供 DataCopyL1ToUB 和 DataCopy(L1ToGM) 用于 L1 到 UB/GM 的直接搬运。
Fixpipe 支持在搬运过程中执行随路量化与格式转换，具体特性参见矩阵搬出关键特性说明。

<!-- cannbot:related:start -->
## 相关

- [矩阵搬出寄存器配置说明](../cube_store_aux_config/cube_store_aux_config.md)（`related`）：矩阵搬出寄存器配置说明 与《矩阵计算的搬出》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [Cube计算(ISASI)总体说明](overall_description.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《Cube计算(ISASI)总体说明》明确“矩阵计算的搬出是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现L0C Buffer与Global Memory、L1 Buffer、Unified Buffer（UB）之间的数据高效传输。该接口系列提供了多种数据搬运模式，能够满足矩阵计算中的数据搬运需求，通常在Mmad接口后配合使用。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [L0C Buffer内存结构介绍](l0_c_memory_structure_intro.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《L0C Buffer内存结构介绍》明确“为提升数据访问效率和吞吐量，L0C Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《普通矩阵计算流程（概述）》明确“Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵搬出关键特性说明](../cube_store_key_features/cube_store_key_features.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵搬出关键特性说明》明确“矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算分形介绍》明确“矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵计算单元（概述）](../overview/cube_compute_unit.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算单元（概述）》明确“Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer用于存储左矩阵，L0B Buffer用于存储右矩阵，L0C Buffer则用于存储初始化累加值和矩阵计算结果。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵计算的搬出](../../cube_compute_tensor_api/cube_compute_store/cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算的搬出》明确“矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
- [矩阵计算的搬出总体说明](../../cube_compute_tensor_api/cube_compute_store/overall_description.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《矩阵计算的搬出总体说明》明确“矩阵计算的搬出接口主要实现L0C Buffer与Global Memory、Unified Buffer之间的数据高效传输。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
<!-- cannbot:related:end -->
