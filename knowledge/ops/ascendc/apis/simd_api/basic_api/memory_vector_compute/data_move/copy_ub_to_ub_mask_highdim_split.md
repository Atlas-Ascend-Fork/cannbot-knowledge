---
type: API
title: Copy
description: 支持UB之间的数据搬运，支持mask操作和DataBlock间隔操作。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/Copy_UBToUB_mask_highdim_split.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Copy

支持UB之间的数据搬运，支持mask操作和DataBlock间隔操作。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 逻辑位置TPosition, SetVectorMask, 掩码, 高维切分, Reg矢量计算。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [如何使用掩码操作API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md)（`explains`）：Copy 与《如何使用掩码操作API》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [高维切分API](../../../../../guides/programming_guide/library_api/basic_api/interface_classification/high_dim_split_api.md)（`explains`）：Copy 与《高维切分API》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [DataCopy](data_copy_ub_to_ub_highdim_split.md)（`related`）：Copy 的 mask 高维切分适合按元素有效位搬运，DataCopy 版本则以块和 stride 描述搬运。
- [AscCopy](../../../c_api/reg/reg_load/asc_copy.md)（`same_topic`）：Copy 与《AscCopy》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [AscCopy](../../../c_api/vector_compute/asc_copy.md)（`same_topic`）：AscCopy 与《Copy》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [Copy](copy_ub_to_ub_continuous.md)（`same_topic`）：Copy 与《Copy》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [ResetMask](../mask_operations/reset_mask.md)（`same_topic`）：Copy 与《ResetMask》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SIMD计算掩码](../simd_compute/mask.md)（`same_topic`）：Copy 与《SIMD计算掩码》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SetMaskCount](../mask_operations/set_mask_count.md)（`same_topic`）：Copy 与《SetMaskCount》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SetMaskNorm](../mask_operations/set_mask_norm.md)（`same_topic`）：Copy 与《SetMaskNorm》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SetVectorMask](../mask_operations/set_vector_mask.md)（`same_topic`）：Copy 与《SetVectorMask》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [UB与UB数据搬运](../../data_move_guide/ub_ub_data_move.md)（`same_topic`）：Copy 与《UB与UB数据搬运》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [高维切分（SIMD计算）](../simd_compute/high_dim_split.md)（`same_topic`）：Copy 与《高维切分（SIMD计算）》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
<!-- cannbot:related:end -->
