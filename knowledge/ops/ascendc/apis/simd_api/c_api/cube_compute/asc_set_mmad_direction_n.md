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
