---
type: API
title: AscSetMmadDirectionM
description: 设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_mmad_direction_m.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetMmadDirectionM

本接口用于设置矩阵乘加计算（Mmad）时逐列生成矩阵计算结果分形。该配置只改变L0C Buffer上结果分形的生成顺序，不改变计算结果、乘加次数或输出格式。

在开启UnitFlag的场景下，当L0C Buffer上结果分形的生成顺序与数据搬出指令的搬出顺序保持一致时，可以获得更好的性能表现，因此本接口可用于以下场景
- UnitFlag关闭时作为所有搬出场景的默认配置（此时不同的结果生成方向通常没有实质性能差异）。
- UnitFlag开启且搬出时不进行随路格式转换，且未因开启B8/B4量化触发Channel Merge功能。
- UnitFlag开启且搬出时开启Nz2DN随路格式转换。

约束：- 本接口需在矩阵乘加指令（asc_mmad、asc_mmad_mx）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。
- 方向配置一旦写入会持续生效，后续矩阵乘加指令若不显式重新配置，将沿用当前方向配置。如需切换为先沿列方向、再沿行方向生成矩阵计算结果分形，请重新调用asc_set_mmad_direction_n接口。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《矩阵乘输出的Channel拆分》说明将NZ格式float类型C矩阵的分形从16x16切分为16x8，使内轴满足32字节对齐便于后续矢量计算。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [Mmad](../../basic_api/cube_compute/mmad_compute/mmad.md)（`related`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《Mmad》说明矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [Mmad辅助配置说明](../../basic_api/cube_compute/mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《Mmad辅助配置说明》说明Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [SetMMColumnMajor/SetMMRowMajor](../../basic_api/cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`related`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《SetMMColumnMajor/SetMMRowMajor》说明控制Mmad/MmadWithSparse优先通过M/N的哪个方向。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [AscMmad](asc_mmad.md)（`same_topic`）：AscMmad 与《AscSetMmadDirectionM》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [AscSetMmadDirectionN](asc_set_mmad_direction_n.md)（`same_topic`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《AscSetMmadDirectionN》说明设置矩阵乘加计算（Mmad）时逐行生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag开启且开启Nz2ND随路格式转换或B8/B4量化触发Channel Merge的场景。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [UnitFlag](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscSetMmadDirectionM》提供“设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
