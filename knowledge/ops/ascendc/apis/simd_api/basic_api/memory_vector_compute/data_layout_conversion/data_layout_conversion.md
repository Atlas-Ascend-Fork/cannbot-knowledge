---
type: API
title: 数据排布转换
description: 矢量数据排布转换接口集，包含 Transpose、TransDataTo5HD 等数据布局转换接口。
tags: [task.lookup, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_layout_conversion/data_layout_conversion.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 数据排布转换

提供 Transpose 和 TransDataTo5HD 两个数据布局转换接口。

Transpose 用于实现 16×16 二维矩阵数据块转置，增强模式还支持 NCHW 与 NHWC 格式互转。TransDataTo5HD 用于将 NCHW 格式转换为 NC1HWC0 格式，也可用于二维矩阵转置；相比 Transpose 仅支持 16×16，TransDataTo5HD 单次 repeat 可处理 512Byte 数据（16 个 DataBlock），支持不同 shape 的矩阵转置和多次 repeat 操作。操作数起始地址需 32Byte 对齐。
