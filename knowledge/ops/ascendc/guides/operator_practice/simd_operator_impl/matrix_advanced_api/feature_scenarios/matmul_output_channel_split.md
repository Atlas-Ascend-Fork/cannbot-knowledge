---
type: Guide
title: 矩阵乘输出的Channel拆分
description: 将NZ格式float类型C矩阵的分形从16x16切分为16x8，使内轴满足32字节对齐便于后续矢量计算。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵乘输出的Channel拆分

## 功能介绍
矩阵乘输出的Channel拆分，又称ChannelSplit。指当Matmul计算结果C矩阵的格式为NZ时，C矩阵采用分形存储，关于NZ格式的详细内容请参考数据格式。当C矩阵的物理排布格式为NZ、数据类型为float时，默认情况下，每个分形内部包含16*16个元素，即分形的大小为16*16。ChannelSplit的功能为将此场景下C矩阵的每个16*16的分形切分为16*8的分形，使得C矩阵按照16*8的分形进行存储。
由于1个float类型数据的大小为4字节，16*8的分形在内轴满足32字节对齐，内轴上的数据量与一条NPU矢量计算指令处理的数据单元一致，这便于后续的其它计算。ChannelSplit功能默认不启用，用户需通过设置MatmulConfig中的isEnableChannelSplit参数为true来开启此功能。
## 使用场景
对于NZ格式、float类型的C矩阵，需要按16*8的分形存储时，使用该功能。
## 约束说明
开启ChannelSplit功能需满足：
-   C矩阵的数据排布格式为CubeFormat::NZ。
-   C矩阵的数据类型为float。
-   C矩阵的内存逻辑位置为Global Memory。
-   矩阵乘结果L0C Buffer（CO1）数据类型为float。

<!-- cannbot:related:start -->
## 相关

- [F32 Channel Split](../../../../../apis/simd_api/basic_api/cube_compute/cube_store_key_features/f32_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分，又称ChannelSplit。指当Matmul计算结果C矩阵的格式为NZ时，C矩阵采用分形存储，关于NZ格式的详细内容请参考数据格式。当C矩阵的物理排布格式为NZ、数据类型为float时，默认情况下，每个分形内部包含16*16个元素，即分形的大小为16*16。ChannelSplit的功能为将此场景下C矩阵的每个16*16的分形切分为16*8的分形，使得C矩阵按照16*8的分形进行存储。；矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。；两端描述同一 F32 NZ Channel Split 存储变换，指南给场景，API 给硬件搬出合同。
- [F32 Channel Split](../../../../../apis/simd_api/basic_api/cube_compute_tensor_api/cube_store_key_features/f32_channel_split.md)（`explains`）：硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。；ChannelSplit的功能为将此场景下C矩阵的每个16*16的分形切分为16*8的分形，使得C矩阵按照16*8的分形进行存储。；两卡描述同一 F32 NZ ChannelSplit 核心对象，API 卡给硬件行为，Guide 给启用方式与使用约束。
<!-- cannbot:related:end -->
