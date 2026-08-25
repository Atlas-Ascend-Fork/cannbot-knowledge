---
type: API
title: UnitFlag
description: unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C
  Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_key_features/UnitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---


# UnitFlag

UnitFlag是Mmad计算的配置参数，用于控制矩阵计算的数据排布和对齐方式。包含isKFull（K轴是否满载）、isNFull（N轴是否满载）等标志，影响Mmad的内部切分和计算策略。

通过MmadTiling中的UnitFlag字段配置。正确配置UnitFlag可以避免不必要的padding计算，提升性能。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Matmul高阶API开启UnitFlag》提供“开启UnitFlag为MMAD与FIXPIPE提供512B细粒度同步，实现计算与搬出流水并行，提升算子性能。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《中级性能优化》提供“本节基于C++ Tensor编程范式，介绍Matmul基础API算子的性能调优方法，通过4个渐进式优化步骤（L1/L0双缓冲机制、细粒度流水同步、多核并行切分、DataCopyIn优先搬运B矩阵），展示从基础实现到高性能优化的完整调优路径。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [高级极限打磨](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/advanced_extreme_optimization.md)（`explains`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《高级极限打磨》提供“本节基于C++ Tensor编程范式，在上文中级性能优化的基础上，进一步介绍Matmul基础API算子的高级极限打磨方法，通过5个高级优化步骤（大包搬运、LoadData3D替代LoadData2D、常量Tiling、UnitFlag优化、L2Cache优化），深入挖掘硬件性能极限。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [Copy](../cube_compute_store/copy_l0_c_to_gm.md)（`related`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Copy》提供“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [Copy](../cube_compute_store/copy_l0_c_to_ub.md)（`related`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Copy》提供“将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [Mmad](../mmad_compute/mmad.md)（`related`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Mmad》提供“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [AscGetL0c2gmUnitflag](../../../c_api/cube_compute/asc_get_l0c2gm_unitflag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscGetL0c2gmUnitflag》提供“数据搬运过程中进行随路量化时，通过调用该接口获取unit_flag设置。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [AscSetL0c2gmConfig](../../../c_api/cube_compute/asc_set_l0c2gm_config.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscSetL0c2gmConfig》提供“数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [AscSetMmadDirectionM](../../../c_api/cube_compute/asc_set_mmad_direction_m.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscSetMmadDirectionM》提供“设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [AscSetMmadDirectionN](../../../c_api/cube_compute/asc_set_mmad_direction_n.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscSetMmadDirectionN》提供“设置矩阵乘加计算（Mmad）时逐行生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag开启且开启Nz2ND随路格式转换或B8/B4量化触发Channel Merge的场景。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [DataCopyL0CToGM](../../cube_compute/cube_compute_store/data_copy_l0_c_to_gm.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《DataCopyL0CToGM》提供“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [FixpipeL0CToGM](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_gm.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《FixpipeL0CToGM》提供“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [FixpipeL0CToUB](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_ub.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《FixpipeL0CToUB》提供“将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [Mmad计算关键特性说明](mmad_compute_key_features.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Mmad计算关键特性说明》提供“本节介绍Mmad矩阵乘计算中的GEMV、HF32和UnitFlag等关键特性，帮助理解不同计算模式、精度模式和细粒度同步机制。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [SetFixPipeConfig](../../cube_compute/cube_store_aux_config/set_fix_pipe_config.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《SetFixPipeConfig》提供“DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [UnitFlag](../../cube_compute/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《UnitFlag》提供“unitFlag的核心功能体现为：Mmad和FixPipe接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
