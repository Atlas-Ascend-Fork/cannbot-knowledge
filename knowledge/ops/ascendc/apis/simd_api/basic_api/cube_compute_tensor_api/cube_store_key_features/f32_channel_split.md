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

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《F32 Channel Split》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [SetFixPipeAddr](../../cube_compute/cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《F32 Channel Split》说明F32 Channel Split是矩阵计算结果搬出过程中的通道拆分能力。当源类型和目的类型均为float、目的格式为NZ，且CopyL0C2GMTrait::enableChannelSplit或CopyL0C2UBTrait::enableChannelSplit设置为true时，硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [F32 Channel Split](../../cube_compute/cube_store_key_features/f32_channel_split.md)（`same_topic`）：《F32 Channel Split》明确“矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。”；它与《F32 Channel Split》的“F32 Channel Split是矩阵计算结果搬出过程中的通道拆分能力。当源类型和目的类型均为float、目的格式为NZ，且CopyL0C2GMTrait::enableChannelSplit或CopyL0C2UBTrait::enableChannelSplit设置为true时，硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
