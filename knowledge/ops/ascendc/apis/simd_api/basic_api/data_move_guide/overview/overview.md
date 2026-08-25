---
type: API
title: 概览
description: 数据搬运导览，介绍AI Core分层存储架构中的数据通路、TPosition映射、搬运功能分类及通用约束等核心概念。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述概述概览

数据搬运是算子开发中最基础且最关键的操作之一。在昇腾AI Core的分层存储架构中，数据需要在不同层级的存储单元之间流转，才能完成计算任务。数据搬运类API（DataCopy、DataCopyPad、Copy、LoadData（2D矩阵搬运）、LoadData（卷积数据搬运）、FixPipe等）开放了底层硬件搬运单元（MTE1/MTE2/MTE3/FixPipe）的能力，使开发者可以高效、灵活地在Global Memory与各级Local Memory之间，以及Local Memory内部进行数据传输。

本章节为数据搬运的导览性内容，旨在帮助读者在深入阅读后续各通路详解章节之前，建立起对以下核心概念的统一认知：

- **存储层级与数据通路：** AI Core内部的物理存储单元有哪些，数据可以在哪些通路之间流动，以及搬运所依赖的硬件流水类型。
- **逻辑位置（TPosition）与物理内存的映射：** Ascend C通过TPosition机制隐藏硬件差异，开发者需理解VECIN/VECOUT/A1/B1/CO1等逻辑位置对应的实际物理存储。
- **搬运功能分类：** 基础数据搬运、高维切分搬运、切片搬运、随路格式转换（ND2NZ/NZ2ND/DN2NZ）、随路量化激活、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运（LoadData（2D矩阵搬运）/LoadData（卷积数据搬运））、多维数据搬运NDDMA等功能的概念与适用场景。
- **关键参数概念：** DataBlock、blockLen、blockCount、srcStride/dstStride、repeat等参数的物理含义与配置方式。
- **通用约束：** 所有数据搬运接口共性的地址对齐要求、数据量约束、同步规则等。

- **数据搬运概念**

- **数据通路**

- **总体约束说明**

<!-- cannbot:related:start -->
## 相关

- [GmUbDataMove](../gm_ub_data_move.md)（`related`）：GmUbDataMove 与《概览》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [L1OrL0CUbDataMove](../l1_or_l0_c_ub_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《概览》说明数据搬运导览，介绍AI Core分层存储架构中的数据通路、TPosition映射、搬运功能分类及通用约束等核心概念。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [总体约束说明（概述）](overall_constraints.md)（`same_topic`）：总体约束页给出概览强调的地址对齐、32B DataBlock 和目的地址重叠同步规则，是所有搬运路径的共同门槛。
- [数据搬运概念（概述）](data_move_concept.md)（`same_topic`）：数据搬运概念页把概览中的能力划分为连续、高维切分、格式转换、非对齐、NDDMA 等类别，并映射到 DataCopy/DataCopyPad/Copy/LoadData。
- [数据通路（概述）](data_path.md)（`same_topic`）：“数据通路（概述）”处理AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：；“概览”明确数据搬运导览，介绍AI Core分层存储架构中的数据通路、TPosition映射、搬运功能分类及通用约束等核心概念。。实质衔接：数据搬运概览把这里的 GM/L1/L0/UB/Fixpipe 硬件通路组织成入口，正文用于解释路径选择，而不是连接每个具体搬运成员。
<!-- cannbot:related:end -->
