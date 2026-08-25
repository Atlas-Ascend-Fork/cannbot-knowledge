---
type: API
title: AscSetL0c2gmLreluAlpha
description: 设置L0C搬运接口计算过程中使用的Leaky ReLU alpha值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_set_l0c2gm_lrelu_alpha.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscSetL0c2gmLreluAlpha

用于设置asc_copy_l0c2l1或asc_copy_l0c2gm接口计算过程中使用的Leaky ReLU alpha值。该值只支持half和float两种数据类型。

参数：config(输入): Leaky ReLU alpha值。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm.md)（`related`）：AscSetL0c2gmLreluAlpha 设置的 alpha 由后续 AscCopyL0c2Gm 随路 LeakyReLU 消费，是该搬出前的直接配置。
- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL0c2Gm：这些卡共同约束同一 L0C→GM fixpipe 搬运：架构变体核对原型，SetL0cCopyParams/Prequant/ChannelPara配置随路转换，NZ2ND与Fixpipe页解释输出布局。 目标卡《AscSetL0c2gmLreluAlpha》补充：设置L0C搬运接口计算过程中使用的Leaky ReLU alpha值。
- [AscCopyL0c2L1](asc_copy_l0c2l1/asc_copy_l0c2l1.md)（`related`）：同一 alpha 配置也作用于文档列出的 AscCopyL0c2L1 随路 LeakyReLU 路径，调用顺序必须先设 alpha 再搬运。
- [AscSetL0c2gmReluAlpha](../sys_var/asc_set_l0c2gm_relu_alpha.md)（`related`）：LReLU alpha 配置是相邻但不同的激活斜率契约，可用于区分 Scalar ReLU 与 LeakyReLU 的寄存器设置。
- [随路Relu](../../basic_api/cube_compute_tensor_api/cube_store_key_features/relu_pre.md)（`related`）：《随路Relu》的任务是“enableRelu默认值为false，表示不使能随路Relu。设置为true时，搬出过程中对输出数据执行Normal Relu激活。”。《AscSetL0c2gmLreluAlpha》具体提供“设置L0C搬运接口计算过程中使用的Leaky ReLU alpha值。”，它直接用于L0C 搬出阶段 enableRelu、Fixpipe 配置和 C API 寄存器状态。
- [AscGetL0c2gmRelu](../cube_compute/asc_get_l0c2gm_relu.md)（`same_topic`）：AscGetL0c2gmRelu 与《AscSetL0c2gmLreluAlpha》的实质衔接是：AscGetL0c2gmRelu 读取 L0C 搬出随路 ReLU 前的向量起点；prequant/unitflag、alpha/config 设置和随路 ReLU 指南共同确定 Fixpipe 后处理状态。
<!-- cannbot:related:end -->
