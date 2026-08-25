---
type: API
title: 辅助数据结构
description: AscendC 矢量计算基础 API 的辅助数据结构总览，涵盖 Coordinate、Layout、TensorTrait、TensorDesc 等类型与参数结构。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/aux_data_structures.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 辅助数据结构

Ascend C 矢量计算基础 API 辅助数据结构总览页，提供张量描述、排布与计算参数的结构化表示。
涵盖 Coordinate 坐标、Layout 排布、TensorTrait 布局承载、TensorDesc 张量描述、ShapeInfo 形状信息、ListTensorDesc 张量描述列表等数据结构。
另包含 UnaryRepeatParams/BinaryRepeatParams 重复参数、complex32/complex64 复数类型及 TPosition 位置枚举，用于矢量计算接口的参数传递与配置。
