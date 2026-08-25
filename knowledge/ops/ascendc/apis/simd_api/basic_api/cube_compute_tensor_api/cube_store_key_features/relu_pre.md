---
type: API
title: 随路Relu
description: enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/relu_pre.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 随路Relu

enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。

enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。 L0C Buffer到Unified Buffer搬运同样通过CopyL0C2UBTrait::enableRelu控制：

本接口属于 Cube 矩阵计算接口。

约束：enableRelu为编译期trait配置，默认不使能。；量化和Relu参数不能为inf、nan或非规格化数。；当前Tensor API不支持随路PRelu。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscGetL0c2gmRelu](../../../c_api/cube_compute/asc_get_l0c2gm_relu.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscGetL0c2gmRelu》具体提供“数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscSetL0c2gmConfig](../../../c_api/cube_compute/asc_set_l0c2gm_config.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscSetL0c2gmConfig》具体提供“数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscSetL0c2gmLreluAlpha](../../../c_api/cube_data_move/asc_set_l0c2gm_lrelu_alpha.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscSetL0c2gmLreluAlpha》具体提供“设置L0C搬运接口计算过程中使用的Leaky ReLU alpha值。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscSetL0c2gmReluAlpha](../../../c_api/sys_var/asc_set_l0c2gm_relu_alpha.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscSetL0c2gmReluAlpha》具体提供“设置RELU_ALPHA寄存器值，存储Scalar ReLU使用的alpha值。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [FixpipeL0CToGM](../../cube_compute/cube_compute_store/fixpipe_l0_c_to_gm.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《FixpipeL0CToGM》具体提供“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU和格式转换的组合接口。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [SetFixPipeClipRelu](../../cube_compute/cube_store_aux_config/set_fix_pipe_clip_relu.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《SetFixPipeClipRelu》具体提供“在L0C Buffer到GM搬运随路量化后，设置ClipReLU操作的最大值。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [SetFixPipeConfig](../../cube_compute/cube_store_aux_config/set_fix_pipe_config.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《SetFixPipeConfig》具体提供“DataCopy数据搬运（L0C Buffer->GM、L0C Buffer->L1 Buffer）过程中进行随路量化时，通过调用该接口设置量化的参数。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [矩阵搬出关键特性说明](../../cube_compute/cube_store_key_features/cube_store_key_features.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《矩阵搬出关键特性说明》具体提供“矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [矩阵搬出关键特性说明](cube_store_key_features.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《矩阵搬出关键特性说明》具体提供“矩阵搬出关键特性说明，包含随路量化、随路 Relu、F32 Channel Split、Int8 Channel Merge、batch 搬运等。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [矩阵搬出寄存器配置说明](../../cube_compute/cube_store_aux_config/cube_store_aux_config.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《矩阵搬出寄存器配置说明》具体提供“本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [随路ReLU](../../cube_compute/cube_store_key_features/accompanying_relu.md)（`related`）：ISASI 的 reluPre/clipReluPre 与 Tensor API 的 enableRelu 都在 L0C 搬出时完成 Normal ReLU，二者是两种编程接口下的同一随路能力。
- [随路量化与随路ReLU场景组合](../../cube_compute/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`same_topic`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《随路量化与随路ReLU场景组合》具体提供“矩阵搬出支持多种随路量化与随路ReLU的组合，芯片支持的全量场景组合参考下表，接下来将对下表中的随路量化ReLU算法逐一介绍。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
<!-- cannbot:related:end -->
