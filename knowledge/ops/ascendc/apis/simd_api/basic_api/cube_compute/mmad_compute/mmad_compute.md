---
type: API
title: 矩阵计算（ISASI）
description: 矩阵计算 ISASI Mmad 接口集，包含 Mmad、MmadMx、MmadBitMode、MmadWithSparse 等矩阵乘计算接口。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/mmad_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵计算（ISASI）

ISASI Cube 矩阵乘计算接口集合，提供 Mmad、MmadMx、MmadBitMode、MmadWithSparse 等矩阵乘算子。Mmad 为标准矩阵乘；MmadMx 支持混合精度输入；MmadBitMode 面向低比特量化场景；MmadWithSparse 用于稀疏矩阵乘。Conv2D、Gemm 接口已废弃，应使用对应新接口替代。接口作用对象为 Cube 单元，使用前需确认 K 方向对齐与数据类型约束。

<!-- cannbot:related:start -->
## 相关

- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《K方向对齐约束》补充：Atlas A2 训练系列产品/Atlas A2 推理系列产品/Atlas A3 训练系列产品/Atlas A3 推理系列产品，Mmad接口支持开启此特性。
- [Mmad辅助配置说明](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：Mmad辅助配置说明 与《矩阵计算（ISASI）》的衔接是：该配置组中的列主序/行主序与 HF32 选项会被 Mmad 执行直接消费；Tensor API 的对应辅助配置提供同一矩阵乘契约下的另一套入口。
- [Conv2D（废弃）](conv2_d_deprecated.md)（`same_topic`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《Conv2D（废弃）》补充：该接口废弃，并将在后续版本移除，请不要使用该接口。 计算给定输入张量和权重张量的2-D卷积，输出结果张量。Conv2D卷积层多用于图像识别，使用过滤器提取图像中的特征。
- [Gemm（废弃）](gemm_deprecated.md)（`same_topic`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《Gemm（废弃）》补充：该接口废弃，并将在后续版本移除，请不要使用该接口。 根据输入的切分规则，将给定的两个输入张量做矩阵乘，输出至结果张量。将A和B两个输入矩阵乘法在一起，得到一个输出矩阵C。
- [Mmad](mmad.md)（`same_topic`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《Mmad》补充：矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
<!-- cannbot:related:end -->
