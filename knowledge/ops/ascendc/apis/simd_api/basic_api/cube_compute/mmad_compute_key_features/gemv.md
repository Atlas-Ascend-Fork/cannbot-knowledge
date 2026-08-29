---
type: API
title: Cube计算(ISASI)GEMV
description: Gemv的核心功能体现为：当矩阵A的维度M取值为1时，接口会自动启用Gemv功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/GEMV.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Cube计算(ISASI)GEMV

当 Mmad 的矩阵 A 维度 M=1 时，接口自动启用 GEMV 模式，退化为 1×K 行向量与 K×N 矩阵的乘法。950 可通过 MmadParams.disableGemv=true 关闭。

约束：1×K 矩阵 A 需 512B 地址对齐，K 个数据连续存储；C 矩阵为 1×N 向量，每个 1×16 子向量在 L0C Buffer 占 1024B，有效数据仅 32B 或 64B。GEMV 模式相较于非对齐处理方式搬运数据量更少、性能更好。
