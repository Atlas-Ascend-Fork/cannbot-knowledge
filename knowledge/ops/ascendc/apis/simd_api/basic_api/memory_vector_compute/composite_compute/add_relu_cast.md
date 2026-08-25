---
type: API
title: AddReluCast
description: 按元素求和，结果和0对比取较大值，并根据源操作数和目的操作数Tensor的数据类型进行精度转换。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/AddReluCast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# AddReluCast

按元素求和，结果和0对比取较大值，并根据源操作数和目的操作数Tensor的数据类型进行精度转换。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, 掩码操作, 高维切分, BinaryRepeatParams。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AddDeqRelu](add_deq_relu.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《AddReluCast》明确“按元素求和，结果和0对比取较大值，并根据源操作数和目的操作数Tensor的数据类型进行精度转换。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [AddRelu](add_relu.md)（`related`）：AddReluCast 在 Add+Relu 后增加类型转换；当输入输出 dtype 相同无需 Cast 时，AddRelu 是更直接的同链路接口。
- [AscAddRelu](../../../c_api/vector_compute/asc_add_relu.md)（`related`）：当输出 dtype 与输入不同，AddReluCast 显式承载转换；它解释 AscAddRelu 签名中 s16→s8、f32→f16 等随路转换边界。
- [SubReluCast](sub_relu_cast.md)（`related`）：AddReluCast 与本接口共享 ReLU+Cast 尾链，仅首个二元运算由 Sub 改为 Add，便于按算式选择。
<!-- cannbot:related:end -->
