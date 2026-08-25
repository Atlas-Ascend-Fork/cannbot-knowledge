---
type: API
title: Int8 Channel Merge
description: 矩阵计算的搬出过程中对于目标数据类型被转换为int8_t、uint8_t的情况，NZ输出时该特性自动启用。硬件会将分形矩阵从16×16扩展为16×32。具体规则如下：若输出通道数N是16的偶数倍，则在N方向上，每两个相邻的16×16分形矩阵将合并为一个单一的16×32分形矩阵。若N是16的奇数倍，则通道1至通道（N–16）将被合并，而最后16个通道保持不变，不进行合并。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/Int8-Channel-Merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Int8 Channel Merge

## 特性说明

矩阵计算的搬出过程中对于目标数据类型被转换为int8_t、uint8_t的情况，NZ输出时该特性自动启用。硬件会将分形矩阵从16×16扩展为16×32。具体规则如下：若输出通道数N是16的偶数倍，则在N方向上，每两个相邻的16×16分形矩阵将合并为一个单一的16×32分形矩阵。若N是16的奇数倍，则通道1至通道（N–16）将被合并，而最后16个通道保持不变，不进行合并。

## 特性约束

硬件自动开启，不能配置。

## 使用示例

例如，当目标数据类型为s8，M为32，N为48时，硬件会先将N方向上前两个16×16的分形矩阵合并成一个16×32的矩阵，然后将剩余的16×16分形矩阵直接搬运至L1 Buffer。

**图1** Int8 Channel Merge示意图

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《Int8 Channel Merge》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《Int8 Channel Merge》说明矩阵计算的搬出过程中对于目标数据类型被转换为int8_t、uint8_t的情况，NZ输出时该特性自动启用。硬件会将分形矩阵从16×16扩展为16×32。具体规则如下：若输出通道数N是16的偶数倍，则在N方向上，每两个相邻的16×16分形矩阵将合并为一个单一的16×32分形矩阵。若N是16的奇数倍，则通道1至通道（N–16）将被合并，而最后16个通道保持不变，不进行合并。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [AccompanyingQuantization](accompanying_quantization.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；AccompanyingQuantization正文说明“矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
- [AscSetL0c2gmChannelPara](../../../c_api/sys_var/asc_set_l0c2gm_channel_para.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；AscSetL0c2gmChannelPara正文说明“设置通道步长寄存器比特位，配合L0C搬运接口使用”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
- [Copy](../../cube_compute_tensor_api/cube_compute_store/copy_l0_c_to_gm.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；Copy正文说明“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
- [Int8 Channel Merge](../../cube_compute_tensor_api/cube_store_key_features/int8_channel_merge.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；Int8 Channel Merge正文说明“Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
- [基础API随路量化](../../cube_compute_tensor_api/cube_store_key_features/quant_pre.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；基础API随路量化正文说明“随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
- [矩阵计算的搬出总体说明](../../cube_compute_tensor_api/cube_compute_store/overall_description.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；矩阵计算的搬出总体说明正文说明“矩阵计算的搬出接口主要实现L0C Buffer与Global Memory、Unified Buffer之间的数据高效传输”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
<!-- cannbot:related:end -->
