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

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分，又称ChannelSplit。指当Matmul计算结果C矩阵的格式为NZ时，C矩阵采用分形存储，关于NZ格式的详细内容请参考数据格式。当C矩阵的物理排布格式为NZ、数据类型为float时，默认情况下，每个分形内部包含16*16个元素，即分形的大小为16*16。ChannelSplit的功能为将此场景下C矩阵的每个16*16的分形切分为16*8的分形，使得C矩阵按照16*8的分形进行存储。；矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。；两端描述同一 F32 NZ Channel Split 存储变换，指南给场景，API 给硬件搬出合同。
<!-- cannbot:related:end -->
