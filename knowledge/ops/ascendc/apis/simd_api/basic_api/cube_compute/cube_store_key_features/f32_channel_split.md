---
type: API
title: F32 Channel Split
description: 矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/F32-Channel-Split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# F32 Channel Split

## 特性说明

矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。

对于DataCopy接口，可以通过配置**DataCopyCO12DstParams结构体参数**定义中channelSplit为true开启。

对于Fixpipe接口，可以通过配置Fixpipe搬运参数结构体说明中channelSplit为true开启。

## 特性约束

- 针对如下产品型号：


    Atlas A3 训练系列产品/Atlas A3 推理系列产品



    Atlas A2 训练系列产品/Atlas A2 推理系列产品


    当Fixpipe指令的输入和输出数据类型都为float，NZ输出到GM，并且不开启NZ2ND与unitFlag时，才能够开启Channel Split功能。

- 针对Ascend 950PR/Ascend 950DT，当Fixpipe指令的输入和输出数据类型都为float,NZ输出到GM，并且不开启NZ2ND、NZ2DN与unitFlag时，才能够开启Channel Split功能。当前搬出到L1 Buffer和UB不支持该功能。

## 使用示例

完整示例请参考fixpipe_l0c2gm样例场景7。

如下图所示，当开启Channel Split功能后，shape为[64,32]的源操作数将会被拆分为16个独立的16x8分形矩阵。

**图1** F32 Channel Split示意图（无无效数据）

当开启Channel Split功能后，nSize（源NZ矩阵在N方向上的大小）必须为8的倍数。如下图所示，shape为[64,24]的源操作数将会被拆分为3列16x8分形矩阵。

**图2** F32 Channel Split示意图（有无效数据）

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《F32 Channel Split》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [AscSetL0c2gmChannelPara](../../../c_api/sys_var/asc_set_l0c2gm_channel_para.md)（`related`）：F32 Channel Split说明矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵；对AscSetL0c2gmChannelPara而言，ChannelPara 只在 NZ2DN 的 L0C 搬运前生效；Channel Split 的格式限制和 AscCopyL0c2Gm 的参数共同界定有效调用。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《F32 Channel Split》说明矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [矩阵搬出关键特性说明](../../cube_compute_tensor_api/cube_store_key_features/cube_store_key_features.md)（`related`）：矩阵搬出关键特性说明说明矩阵搬出关键特性说明，包含随路量化、随路 Relu、F32 Channel Split、Int8 Channel Merge、batch 搬运等；对F32 Channel Split而言，Channel Split 是 L0C 搬出关键特性，只有总览补齐其与格式转换、量化、ReLU 组合时的选型约束。
- [F32 Channel Split](../../cube_compute_tensor_api/cube_store_key_features/f32_channel_split.md)（`same_topic`）：《F32 Channel Split》明确“矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。”；它与《F32 Channel Split》的“F32 Channel Split是矩阵计算结果搬出过程中的通道拆分能力。当源类型和目的类型均为float、目的格式为NZ，且CopyL0C2GMTrait::enableChannelSplit或CopyL0C2UBTrait::enableChannelSplit设置为true时，硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
