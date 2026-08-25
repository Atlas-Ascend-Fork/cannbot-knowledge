---
type: API
title: MaskMergeMode
description: 枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/MaskMergeMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# MaskMergeMode

枚举类型，用于指定寄存器数据写入模式，包括ZEROING置零和MERGING保留原值两种模式。

本接口属于 Reg 矢量计算辅助数据类型定义。

# MaskMergeMode | 参数名 | 描述 | | :-- | :-- | | MaskMergeMode | 用于指定写入寄存器数据模式。 enum class MaskMergeMode { UNKNOWN, MERGING, ZEROING }; • UNKNOWN：当转换类型不支持MaskMergeMode时，选择该模式； • ZEROING：mask未选择的元素在dst中置零； • MERGING：mask未选择的元素对应dst元素中保留dst原值。 | 以Duplicate接口为例，ZEROING和MERGING模式图示如下： 图1 ZEROING/MERGING对比

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
