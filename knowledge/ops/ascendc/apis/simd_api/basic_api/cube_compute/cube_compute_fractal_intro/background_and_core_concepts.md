---
type: API
title: 背景与核心概念
description: 矩阵计算单元采用分块计算逻辑，例如可并行处理16×16的矩阵分片。在传统的线性存储布局（如row major（行主序）或column major（列主序））中，数据按行或列连续存放。当需要读取一个16×16的矩形数据块时，若直接从内存中获取，则需访问不连续的多个内存地址以逐行“收集”数据，这种非连续访问会导致内存效率显著下降。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/background_and_core_concepts.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 背景与核心概念

矩阵计算单元采用分块计算逻辑，例如可并行处理16×16的矩阵分片。在传统的线性存储布局（如row major（行主序）或column major（列主序））中，数据按行或列连续存放。当需要读取一个16×16的矩形数据块时，若直接从内存中获取，则需访问不连续的多个内存地址以逐行“收集”数据，这种非连续访问会导致内存效率显著下降。

为解决上述问题，引入了矩阵分形存储格式。该格式通过软件层对数据进行重排，使每个16×16计算块在物理内存中连续存放。硬件仅需发起一次连续读取，即可将整个数据块加载至片上寄存器，避免了多地址寻址开销，从而大幅提升矩阵计算单元的数据吞吐率。

昇腾AI处理器的矩阵计算单元为追求极高的数据吞吐率与计算密度，采用了专有的硬件架构设计。与通用CPU常用的连续线性存储不同，该单元要求输入输出数据必须符合特定的分形存储格式。在使用Ascend C的Mmad类接口进行算子开发时，深入理解这些数据格式对于实现正确的数据搬运、分块及性能优化至关重要。

为便于理解与记忆，文档采用“大Y小x”的直观命名法：

- 大Y（Z/N）：表示分形矩阵之间的排列顺序（Z为row major（行主序），N为column major（列主序））。
- 小x（z/n）：表示分形矩阵内部元素的排列顺序（z为row major（行主序），n为column major（列主序））。

<!-- cannbot:related:start -->
## 相关

- [数据搬运概念（概述）](../../data_move_guide/overview/data_move_concept.md)（`related`）：分形布局决定连续块如何在 GM/L1/L0 间搬运，数据搬运概念页解释物理传输单位。
- [关键分形格式详解](key_fractal_format_details.md)（`same_topic`）：关键分形页给出 A/B/C 主矩阵的 block 布局，是地址计算的直接依据。
- [矩阵计算分形介绍](cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《背景与核心概念》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算分形介绍](../../cube_compute_tensor_api/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《背景与核心概念》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [辅助矩阵分形格式详解](aux_cube_fractal_format_details.md)（`same_topic`）：辅助分形页补充 bias/scale 等 buffer 格式，连接概念与辅助数据搬运。
<!-- cannbot:related:end -->
