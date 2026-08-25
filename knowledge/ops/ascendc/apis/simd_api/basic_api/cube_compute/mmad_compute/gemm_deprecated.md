---
type: API
title: Gemm（废弃）
description: 该接口废弃，并将在后续版本移除，请不要使用该接口。 根据输入的切分规则，将给定的两个输入张量做矩阵乘，输出至结果张量。将A和B两个输入矩阵乘法在一起，得到一个输出矩阵C。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Gemm_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Gemm（废弃）

该接口已废弃，将在后续版本移除，请勿使用。根据切分规则将两个输入张量做矩阵乘，输出结果矩阵 C=A×B。

原型：Gemm(dst, src0, src1, m, k, n, tiling, partialsum=true, initValue=0)，tiling 通过 GetGemmTiling(m, k, n) 获取。仅 Atlas 推理系列产品 AI Core 和 Atlas 训练系列产品曾支持。请使用 Mmad 等接口替代。

<!-- cannbot:related:start -->
## 相关

- [废弃接口](../../../../appendix/deprecated_interface.md)（`related`）：Gemm（废弃）：Gemm 已废弃，附录确认废弃状态，正文明确把 Mmad 作为矩阵乘替代路径，因此两者形成可执行迁移关系。 目标卡《废弃接口》补充：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。
- [Mmad](mmad.md)（`same_topic`）：Gemm（废弃）：Gemm 已废弃，附录确认废弃状态，正文明确把 Mmad 作为矩阵乘替代路径，因此两者形成可执行迁移关系。 目标卡《Mmad》补充：矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
- [矩阵计算（ISASI）](mmad_compute.md)（`same_topic`）：矩阵计算（ISASI）：该集合明确以 Mmad替代废弃 Gemm/Conv2D，并要求 K方向对齐；所选卡分别给标准调用、迁移来源和最关键的输入约束，未把所有特化成员全连接。 目标卡《Gemm（废弃）》补充：该接口废弃，并将在后续版本移除，请不要使用该接口。 根据输入的切分规则，将给定的两个输入张量做矩阵乘，输出至结果张量。将A和B两个输入矩阵乘法在一起，得到一个输出矩阵C。
<!-- cannbot:related:end -->
