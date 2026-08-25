---
type: API
title: Mmad辅助配置说明
description: Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/mmad_compute_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mmad辅助配置说明

Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。

控制Mmad/MmadWithSparse优先通过M/N的哪个方向。

本接口组包含 SetMMColumnMajor/SetMMRowMajor, SetHF32Mode, SetHF32TransMode。

本接口属于 Cube 矩阵计算接口。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《Mmad辅助配置说明》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《Mmad辅助配置说明》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [AscSetFp32Mode](../../../c_api/cube_compute/asc_set_fp32_mode.md)（`related`）：AscSetFp32Mode 与《Mmad辅助配置说明》的实质衔接是：AscSetFp32Mode 与 HF32 round/enable/trans 配置共同决定 AscMmad 的 FP32/HF32 计算模式，Mmad 约束和 HF32 指南说明精度与方向设置。
- [AscSetMmadDirectionM](../../../c_api/cube_compute/asc_set_mmad_direction_m.md)（`related`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《Mmad辅助配置说明》说明Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [DataCopy](../cube_compute_load/data_copy_l1_to_bias_table.md)（`related`）：DataCopy 与《Mmad辅助配置说明》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《Mmad辅助配置说明》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad](../mmad_compute/mmad.md)（`related`）：Mmad辅助配置说明 与《Mmad》的衔接是：该配置组中的列主序/行主序与 HF32 选项会被 Mmad 执行直接消费；Tensor API 的对应辅助配置提供同一矩阵乘契约下的另一套入口。
- [MmadBitMode](../mmad_compute/mmad_bit_mode.md)（`related`）：Mmad辅助配置说明说明Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。
- [Mmad计算关键特性说明](../mmad_compute_key_features/mmad_compute_key_features.md)（`related`）：Mmad辅助配置说明 与《Mmad计算关键特性说明》的衔接是：该配置组中的列主序/行主序与 HF32 选项会被 Mmad 执行直接消费；Tensor API 的对应辅助配置提供同一矩阵乘契约下的另一套入口。
- [基础APIGEMV](../../cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad辅助配置说明》明确提供“Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [矩阵计算（ISASI）](../mmad_compute/mmad_compute.md)（`related`）：Mmad辅助配置说明 与《矩阵计算（ISASI）》的衔接是：该配置组中的列主序/行主序与 HF32 选项会被 Mmad 执行直接消费；Tensor API 的对应辅助配置提供同一矩阵乘契约下的另一套入口。
- [Mmad计算辅助配置接口](../../cube_compute_tensor_api/mmad_compute_aux_config/mmad_compute_aux_config.md)（`same_topic`）：《Mmad辅助配置说明》明确“Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。”；它与《Mmad计算辅助配置接口》的“Mmad计算辅助配置接口列表如下：”在实际调用参数、数据流或结果校验上直接衔接。
- [SetMMColumnMajor/SetMMRowMajor](set_mm_column_major_set_mm_row_major.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad辅助配置说明》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
<!-- cannbot:related:end -->
