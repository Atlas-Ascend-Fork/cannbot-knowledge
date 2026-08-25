---
type: API
title: Int8 Channel Merge
description: Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/int8_channel_merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Int8 Channel Merge

Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置。

Int8 Channel Merge：当目标数据类型为`int8_t`或`uint8_t`时，NZ输出自动启用该特性。硬件会将分形矩阵从16×16扩展为16×32。若输出通道数N是16的偶数倍，则N方向上每两个相邻的16×16分形矩阵合并为一个16×32分形矩阵。若N是16的奇数倍，则前N - 16个通道参与合并，最后16个通道保持16×16分形矩阵不变。针对Ascend 950PR/Ascend 950DT，`hifloat8_t`、`fp8_e4m3fn_t`类型也支持该特性。

## 使用示例

Int8 Channel Merge：当目标数据类型为`int8_t`，M为32，N为48时，硬件会将N方向上前两个16×16分形矩阵合并成一个16×32分形矩阵，剩余的一个16×16分形矩阵保持不变并输出。

**图1**  Int8 Channel Merge示意图

## 约束说明

- Channel Merge为硬件自动使能，不能通过参数配置。
- Int8 Channel Merge在NZ输出且目的类型为`int8_t`或`uint8_t`时自动启用。Ascend 950PR/Ascend 950DT上`hifloat8_t`、`fp8_e4m3fn_t` NZ输出也支持该特性。

<!-- cannbot:related:start -->
## 相关

- [矩阵乘输出的Channel拆分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_output_channel_split.md)（`explains`）：矩阵乘输出的Channel拆分 与《Int8 Channel Merge》的实质衔接是：Channel split 的高低通道接口、Int8 merge、Fixpipe 地址、NZ2ND 与 M/N 方向设置共同实现 Matmul 输出拆分和恢复。
- [Copy](../cube_compute_store/copy_l0_c_to_gm.md)（`related`）：Int8 Channel Merge 只在 L0C→GM Copy 的目的格式为 NZ 且 dtype 为 int8/uint8（950 还含部分 FP8）时自动发生。
- [SetFixPipeAddr](../../cube_compute/cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《Int8 Channel Merge》说明Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [Int8 Channel Merge](../../cube_compute/cube_store_key_features/int8_channel_merge.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；Int8 Channel Merge正文说明“Channel Merge是矩阵计算结果搬出过程中的硬件自动合并能力，仅在目的格式NZ的输出场景生效，用户无需也不能通过参数手动配置”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
<!-- cannbot:related:end -->
