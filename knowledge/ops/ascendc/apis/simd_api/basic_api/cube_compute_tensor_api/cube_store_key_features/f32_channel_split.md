---
type: API
title: F32 Channel Split
description: F32 Channel Split是矩阵计算结果搬出过程中的通道拆分能力。当源类型和目的类型均为float、目的格式为NZ，且CopyL0C2GMTrait::enableChannelSplit或CopyL0C2UBTrait::enableChannelSplit设置为true时，硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/f32_channel_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# F32 Channel Split

F32 Channel Split是矩阵计算结果搬出过程中的通道拆分能力。当源类型和目的类型均为float、目的格式为NZ，且CopyL0C2GMTrait::enableChannelSplit或CopyL0C2UBTrait::enableChannelSplit设置为true时，硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。

本接口属于 Cube 矩阵计算接口。

约束：F32 Channel Split仅支持源类型和目的类型均为float，目的格式为NZ。；启用F32 Channel Split时，不能同时使能unitFlag，N方向大小必须为8的倍数。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。；ChannelSplit的功能为将此场景下C矩阵的每个16*16的分形切分为16*8的分形，使得C矩阵按照16*8的分形进行存储。；两卡描述同一 F32 NZ ChannelSplit 核心对象，API 卡给硬件行为，Guide 给启用方式与使用约束。
<!-- cannbot:related:end -->
