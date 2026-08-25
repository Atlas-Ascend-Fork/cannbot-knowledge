---
type: API
title: L1OrL0CUbDataMove
description: 提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_or_L0C_UB_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1OrL0CUbDataMove

L1 Buffer 及 L0C Buffer 与 Unified Buffer 间数据搬运接口概述。L1→UB 支持 DataCopyL1ToUB（连续/高维切分，仅 950）。L0C→UB 支持 DataCopy（增强随路反量化/ReLU，仅 Atlas 推理 AI Core）和 Fixpipe（随路量化/格式转换，950/Atlas 200I/500 A2）。UB→L1 支持 DataCopy（连续/高维切分/ND2NZ，a2/a3/950）。UB 地址需 32B 对齐。

<!-- cannbot:related:start -->
## 相关

- [DataCopy（L0C Buffer到UB数据搬运）](../cube_compute/cube_compute_store/data_copy_l0_c_to_ub.md)（`related`）：DataCopy（L0C Buffer到UB数据搬运） 与《L1OrL0CUbDataMove》的实质衔接是：L0C 到 UB 搬出依赖 L0C 布局、Copy/Fixpipe、双目标模式和对齐/stride 约束。
- [FixpipeL0CToUB](../cube_compute/cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《FixpipeL0CToUB》说明将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [L1与L0数据搬运](l1_l0_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《L1与L0数据搬运》说明L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [总体约束说明（概述）](overview/overall_constraints.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《总体约束说明（概述）》说明所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [数据搬运导览](data_move_guide.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [数据搬运概念（概述）](overview/data_move_concept.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《数据搬运概念（概述）》说明数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [数据通路（概述）](overview/data_path.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《数据通路（概述）》说明AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [概览](overview/overview.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《概览》说明数据搬运导览，介绍AI Core分层存储架构中的数据通路、TPosition映射、搬运功能分类及通用约束等核心概念。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [Copy](../cube_compute_tensor_api/cube_compute_store/copy_l0_c_to_ub.md)（`same_topic`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《Copy》说明将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [DataCopyL1ToUB（L1到UB数据搬运）](../cube_compute/cube_compute_store/data_copy_l1_to_ub.md)（`same_topic`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《DataCopyL1ToUB（L1到UB数据搬运）》说明提供从L1 Buffer搬运数据到Unified Buffer的基础能力，数据在传输过程中保持原始格式和内容不变，支持连续和非连续的数据搬运。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
