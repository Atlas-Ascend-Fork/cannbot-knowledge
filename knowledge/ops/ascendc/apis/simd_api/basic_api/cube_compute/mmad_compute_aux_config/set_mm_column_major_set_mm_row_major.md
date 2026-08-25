---
type: API
title: SetMMColumnMajor/SetMMRowMajor
description: 控制Mmad/MmadWithSparse优先通过M/N的哪个方向。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_aux_config/SetMMColumnMajor-SetMMRowMajor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetMMColumnMajor/SetMMRowMajor

控制 Mmad/MmadWithSparse 的计算方向优先级。SetMMColumnMajor 表示 Cube 先沿 M 方向再沿 N 方向生成结果；SetMMRowMajor 表示先沿 N 方向再沿 M 方向。开启 unitFlag 时需配合设置：Fixpipe 开启 NZ2ND/ChannelMerge 时用 SetMMRowMajor，否则用 SetMMColumnMajor。支持 950/a2/a3/Atlas 200I/500 A2。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启UnitFlag](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_unit_flag.md)（`explains`）：SetMMColumnMajor/SetMMRowMajor 与《Matmul高阶API开启UnitFlag》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《SetMMColumnMajor/SetMMRowMajor》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [AscSetMmadDirectionM](../../../c_api/cube_compute/asc_set_mmad_direction_m.md)（`related`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《SetMMColumnMajor/SetMMRowMajor》说明控制Mmad/MmadWithSparse优先通过M/N的哪个方向。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [NZ2ND](../cube_store_key_features/nz2_nd.md)（`related`）：SetMMColumnMajor/SetMMRowMajor 与《NZ2ND》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetMMColumnMajor/SetMMRowMajor 与《SetFixPipeConfig》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [UnitFlag](../mmad_compute_key_features/unit_flag.md)（`related`）：SetMMColumnMajor/SetMMRowMajor 与《UnitFlag》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [基础APIGEMV](../../cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《SetMMColumnMajor/SetMMRowMajor》明确提供“控制Mmad/MmadWithSparse优先通过M/N的哪个方向。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [Mmad](../mmad_compute/mmad.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [Mmad](../../cube_compute_tensor_api/mmad_compute/mmad.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [Mmad计算辅助配置接口](../../cube_compute_tensor_api/mmad_compute_aux_config/mmad_compute_aux_config.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad计算辅助配置接口》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [Mmad辅助配置说明](mmad_compute_aux_config.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad辅助配置说明》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
<!-- cannbot:related:end -->
