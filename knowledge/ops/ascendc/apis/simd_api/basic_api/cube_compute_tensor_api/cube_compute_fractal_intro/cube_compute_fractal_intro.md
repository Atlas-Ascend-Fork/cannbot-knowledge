---
type: API
title: 矩阵计算分形介绍
description: 矩阵计算分形格式介绍，包含背景与核心概念、关键分形格式及辅助矩阵分形格式详解。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_fractal_intro/cube_compute_fractal_intro.md
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

- [矩阵计算的搬入总体说明](../cube_compute_load/overall_description.md)（`related`）：矩阵计算的搬入总体说明 与《矩阵计算分形介绍》的实质衔接是：Cube Load 总体说明用于选择 GM→L1 与 L1→各 L0/Bias/Fixpipe 通路；分形格式、缓存位置和搬入约束决定 Copy 路径。
- [CopyGmToL1](../cube_compute_load/copy_gm_to_l1.md)（`same_topic`）：矩阵计算分形介绍 与《CopyGmToL1》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [CopyL1ToFixpipe](../cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：矩阵计算分形介绍 与《CopyL1ToFixpipe》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [CopyL1ToL0A](../cube_compute_load/copy_l1_to_l0_a.md)（`same_topic`）：矩阵计算分形介绍 与《CopyL1ToL0A》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [CopyL1ToL0B](../cube_compute_load/copy_l1_to_l0_b.md)（`same_topic`）：矩阵计算分形介绍 与《CopyL1ToL0B》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [Mmad](../mmad_compute/mmad.md)（`same_topic`）：矩阵计算分形介绍 与《Mmad》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [关键分形格式详解](../../cube_compute/cube_compute_fractal_intro/key_fractal_format_details.md)（`same_topic`）：矩阵计算分形介绍 与《关键分形格式详解》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [普通矩阵计算流程（概述）](../../cube_compute/overview/cube_compute_flow.md)（`same_topic`）：矩阵计算分形介绍 与《普通矩阵计算流程（概述）》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵搬出关键特性说明](../cube_store_key_features/cube_store_key_features.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵搬出关键特性说明》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算分形介绍](../../cube_compute/cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算分形介绍》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算的搬入](../cube_compute_load/cube_compute_load.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算的搬入》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算的搬出》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算的搬出总体说明](../cube_compute_store/overall_description.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算的搬出总体说明》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [背景与核心概念](../../cube_compute/cube_compute_fractal_intro/background_and_core_concepts.md)（`same_topic`）：矩阵计算分形介绍 与《背景与核心概念》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [辅助矩阵分形格式详解](../../cube_compute/cube_compute_fractal_intro/aux_cube_fractal_format_details.md)（`same_topic`）：矩阵计算分形介绍 与《辅助矩阵分形格式详解》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
<!-- cannbot:related:end -->
