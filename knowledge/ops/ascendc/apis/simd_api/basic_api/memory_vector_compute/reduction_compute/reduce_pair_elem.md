---
type: API
title: ReducePairElem
description: 对相邻两个元素进行归约求和操作，结果按顺序写入目标地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/ReducePairElem.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReducePairElem

对相邻两个元素进行归约求和操作，结果按顺序写入目标地址。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, LocalTensor, 掩码概述, 高维切分。

本接口属于 UB 矢量计算归约接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ResetMask](../mask_operations/reset_mask.md)（`related`）：手动设置 mask 后必须 ResetMask，避免 SPR 状态污染后续 Vector 指令；这是 focal 明确要求的调用后清理动作。
- [SetMaskCount](../mask_operations/set_mask_count.md)（`related`）：计数模式 ReducePairElem 需要先由 SetMaskCount 配置 mask 计数语义，否则 repeat 解释会与预期不一致。
- [SetMaskNorm](../mask_operations/set_mask_norm.md)（`related`）：ReducePairElem 在 isSetMask=false 时要求调用者预先设置连续模式 mask，SetMaskNorm 正是建立该模式的前置步骤。
- [PairReduceElem](../../reg_vector_compute/reduction_compute/pair_reduce_elem.md)（`same_topic`）：《PairReduceElem》处理“将源寄存器中相邻两个数值相加，结果保存在目的寄存器的低位位置。”。《ReducePairElem》明确提供“对相邻两个元素进行归约求和操作，结果按顺序写入目标地址。”，其参数、调用或验证步骤直接接入PairReduceElem 的寄存器规约语义、C 层等价入口和跨 chunk 正确性。
<!-- cannbot:related:end -->
