---
type: API
title: SubRelu
description: 按元素求差，再进行Relu计算（结果和0对比取较大值）。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/SubRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SubRelu

按元素求差，再进行Relu计算（结果和0对比取较大值）。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, 掩码操作, 高维切分, BinaryRepeatParams。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ResetMask](../mask_operations/reset_mask.md)（`related`）：SubRelu 与《ResetMask》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [SIMD计算掩码](../simd_compute/mask.md)（`related`）：SubRelu 与《SIMD计算掩码》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [SetMaskNorm](../mask_operations/set_mask_norm.md)（`related`）：SubRelu 与《SetMaskNorm》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [SetVectorMask](../mask_operations/set_vector_mask.md)（`related`）：SubRelu 与《SetVectorMask》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [SubReluCast](sub_relu_cast.md)（`related`）：SubRelu 保留相同减法和激活但不做类型转换，可在源目 dtype 相同或需拆分 Cast 时选用。
- [AscSubRelu](../../../c_api/vector_compute/asc_sub_relu.md)（`same_topic`）：SubRelu 与《AscSubRelu》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
<!-- cannbot:related:end -->
