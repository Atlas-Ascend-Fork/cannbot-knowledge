---
type: API
title: 数据搬运概念（概述）
description: 数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/data_move_concept.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 数据搬运概念（概述）

数据搬运按功能复杂度递增分为：基础连续搬运（DataCopy，count 参数指定元素数）、高维切分搬运（DataCopyParams：blockLen/blockCount/srcStride/dstStride/repeat，DataBlock 32B 为单位）、切片搬运（SliceInfo 多维子区域提取）、随路格式转换（ND2NZ/NZ2ND/DN2NZ，搬运同时完成格式转换）、随路量化激活搬运（L0C→GM 的 quant/ReLU）、非对齐搬运（DataCopyPad，自定义 Padding）、UB 内部搬运（Copy，支持 mask）、矩阵分形搬运（LoadData，512B 分形）和多维数据搬运（NDDMA，自由配置维度和 Stride）。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../memory_vector_compute/data_move/data_copy_gm_and_ub_continuous.md)（`related`）：基础连续搬运类别由该 DataCopy 接口直接实现，count 表达连续元素数。
- [DataCopy](../../memory_vector_compute/data_move/data_copy_gm_to_ub_nddma.md)（`related`）：概述将 NDDMA 定位为多维自由 stride 搬运，适合超出普通高维切分表达能力的场景。
- [GmUbDataMove](../gm_ub_data_move.md)（`related`）：GmUbDataMove 与《数据搬运概念（概述）》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [L1OrL0CUbDataMove](../l1_or_l0_c_ub_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《数据搬运概念（概述）》说明数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [L1与BiasTable Buffer数据搬运](../l1_bias_table_data_move.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《数据搬运概念（概述）》说明数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [总体约束说明（概述）](overall_constraints.md)（`related`）：DataMoveConcept 定义 DataBlock、搬运通路和长度单位，为总体约束中的 32B 对齐规则提供术语基础。
- [背景与核心概念](../../cube_compute/cube_compute_fractal_intro/background_and_core_concepts.md)（`related`）：分形布局决定连续块如何在 GM/L1/L0 间搬运，数据搬运概念页解释物理传输单位。
- [数据搬运导览](../data_move_guide.md)（`same_topic`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《数据搬运概念（概述）》说明数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [数据通路（概述）](data_path.md)（`same_topic`）：数据路径说明给出 GM、UB、L1、L0 与 Fixpipe 的可达通路，是按搬运概念选 API 的第一层约束。
- [概览](overview.md)（`same_topic`）：数据搬运概念页把概览中的能力划分为连续、高维切分、格式转换、非对齐、NDDMA 等类别，并映射到 DataCopy/DataCopyPad/Copy/LoadData。
- [矩阵计算输入搬运约束](../../cube_compute/cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《数据搬运概念（概述）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
