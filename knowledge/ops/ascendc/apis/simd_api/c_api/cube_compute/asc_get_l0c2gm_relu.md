---
type: API
title: AscGetL0c2gmRelu
description: 数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_get_l0c2gm_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscGetL0c2gmRelu

数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [随路Relu](../../basic_api/cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscGetL0c2gmRelu》具体提供“数据搬运过程中进行随路量化时，通过调用该接口获取ReLU操作前矢量的起始地址。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscGetL0c2gmPrequant](asc_get_l0c2gm_prequant.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscGetL0c2gmPrequant》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [AscGetL0c2gmUnitflag](asc_get_l0c2gm_unitflag.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscGetL0c2gmUnitflag》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [AscSetL0c2gmConfig](asc_set_l0c2gm_config.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscSetL0c2gmConfig》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [AscSetL0c2gmLreluAlpha](../cube_data_move/asc_set_l0c2gm_lrelu_alpha.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscSetL0c2gmLreluAlpha》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [AscSetL0c2gmReluAlpha](../sys_var/asc_set_l0c2gm_relu_alpha.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscSetL0c2gmReluAlpha》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [随路ReLU](../../basic_api/cube_compute/cube_store_key_features/accompanying_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《随路ReLU》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
- [随路量化与随路ReLU场景组合](../../basic_api/cube_compute/cube_store_key_features/accompanying_quantization_and_relu_scenario_combination.md)（`same_topic`）：AscGetL0c2gmRelu 与《随路量化与随路ReLU场景组合》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
<!-- cannbot:related:end -->
