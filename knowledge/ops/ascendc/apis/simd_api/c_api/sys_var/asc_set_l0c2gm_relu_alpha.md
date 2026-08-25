---
type: API
title: AscSetL0c2gmReluAlpha
description: 设置RELU_ALPHA寄存器值，存储Scalar ReLU使用的alpha值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_l0c2gm_relu_alpha.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetL0c2gmReluAlpha

对RELU_ALPHA寄存器中的值进行设置。这是一个64bit的寄存器，存储在fixpipe或cube指令中进行Scalar ReLU时使用的alpha值。 其中各bit含义如下： 表1 RELU_ALPHA寄存器比特位说明
函数原型：void asc_set_l0c2gm_relu_alpha(uint64_t config)
参数：config（输入）：待设置的寄存器值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSetL0c2gmLreluAlpha](../cube_data_move/asc_set_l0c2gm_lrelu_alpha.md)（`related`）：LReLU alpha 配置是相邻但不同的激活斜率契约，可用于区分 Scalar ReLU 与 LeakyReLU 的寄存器设置。
- [随路ReLU](../../basic_api/cube_compute/cube_store_key_features/accompanying_relu.md)（`related`）：随路 ReLU 特性说明解释 RELU_ALPHA 在 L0C 搬出时如何参与 Scalar ReLU。
- [随路Relu](../../basic_api/cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscSetL0c2gmReluAlpha》具体提供“设置RELU_ALPHA寄存器值，存储Scalar ReLU使用的alpha值。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscGetL0c2gmRelu](../cube_compute/asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscSetL0c2gmReluAlpha》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
<!-- cannbot:related:end -->
