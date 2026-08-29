---
type: API
title: ShiftLeft
description: 对源操作数中的每个元素进行左移操作，左移位数由标量scalarValue决定，无符号类型执行逻辑左移，有符号类型执行算术左移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/ShiftLeft.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ShiftLeft

对源操作数中的每个元素进行左移操作，左移位数由标量scalarValue决定，无符号类型执行逻辑左移，有符号类型执行算术左移。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 TensorTrait, SetVectorMask, 通用地址对齐约束, 通用地址对齐约束, 掩码。

本接口属于 UB 矢量计算逻辑运算接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ShiftLeft](shift_left_shift_amount_tensor.md)（`same_topic`）：对源操作数中的每个元素进行左移操作，左移位数由标量scalarValue决定，无符号类型执行逻辑左移，有符号类型执行算术左移。；对源操作数中的每个元素进行左移操作，左移位数由Tensor指定，无符号类型执行逻辑左移，有符号类型执行算术左移。。两卡描述相同 ShiftLeft 元素语义的两个重载，核心差异是移位量由单个标量还是逐元素 Tensor 提供。
<!-- cannbot:related:end -->
