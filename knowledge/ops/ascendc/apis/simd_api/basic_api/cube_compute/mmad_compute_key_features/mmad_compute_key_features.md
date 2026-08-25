---
type: API
title: Mmad计算关键特性说明
description: Mmad计算关键特性集合，涵盖GEMV、HF32、UnitFlag及K方向对齐约束等特性说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/mmad_compute_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mmad计算关键特性说明

Mmad 矩阵乘计算的关键特性说明集合，涵盖 GEMV（矩阵向量乘）、HF32（半精度浮点格式）、UnitFlag（单位标志控制）以及 K 方向对齐约束。这些特性影响 Mmad 接口的精度选择、数据格式与对齐要求，使用前需确认目标硬件与场景是否支持对应特性，并遵循各特性的数据布局与对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《Mmad计算关键特性说明》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《Mmad计算关键特性说明》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [DataCopy](../cube_compute_load/data_copy_l1_to_bias_table.md)（`related`）：DataCopy 与《Mmad计算关键特性说明》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [K方向对齐约束](k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《Mmad计算关键特性说明》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad辅助配置说明](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：Mmad辅助配置说明 与《Mmad计算关键特性说明》的衔接是：该配置组中的列主序/行主序与 HF32 选项会被 Mmad 执行直接消费；Tensor API 的对应辅助配置提供同一矩阵乘契约下的另一套入口。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《Mmad计算关键特性说明》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
<!-- cannbot:related:end -->
