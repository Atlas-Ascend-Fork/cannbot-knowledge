---
type: API
title: UnitFlag
description: unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C
  Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/UnitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# UnitFlag

Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步，降低同步延迟。unitFlag=2 时开启但不改变标志位（Mmad 写等待 flag=0 后写入保持 0；Fixpipe 读等待 flag=1 后读取保持 1）；unitFlag=3 时开启并改变标志位（Mmad 写后设 1；Fixpipe 读后设 0）。

K 轴迭代场景：前 n-1 次 Mmad 设 unitFlag=2 保持写入能力，最后 1 次设 3 通知 Fixpipe 可读；Fixpipe 设 3 读后恢复为 0。需配合 SetMMColumnMajor/SetMMRowMajor 设置方向：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。Mmad 和 Fixpipe 须同步开启 unitFlag，建议计算量与搬出量一致，否则可通过 SetFixPipeConfig() 重置 L0C Buffer 状态。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：《UnitFlag》给出“unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”；该约束/探针可直接复现、解释或前置验证《Matmul高阶API开启UnitFlag》中的“开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。”。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《UnitFlag》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [AscGetL0c2gmUnitflag](../../../c_api/cube_compute/asc_get_l0c2gm_unitflag.md)（`related`）：C API getter 读取 L0C→GM 搬运的 unit flag 状态，连接特性概念与底层控制。
- [AscSetMmadDirectionN](../../../c_api/cube_compute/asc_set_mmad_direction_n.md)（`related`）：DirectionN 只在 UnitFlag 与特定搬出顺序组合下有性能意义，该说明给出启用边界。
- [K方向对齐约束](k_direction_alignment_constraint.md)（`related`）：使用 UnitFlag 优化流水仍需满足 K 方向对齐，不能用同步标志绕过 shape 约束。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《UnitFlag》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [SetMMColumnMajor/SetMMRowMajor](../mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：SetMMColumnMajor/SetMMRowMajor 与《UnitFlag》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [UnitFlag](../../cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《UnitFlag》提供“unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
