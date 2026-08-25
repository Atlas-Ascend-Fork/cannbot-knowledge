---
type: API
title: AscSetL0cCopyPrequant
description: 设置数据搬运随路量化流程中的标量量化参数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l0c_copy_prequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL0cCopyPrequant

数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的标量量化参数。

参数：config(输入): 量化过程中使用到的标量量化参数。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：《AscCopyL0c2Gm》明确“将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。”；它与《AscSetL0cCopyPrequant》的“设置数据搬运随路量化流程中的标量量化参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0cCopyPrequant》补充：设置数据搬运随路量化流程中的标量量化参数。
- [AscSetL0cCopyParams](asc_set_l0c_copy_params.md)（`related`）：《AscSetL0cCopyParams》明确“设置L0C搬运随路格式转换（NZ转ND）的相关配置。”；它与《AscSetL0cCopyPrequant》的“设置数据搬运随路量化流程中的标量量化参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscGetL0c2gmPrequant](../cube_compute/asc_get_l0c2gm_prequant.md)（`same_topic`）：AscGetL0c2gmPrequant 与《AscSetL0cCopyPrequant》的实质衔接是：AscGetL0c2gmPrequant 读取随路量化前矢量地址，AscSetL0cCopyPrequant、总配置和 C++ prequant flag 是写入并启用同一状态的控制端。
- [AscSetL0c2gmQuantPost](../sys_var/asc_set_l0c2gm_quant_post.md)（`same_topic`）：焦点处理L0C2GM QUANT_POST 寄存器与 Fixpipe 量化搬出配置；AscSetL0cCopyPrequant正文说明“设置数据搬运随路量化流程中的标量量化参数”。候选设置 Fixpipe 的量化参数并由 L0C 搬出接口实际消费。
<!-- cannbot:related:end -->
