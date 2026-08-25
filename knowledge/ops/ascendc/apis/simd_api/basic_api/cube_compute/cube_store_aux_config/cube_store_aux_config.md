---
type: API
title: 矩阵搬出寄存器配置说明
description: 本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_aux_config/cube_store_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬出寄存器配置说明

矩阵计算 ISASI 搬出阶段的 Fixpipe 寄存器配置接口集。
涉及寄存器在相同核函数内部维持状态直到被人为改变，不同核函数之间不继承之前的状态。
包含 SetFixPipeConfig 设置总体配置，SetFixpipePreQuantFlag 控制随路量化开关，SetFixpipeNz2ndFlag 控制 NZ 到 ND 格式转换，SetFixPipeClipRelu 设置裁剪与 ReLU，SetFixPipeAddr 设置搬出地址。

<!-- cannbot:related:start -->
## 相关

- [设置合理的L2 CacheMode](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：矩阵搬出寄存器配置说明 与《设置合理的L2 CacheMode》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [AccompanyingQuantization](../cube_store_key_features/accompanying_quantization.md)（`related`）：矩阵搬出寄存器配置说明 与《AccompanyingQuantization》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [NZ2ND](../cube_store_key_features/nz2_nd.md)（`related`）：矩阵搬出寄存器配置说明 与《NZ2ND》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [SetFixpipeNz2ndFlag](set_fixpipe_nz2nd_flag.md)（`related`）：《SetFixpipeNz2ndFlag》说明DataCopy数据搬运（L0C Buffer->GM）过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；《矩阵搬出寄存器配置说明》说明本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。。二者在NZ2ND标志控制Fixpipe L0C搬出格式，必须与Fixpipe配置、L0C到GM搬运、C接口和卷积格式转换保持一致上存在可执行的直接衔接。
- [矩阵计算的搬出](../cube_compute_store/cube_compute_store.md)（`related`）：矩阵搬出寄存器配置说明 与《矩阵计算的搬出》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [随路ReLU](../cube_store_key_features/accompanying_relu.md)（`related`）：矩阵搬出寄存器配置说明 与《随路ReLU》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [随路Relu](../../cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《矩阵搬出寄存器配置说明》具体提供“本章节涉及寄存器在相同核函数内部会维持状态直到被人为改变，而在不同核函数内部不会继承之前的状态。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [随路量化与随路ReLU场景组合](../cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`related`）：矩阵搬出寄存器配置说明 与《随路量化与随路ReLU场景组合》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [SetFixPipeAddr](set_fix_pipe_addr.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixPipeAddr》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [SetFixPipeClipRelu](set_fix_pipe_clip_relu.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixPipeClipRelu》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [SetFixPipeConfig](set_fix_pipe_config.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixPipeConfig》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [SetFixpipePreQuantFlag](set_fixpipe_pre_quant_flag.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《SetFixpipePreQuantFlag》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
- [矩阵搬出关键特性说明](../cube_store_key_features/cube_store_key_features.md)（`same_topic`）：矩阵搬出寄存器配置说明 与《矩阵搬出关键特性说明》的实质衔接是：矩阵搬出配置寄存器在核内持久，SetFixPipeConfig/NZ2ND/Addr/Relu/PreQuant 控制 Fixpipe 搬出；量化、ReLU、L2 和格式转换材料说明各状态的真实效果。
<!-- cannbot:related:end -->
