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

- [AscMmad](asc_mmad.md)（`related`）：本接口是Ascend C面向昇腾AI芯片的矩阵乘加（Mmad）核心计算接口；本接口需在矩阵乘加指令（asc_mmad、asc_mmad_mx）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。；方向 M 配置是 asc_mmad 执行前的持久前置状态，直接决定结果分形生成顺序。
- [AscSetMmadDirectionN](asc_set_mmad_direction_n.md)（`related`）：M 方向接口规定“如需切换为先沿列方向、再沿行方向生成矩阵计算结果分形，请重新调用asc_set_mmad_direction_n接口。”；N 方向接口反向规定“如需切换为先沿行方向、再沿列方向生成矩阵计算结果分形，请重新调用asc_set_mmad_direction_m接口。”，两端构成依搬出顺序切换结果生成方向的成对配置。
- [UnitFlag](../../basic_api/cube_compute/mmad_compute_key_features/unit_flag.md)（`related`）：方向 M 卡把使用条件限定为“在开启UnitFlag的场景下，当L0C Buffer上结果分形的生成顺序与数据搬出指令的搬出顺序保持一致时，可以获得更好的性能表现”；UnitFlag 卡说明“Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步，降低同步延迟。”，解释方向配置为何必须与细粒度生产/消费顺序一致。
<!-- cannbot:related:end -->
