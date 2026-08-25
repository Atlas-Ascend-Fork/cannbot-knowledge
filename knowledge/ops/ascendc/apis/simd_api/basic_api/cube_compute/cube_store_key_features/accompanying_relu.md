---
type: API
title: 随路ReLU
description: 矩阵计算的搬出过程中支持随路ReLU能力，当前支持如下随路ReLU能力。DataCopyCO12DstParams结构体参数定义中reluPre可设置为1开启Normal
  ReLU，结合clipReluPre可进一步开启ClipReLU能力。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/accompanying_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 随路ReLU

## 特性说明

矩阵计算的搬出过程中支持随路ReLU能力，当前支持如下随路ReLU能力。**DataCopyCO12DstParams结构体参数**定义中reluPre可设置为1开启Normal ReLU，结合clipReluPre可进一步开启ClipReLU能力。

- 参数配置为0时，即不开启随路ReLU能力。

- 参数配置为1时，即Normal ReLU，无需配置额外寄存器，对输出数据执行激活处理：`y = max(0, x)`。

- 开启Normal ReLU（reluPre=1）且同时配置clipReluPre=1并调用SetFixPipeClipRelu接口时，即Normal ReLU + ClipReLU，先执行`y = max(0, x)`，再执行`y = min(clipReluMaxVal, y)`，其中clipReluMaxVal通过SetFixPipeClipRelu接口设置。详见SetFixPipeClipRelu。

与随路量化组合使用的详细信息请参考随路量化与随路ReLU场景组合。

<!-- cannbot:related:start -->
## 相关

- [AccompanyingQuantization](accompanying_quantization.md)（`related`）：AccompanyingQuantization 定义与随路 ReLU 可组合的 scalar/tensor 量化模式，二者共同决定搬出后的 cast、quant 和激活次序。
- [AscCopyL0c2Gm](../../../c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：随路ReLU说明矩阵计算的搬出过程中支持随路ReLU能力，当前支持如下随路ReLU能力。DataCopyCO12DstParams结构体参数定义中reluPre可设置为1开启Normal ReLU，结合clipReluPre可进一步开启ClipReLU能力。
- [AscSetL0c2gmReluAlpha](../../../c_api/sys_var/asc_set_l0c2gm_relu_alpha.md)（`related`）：随路 ReLU 特性说明解释 RELU_ALPHA 在 L0C 搬出时如何参与 Scalar ReLU。
- [SetFixPipeAddr](../cube_store_aux_config/set_fix_pipe_addr.md)（`related`）：《SetFixPipeAddr》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路量化后，通过调用该接口设置Elementwise操作时LocalTensor的地址。；《随路ReLU》说明矩阵计算的搬出过程中支持随路ReLU能力，当前支持如下随路ReLU能力。DataCopyCO12DstParams结构体参数定义中reluPre可设置为1开启Normal ReLU，结合clipReluPre可进一步开启ClipReLU能力。。二者在SetFixPipeAddr为L0C搬出随路Elementwise步骤提供LocalTensor地址，需与Fixpipe路径、量化/ReLU和Channel处理配置配套上存在可执行的直接衔接。
- [SetFixPipeClipRelu](../cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：开启 reluPre 与 clipReluPre 后必须调用 SetFixPipeClipRelu 设置 clipReluMaxVal，该接口完成随路 ClipReLU 的上界配置。
- [SetFixPipeConfig](../cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《随路ReLU》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [矩阵搬出关键特性说明](cube_store_key_features.md)（`related`）：ISASI 矩阵搬出关键特性页把随路 ReLU 定位在 L0C 到 GM/UB/L1 的 FixPipe 后处理链，并关联格式转换、通道处理和量化。
- [矩阵搬出关键特性说明](../../cube_compute_tensor_api/cube_store_key_features/cube_store_key_features.md)（`related`）：Tensor API 搬出特性页说明 ReLU 与量化可在 L0C 到 GM/UB 搬运时一起完成，解释 enableRelu 版本能力的执行位置。
- [矩阵搬出寄存器配置说明](../cube_store_aux_config/cube_store_aux_config.md)（`related`）：矩阵搬出寄存器配置说明 与《随路ReLU》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：ISASI 的 reluPre/clipReluPre 与 Tensor API 的 enableRelu 都在 L0C 搬出时完成 Normal ReLU，二者是两种编程接口下的同一随路能力。
- [AscGetL0c2gmRelu](../../../c_api/cube_compute/asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《随路ReLU》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [随路量化与随路ReLU场景组合](accompanying_quantization_and_relu_scenario_combination.md)（`same_topic`）：随路量化与 ReLU 组合页给出 M1/M2 在 no ReLU、Normal ReLU 及不同 quantPre 模式下的取值，是随路 ReLU 与量化同时开启时的约束矩阵。
<!-- cannbot:related:end -->
