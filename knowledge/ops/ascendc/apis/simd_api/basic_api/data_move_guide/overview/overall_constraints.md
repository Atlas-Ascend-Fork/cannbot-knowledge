---
type: API
title: 总体约束说明（概述）
description: 所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/overview/overall_constraints.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 总体约束说明（概述）

地址对齐要求：GM 1B、UB/L1 32B、L0A/L0B 512B、L0C 64B、BiasTable 64B、Fixpipe 128B。DataBlock（32B）为搬运基本寻址粒度。具体接口有不同对齐要求时以接口说明为准；不满足对齐时使用 DataCopyPad。

多指令同步：多个 DataCopy 目的地址重叠时需调用 PipeBarrier 插入同步（MTE3 流水用 PipeBarrier<PIPE_MTE3>()，MTE2 流水用 PipeBarrier<PIPE_MTE2>()），保证串行化。

<!-- cannbot:related:start -->
## 相关

- [GmUbDataMove](../gm_ub_data_move.md)（`related`）：GmUbDataMove 与《总体约束说明（概述）》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [L1OrL0CUbDataMove](../l1_or_l0_c_ub_data_move.md)（`related`）：《L1OrL0CUbDataMove》说明提供L1 Buffer及L0C Buffer与Unified Buffer间数据搬运接口概述，涵盖连续搬运、高维切分、格式转换及随路量化激活等场景。；《总体约束说明（概述）》说明所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。。二者在L1/L0C到UB路径需要结合数据通路约束选择DataCopy或Fixpipe接口，并分别落实L1到UB和L0C到UB的搬运合同上存在可执行的直接衔接。
- [L1与BiasTable Buffer数据搬运](../l1_bias_table_data_move.md)（`related`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《总体约束说明（概述）》说明所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
- [数据搬运导览](../data_move_guide.md)（`related`）：《数据搬运导览》说明数据搬运导览，按 GM/UB/L1/L0/L0C 等路径组织 AscendC 基础 API 数据搬运接口的索引。；《总体约束说明（概述）》说明所有数据搬运接口共享若干通用约束规则，在进行任何搬运操作前都应确保这些约束被满足，否则可能导致未定义行为或数据异常。。二者在导览按GM、UB、L1、L0和L0C通路组织搬运选择，并以数据通路和对齐约束解释各子路径上存在可执行的直接衔接。
- [数据搬运概念（概述）](data_move_concept.md)（`related`）：DataMoveConcept 定义 DataBlock、搬运通路和长度单位，为总体约束中的 32B 对齐规则提供术语基础。
- [概览](overview.md)（`same_topic`）：总体约束页给出概览强调的地址对齐、32B DataBlock 和目的地址重叠同步规则，是所有搬运路径的共同门槛。
<!-- cannbot:related:end -->
