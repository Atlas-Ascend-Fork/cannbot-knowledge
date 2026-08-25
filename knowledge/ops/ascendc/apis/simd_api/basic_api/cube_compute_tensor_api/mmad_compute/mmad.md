---
type: API
title: Mmad
description: 完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute/Mmad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Mmad

完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C。计算公式：C = A * B，带bias时C = A * B + Bias。仅Ascend 950PR/950DT支持。试验接口。流水类型：PIPE_M。

函数原型通过模板参数指定AtomType（矩阵计算类型）、AntiQuantType（反量化类型）等。接口参数包含dstTensor（L0C输出）、srcTensorL0A（左矩阵A）、srcTensorL0B（右矩阵B）、biasTable（bias输入，可选）、tiling（MmadTiling切分信息）等。

MmadTiling包含M/N/K轴切分参数、迭代次数、数据类型信息等。约束：遵循Cube计算地址对齐和数据类型约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [AscHf32RoundMode](../../../c_api/enum/asc_hf32_round_mode.md)（`related`）：《AscHf32RoundMode》处理“用于Mmad计算开启HF32模式时FP32到HF32的舍入模式管理策略，在调用asc_set_hf32_round_mode时使用。”。《Mmad》明确“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”，可直接用于核对HF32 rounding/trans mode 的配置入口及其对 Mmad 执行精度的直接影响。
- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《Mmad》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [K方向对齐约束](../../cube_compute/mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：K方向对齐约束 与《Mmad》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad](../../cube_compute/mmad_compute/mmad.md)（`related`）：两张卡都执行 L0A×L0B 累加到 L0C 的 Mmad，但焦点是 Tensor API，候选是另一套基础接口与参数模型。
- [Mmad计算辅助配置接口](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：《Mmad》明确“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”；它与《Mmad计算辅助配置接口》的“Mmad计算辅助配置接口列表如下：”在实际调用参数、数据流或结果校验上直接衔接。
- [UnitFlag](../mmad_compute_key_features/unit_flag.md)（`related`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Mmad》提供“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [基础APIGEMV](../mmad_compute_key_features/gemv.md)（`related`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《Mmad》明确提供“完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C，支持普通模式和MX模式。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
- [基础APIHF32](../mmad_compute_key_features/hf32.md)（`related`）：焦点说明的 HF32 是 Tensor API Mmad 的输入精度模式；Mmad 卡给出实际消费该模式的矩阵乘契约。
- [SetMMColumnMajor/SetMMRowMajor](../../cube_compute/mmad_compute_aux_config/set_mm_column_major_set_mm_row_major.md)（`same_topic`）：SetMMColumnMajor/SetMMRowMajor 与《Mmad》的实质衔接是：SetMMColumnMajor/RowMajor 直接控制 Mmad/MmadWithSparse 生成方向；开启 unitFlag 且 Fixpipe 做 NZ2ND/ChannelMerge 时，方向选择还必须和搬出配置、UnitFlag 调优保持一致。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《Mmad》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
<!-- cannbot:related:end -->
