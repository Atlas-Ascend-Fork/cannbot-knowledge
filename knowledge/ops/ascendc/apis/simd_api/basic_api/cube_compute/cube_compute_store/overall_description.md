---
type: API
title: Cube计算(ISASI)总体说明
description: 矩阵计算的搬出是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现L0C Buffer与Global Memory、L1 Buffer、Unified
  Buffer（UB）之间的数据高效传输。该接口系列提供了多种数据搬运模式，能够满足矩阵计算中的数据搬运需求，通常在Mmad接口后配合使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_store/overall_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Cube计算(ISASI)总体说明

矩阵计算的搬出是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现L0C Buffer与Global Memory、L1 Buffer、Unified Buffer（UB）之间的数据高效传输。该接口系列提供了多种数据搬运模式，能够满足矩阵计算中的数据搬运需求，通常在Mmad接口后配合使用。

矩阵计算的搬出接口支持多种随路搬运场景，包括**随路量化、随路ReLU、随路格式转换（NZ2ND、NZ2DN）、随路通道拆分（Channel Split）、随路通道合并（Channel Merge）、UB双目标模式**。通过灵活配置不同的参数结构体，开发者可以精确控制数据的搬运路径、起始位置、搬运长度、随路搬运能力等关键信息，充分利用硬件的数据搬运能力，最大化算子的整体执行性能。

矩阵计算的搬出整体流程如下图所示：

**图1** 矩阵计算的搬出整体流程图（NPU架构版本2201）

**图2** 矩阵计算的搬出整体流程图（NPU架构版本3510）

其中，Fixpipe Buffer不同的量化模式对应的内存排布如下：

**图3** Fixpipe Buffer内存排布图

<!-- cannbot:related:start -->
## 相关

- [Cube计算(ISASI)总体说明](../cube_compute_load/overall_description.md)（`related`）：Cube load 总体说明覆盖 Mmad 前的 GM/UB→L1/L0A/L0B 输入路径，与本卡的 L0C→GM/L1/UB 输出路径拼成完整矩阵数据流。
- [矩阵计算的搬出](cube_compute_store.md)（`same_topic`）：《矩阵计算的搬出》处理“矩阵计算 ISASI 搬出接口集，涵盖 DataCopy、Fixpipe 等 L0C/L1/UB/GM 间搬运接口及 L0C Buffer 内存结构。”。《Cube计算(ISASI)总体说明》明确“矩阵计算的搬出是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现L0C Buffer与Global Memory、L1 Buffer、Unified Buffer（UB）之间的数据高效传输。该接口系列提供了多种数据搬运模式，能够满足矩阵计算中的数据搬运需求，通常在Mmad接口后配合使用。”，可直接用于核对Cube L0C 搬出寄存器、分形、量化特性和完整矩阵计算数据流合同。
<!-- cannbot:related:end -->
