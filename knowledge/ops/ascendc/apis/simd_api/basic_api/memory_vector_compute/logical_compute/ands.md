---
type: API
title: Ands
description: 矢量内每个元素和标量间做按位与操作，支持标量在前和标量在后两种场景，标量输入支持配置LocalTensor单点元素。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/Ands.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Ands

矢量内每个元素和标量间做按位与操作，支持标量在前和标量在后两种场景，标量输入支持配置LocalTensor单点元素。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, 掩码, 高维切分API, UnaryRepeatParams。

本接口属于 UB 矢量计算逻辑运算接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [And](and.md)（`same_topic`）：矢量内每个元素和标量间做按位与操作，支持标量在前和标量在后两种场景，标量输入支持配置LocalTensor单点元素。；对LocalTensor中的元素做按位与运算，支持整个tensor、前n个数据连续计算和高维切分计算三种调用方式。。两卡的核心操作都是 LocalTensor 元素的按位与；一端覆盖 tensor 与标量的操作数形态，另一端覆盖 tensor 间及连续或高维切分的调用形态，属于同一 And API 主题的重载边界。
<!-- cannbot:related:end -->
