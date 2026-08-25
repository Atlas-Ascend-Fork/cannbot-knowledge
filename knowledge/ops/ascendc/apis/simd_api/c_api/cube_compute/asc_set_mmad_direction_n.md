---
type: API
title: AscSetMmadDirectionN
description: 设置矩阵乘加计算（Mmad）时逐行生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag开启且开启Nz2ND随路格式转换或B8/B4量化触发Channel
  Merge的场景。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_mmad_direction_n.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetMmadDirectionN

本接口用于设置矩阵乘加计算（Mmad）时逐行生成矩阵计算结果分形。该配置只改变L0C Buffer上结果分形的生成顺序，不改变计算结果、乘加次数或输出格式。

在开启UnitFlag的场景下，当L0C Buffer上结果分形的生成顺序与数据搬出指令的搬出顺序保持一致时，可以获得更好的性能表现，因此本接口可用于以下场景
- UnitFlag开启且搬出时开启Nz2ND随路格式转换。
- UnitFlag开启且搬出时不进行随路格式转换，且开启B8/B4量化触发Channel Merge功能。

约束：- 本接口需在矩阵乘加指令（asc_mmad、asc_mmad_mx）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。
- 方向配置一旦写入会持续生效，后续矩阵乘加指令若不显式重新配置，将沿用当前方向配置。如需切换为先沿行方向、再沿列方向生成矩阵计算结果分形，请重新调用asc_set_mmad_direction_m接口。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《AscSetMmadDirectionN》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [AscMmad](asc_mmad.md)（`related`）：方向配置必须在 asc_mmad 前调用，并决定其 L0C 结果分形生成顺序。
- [AscSetL0c2gmNz2nd](asc_set_l0c2gm_nz2nd.md)（`related`）：AscSetL0c2gmNz2nd 与《AscSetMmadDirectionN》的实质衔接是：AscSetL0c2gmNz2nd 为 L0C 搬出配置 NZ→ND，AscSetL0cCopyParams 与 C++ SetFixpipeNz2ndFlag 是同一配置的相邻 API 层表达；NZ2ND 概念和 MmadDirectionN 说明格式转换与搬出方向的配合。
- [NZ2ND](../../basic_api/cube_compute/cube_store_key_features/nz2_nd.md)（`related`）：DirectionN 的适用场景之一是 UnitFlag 开启且搬出做 NZ2ND，二者顺序需匹配。
- [UnitFlag](../../basic_api/cube_compute/mmad_compute_key_features/unit_flag.md)（`related`）：DirectionN 只在 UnitFlag 与特定搬出顺序组合下有性能意义，该说明给出启用边界。
- [AscSetMmadDirectionM](asc_set_mmad_direction_m.md)（`same_topic`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《AscSetMmadDirectionN》说明设置矩阵乘加计算（Mmad）时逐行生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag开启且开启Nz2ND随路格式转换或B8/B4量化触发Channel Merge的场景。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [UnitFlag](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscSetMmadDirectionN》提供“设置矩阵乘加计算（Mmad）时逐行生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag开启且开启Nz2ND随路格式转换或B8/B4量化触发Channel Merge的场景。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
