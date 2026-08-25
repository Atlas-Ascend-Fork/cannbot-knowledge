---
type: API
title: L1与BiasTable Buffer数据搬运
description: DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_BiasTable_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1与BiasTable Buffer数据搬运

DataCopy 实现 L1 Buffer 到 BiasTable Buffer 的连续数据搬运，格式和内容保持不变。用于将矩阵计算的 bias 参数从 L1 搬运至 BiasTable Buffer。BiasTable Buffer 地址需 64B 对齐，L1 Buffer 地址需 32B 对齐。

<!-- cannbot:related:start -->
## 相关

- [SetBiasType](../../adv_api/convolution_compute/conv3_d_tiling/set_bias_type.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《SetBiasType》说明设置Bias在内存上的位置、数据格式和数据类型。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [总体约束说明（概述）](overview/overall_constraints.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《总体约束说明（概述）》说明所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [数据搬运导览](data_move_guide.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [数据搬运概念（概述）](overview/data_move_concept.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《数据搬运概念（概述）》说明数据搬运类接口提供了全面的数据搬运功能，覆盖从最基础的连续搬运到复杂的随路转换和量化激活。按照功能复杂度递增，搬运能力可以分为以下几个类别：基础数据搬运、高维切分搬运、切片搬运、随路格式转换搬运、随路量化激活搬运、非对齐搬运、UB内部搬运（Copy）、矩阵分形搬运和多维数据搬运NDDMA。每一类在后续章节中都有对应的详细接口说明。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [数据通路（概述）](overview/data_path.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《数据通路（概述）》说明AI Core是昇腾处理器的核心计算单元，以NPU架构版本2201为例，其内部分层存储架构如图1所示，主要包含以下组成部分：。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [AscCopyL12Bt](../../c_api/cube_data_move/asc_copy_l12bt/asc_copy_l12bt.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《AscCopyL12Bt》说明L1到Bt Buffer数据搬运接口集合，包含不同架构版本。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [CopyL1ToBiasTable](../cube_compute_tensor_api/cube_compute_load/copy_l1_to_bias_table.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《CopyL1ToBiasTable》说明通过Tensor API的Copy接口将L1 Buffer中的bias数据搬运到BiasTable Buffer，作为Mmad计算的bias输入。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [DataCopy](../cube_compute/cube_compute_load/data_copy_l1_to_bias_table.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《DataCopy》说明将矩阵计算用到的Bias参数从L1 Buffer搬运到BiasTable Buffer。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [asc_copy_l12bt](../../c_api/cube_data_move/asc_copy_l12bt/asc_copy_l12bt_arch_2201.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《asc_copy_l12bt》说明将数据从L1 Buffer搬运到BiasTable Buffer中，BiasTable Buffer用于存放矩阵计算中的Bias。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [asc_copy_l12bt](../../c_api/cube_data_move/asc_copy_l12bt/asc_copy_l12bt_arch_3510.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《asc_copy_l12bt》说明将MMAD指令的Bias数据从L1 Buffer搬运到BiasTable Buffer中。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
<!-- cannbot:related:end -->
