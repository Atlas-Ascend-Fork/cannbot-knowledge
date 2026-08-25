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

- [AscSetMmadDirectionM](../../../../../apis/simd_api/c_api/cube_compute/asc_set_mmad_direction_m.md)（`explains`）：《AscSetMmadDirectionM》说明设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。；《矩阵乘输出的Channel拆分》说明将NZ格式float类型C矩阵的分形从16x16切分为16x8，使内轴满足32字节对齐便于后续矢量计算。。二者在M/N方向配置改变Mmad输入分形与行列主序，必须在AscMmad/Mmad调用和输出Channel拆分前保持一致上存在可执行的直接衔接。
- [AscSetMmadDirectionN](../../../../../apis/simd_api/c_api/cube_compute/asc_set_mmad_direction_n.md)（`explains`）：矩阵乘输出的Channel拆分 与《AscSetMmadDirectionN》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [F32 Channel Split](../../../../../apis/simd_api/basic_api/cube_compute/cube_store_key_features/f32_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《F32 Channel Split》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [F32 Channel Split](../../../../../apis/simd_api/basic_api/cube_compute_tensor_api/cube_store_key_features/f32_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《F32 Channel Split》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [Int8 Channel Merge](../../../../../apis/simd_api/basic_api/cube_compute/cube_store_key_features/int8_channel_merge.md)（`explains`）：矩阵乘输出的Channel拆分 与《Int8 Channel Merge》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [Int8 Channel Merge](../../../../../apis/simd_api/basic_api/cube_compute_tensor_api/cube_store_key_features/int8_channel_merge.md)（`explains`）：矩阵乘输出的Channel拆分 与《Int8 Channel Merge》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [NZ2ND](../../../../../apis/simd_api/basic_api/cube_compute/cube_store_key_features/nz2_nd.md)（`explains`）：矩阵乘输出的Channel拆分 与《NZ2ND》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [SetFixPipeAddr](../../../../../apis/simd_api/basic_api/cube_compute/cube_store_aux_config/set_fix_pipe_addr.md)（`explains`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《矩阵乘输出的Channel拆分》说明将NZ格式float类型C矩阵的分形从16x16切分为16x8，使内轴满足32字节对齐便于后续矢量计算。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [多核对齐切分](multi_core_aligned_split.md)（`same_topic`）：多核对齐切分 与《矩阵乘输出的Channel拆分》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
<!-- cannbot:related:end -->
