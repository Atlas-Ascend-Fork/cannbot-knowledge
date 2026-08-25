---
type: API
title: K方向对齐约束
description: Atlas A2 训练系列产品/Atlas A2 推理系列产品/Atlas A3 训练系列产品/Atlas A3 推理系列产品，Mmad接口支持开启此特性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/k_direction_alignment_constraint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# K方向对齐约束

通过 MmadParams.kDirectionAlign 控制 float 数据类型时 L0A/L0B Buffer 矩阵 K 方向对齐方式。true 对齐到 ceil(K/16)×16，false 对齐到 ceil(K/8)×8。A 矩阵非转置场景无需开启；转置场景需开启以避免读入无效数据。950 的 L0A Buffer 为 NZ 排布，K 方向 8 对齐，无需此特性。仅 a2/a3 支持。

<!-- cannbot:related:start -->
## 相关

- [AscMmad](../../../c_api/cube_compute/asc_mmad.md)（`related`）：AscMmad 与《K方向对齐约束》的实质衔接是：AscMmad 在 AIC 上消费 L0A/L0B 并累加到 L0C；Mmad 约束、方向/HF32 配置、Cube 流程和 AIV 误调用故障共同覆盖实际调用边界。
- [Cube计算(ISASI)HF32](hf32.md)（`related`）：启用 HF32 并不消除 K 方向对齐约束；矩阵 shape 仍需同时满足该硬件条件。
- [Mmad](../mmad_compute/mmad.md)（`related`）：K方向对齐约束 与《Mmad》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad](../../cube_compute_tensor_api/mmad_compute/mmad.md)（`related`）：K方向对齐约束 与《Mmad》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [MmadWithSparse](../mmad_compute/mmad_with_sparse.md)（`related`）：K方向对齐约束 与《MmadWithSparse》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad计算关键特性说明](mmad_compute_key_features.md)（`related`）：K方向对齐约束 与《Mmad计算关键特性说明》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [Mmad辅助配置说明](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：K方向对齐约束 与《Mmad辅助配置说明》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [SetHF32TransMode](../mmad_compute_aux_config/set_hf32_trans_mode.md)（`related`）：K方向对齐约束 与《SetHF32TransMode》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [UnitFlag](unit_flag.md)（`related`）：使用 UnitFlag 优化流水仍需满足 K 方向对齐，不能用同步标志绕过 shape 约束。
- [矩阵计算输入搬运约束](../cube_compute_load/cube_compute_input_move_constraint.md)（`related`）：K方向对齐约束 与《矩阵计算输入搬运约束》的实质衔接是：K 对齐由 Mmad 的输入格式、数据搬运与参数配置共同决定；普通、Tensor API 和稀疏 Mmad 均需按该约束选择 K 长度及转换模式。
- [矩阵计算（ISASI）](../mmad_compute/mmad_compute.md)（`related`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《K方向对齐约束》补充：Atlas A2 训练系列产品/Atlas A2 推理系列产品/Atlas A3 训练系列产品/Atlas A3 推理系列产品，Mmad接口支持开启此特性。
- [基础APIGEMV](../../cube_compute_tensor_api/mmad_compute_key_features/gemv.md)（`same_topic`）：《基础APIGEMV》处理“GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。”。《K方向对齐约束》明确提供“Atlas A2 训练系列产品/Atlas A2 推理系列产品/Atlas A3 训练系列产品/Atlas A3 推理系列产品，Mmad接口支持开启此特性。”，其参数、调用或验证步骤直接接入GEMV 的 Mmad 形状、行主序布局、对齐、Tiling 和结果验证。
<!-- cannbot:related:end -->
