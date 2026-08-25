---
type: API
title: AscSetL0c2gmConfig
description: 数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_l0c2gm_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL0c2gmConfig

数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。

参数：relu_pre(输入): ReLU操作前矢量的起始地址。；quant_pre(输入): 量化操作前矢量的起始地址。；enable_unit_flag(输入): 是否启用unit_flag。unit_flag是一种矩阵计算指令和矩阵搬运指令细粒度的并行，开启该功能后，硬件每计算完一个分形，计算结果就会被搬出，该功能。

约束：支持以下三种传参形式
- 同时设置relu_pre和quant_pre。
- 仅传入relu_pre，quant_pre传入0。
- 仅传入quant_pre，relu_pre传入0。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetL0c2gmUnitflag](asc_get_l0c2gm_unitflag.md)（`related`）：AscSetL0c2gmConfig 写入随路量化及 unit_flag 等配置，AscGetL0c2gmUnitflag 从同一 L0C→GM 状态读取该标志。
- [SetFixPipeConfig](../../basic_api/cube_compute/cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《AscSetL0c2gmConfig》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [随路Relu](../../basic_api/cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscSetL0c2gmConfig》具体提供“数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscGetL0c2gmPrequant](asc_get_l0c2gm_prequant.md)（`same_topic`）：AscGetL0c2gmPrequant 与《AscSetL0c2gmConfig》的实质衔接是：AscGetL0c2gmPrequant 读取随路量化前矢量地址，AscSetL0cCopyPrequant、总配置和 C++ prequant flag 是写入并启用同一状态的控制端。
- [AscGetL0c2gmRelu](asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscSetL0c2gmConfig》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [AscSetL0c2gmQuantPost](../sys_var/asc_set_l0c2gm_quant_post.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscSetL0c2gmConfig正文说明“数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
- [UnitFlag](../../basic_api/cube_compute_tensor_api/mmad_compute_key_features/unit_flag.md)（`same_topic`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《AscSetL0c2gmConfig》提供“数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的矢量量化参数。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
<!-- cannbot:related:end -->
