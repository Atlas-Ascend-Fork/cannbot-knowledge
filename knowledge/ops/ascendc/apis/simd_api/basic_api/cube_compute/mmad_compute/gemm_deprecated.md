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
