---
type: API
title: SetFixPipeAddr
description: DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/SetFixPipeAddr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# SetFixPipeAddr

DataCopy 数据搬运（L0C Buffer→GM）过程中进行随路量化后，设置 Elementwise 操作时 LocalTensor 的地址。

参数：eleWiseData 为 L1 Buffer 上的源操作数（LocalTensor，TPosition A1/B1/C1，32B 对齐，仅支持 half）；c0ChStride 为 L1 Buffer 上的 C0 channel stride，单位 C0_SIZE（32B），表示沿 N 方向以 C0 为单位切分的数据块间隔。仅 Atlas 200I/500 A2 推理产品支持。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《矩阵乘输出的Channel拆分》说明将NZ格式float类型C矩阵的分形从16x16切分为16x8，使内轴满足32字节对齐便于后续矢量计算。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《AccompanyingQuantization》说明矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [CopyL1ToFixpipe](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_fixpipe.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《CopyL1ToFixpipe》说明通过Tensor API的Copy接口将L1 Buffer中的量化数据搬运到Fixpipe Buffer，用于L0C输出时随路量化。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [F32 Channel Split](../cube_store_key_features/f32_channel_split.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《F32 Channel Split》说明矩阵计算的搬出过程中对于目标类型为f32，如果开启了Channel Split（通道拆分），硬件就能够将16×16的分形矩阵转换为16×8的小z分形矩阵，此时每个16×16的分形矩阵将被拆分为2个独立的16×8的小z分形矩阵。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [F32 Channel Split](../../cube_compute_tensor_api/cube_store_key_features/f32_channel_split.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《F32 Channel Split》说明F32 Channel Split是矩阵计算结果搬出过程中的通道拆分能力。当源类型和目的类型均为float、目的格式为NZ，且CopyL0C2GMTrait::enableChannelSplit或CopyL0C2UBTrait::enableChannelSplit设置为true时，硬件会将16×16的分形矩阵拆分为两个独立的16×8小Z分形矩阵。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [FixpipeL0CToGM](../cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《FixpipeL0CToGM》说明将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [FixpipeL0CToUB](../cube_compute_store/fixpipe_l0_c_to_ub.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《FixpipeL0CToUB》说明将L0C Buffer中的矩阵计算结果搬运至Unified Buffer，支持随路量化和格式转换。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [Int8 Channel Merge](../cube_store_key_features/int8_channel_merge.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《Int8 Channel Merge》说明矩阵计算的搬出过程中对于目标数据类型被转换为int8_t、uint8_t的情况，NZ输出时该特性自动启用。硬件会将分形矩阵从16×16扩展为16×32。具体规则如下：若输出通道数N是16的偶数倍，则在N方向上，每两个相邻的16×16分形矩阵将合并为一个单一的16×32分形矩阵。若N是16的奇数倍，则通道1至通道（N–16）将被合并，而最后16个通道保持不变，不进行合并。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [Int8 Channel Merge](../../cube_compute_tensor_api/cube_store_key_features/int8_channel_merge.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《Int8 Channel Merge》说明Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [随路ReLU](../cube_store_key_features/accompanying_relu.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《随路ReLU》说明矩阵计算的搬出过程中支持随路ReLU能力，当前支持如下随路ReLU能力。DataCopyCO12DstParams结构体参数定义中reluPre可设置为1开启Normal ReLU，结合clipReluPre可进一步开启ClipReLU能力。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [随路量化与随路ReLU场景组合](../cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《随路量化与随路ReLU场景组合》说明矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeConfig](set_fix_pipe_config.md)（`same_topic`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《SetFixPipeConfig》说明DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [矩阵搬出寄存器配置说明](cube_store_aux_config.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixPipeAddr》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
<!-- cannbot:related:end -->
