---
type: API
title: ResetMask
description: 恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/ResetMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ResetMask

恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask。

本接口属于 UB 矢量计算掩码操作接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [如何使用掩码操作API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md)（`explains`）：如何使用掩码操作API 与《ResetMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [AscGetMaskSpr](../../../c_api/reg/reg_data_types/asc_get_mask_spr.md)（`related`）：调试完 mask SPR 后需用 ResetMask 恢复默认状态，避免读取/实验后留下的 mask 配置影响后续指令。
- [Or](../logical_compute/or.md)（`related`）：Or 与《ResetMask》的衔接是：Or 在手动 mask 模式必须先用 SetMaskCount/SetMaskNorm 建立掩码并在结束后 ResetMask；Ors 和 Reg Or 是标量/Reg 形态的直接语义变体。
- [ReducePairElem](../reduction_compute/reduce_pair_elem.md)（`related`）：手动设置 mask 后必须 ResetMask，避免 SPR 状态污染后续 Vector 指令；这是 focal 明确要求的调用后清理动作。
- [SIMD计算掩码](../simd_compute/mask.md)（`related`）：《ResetMask》明确“恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。”；它与《SIMD计算掩码》的“Mask（掩码）是Ascend C中用于控制数据元素是否参与计算的标识位序列。每一位掩码对应数据中的一个元素的位置，通过有效位和无效位标记，实现对数据操作的精细化开关控制。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetMaskCount](set_mask_count.md)（`related`）：SetMaskCount 切到 Counter 模式后要求计算结束用 ResetMask 恢复默认 mask；两卡构成手工 mask 模式的进入/退出生命周期。
- [SetVectorMask](set_vector_mask.md)（`related`）：手工 SetVectorMask 完成后需用 ResetMask 恢复默认状态，避免后续矢量指令继承当前 mask。
- [SubRelu](../composite_compute/sub_relu.md)（`related`）：SubRelu 与《ResetMask》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [Ands](../logical_compute/ands.md)（`same_topic`）：Ands：Ands在 isSetMask=false时依赖SetMaskCount/Norm/VectorMask并要求ResetMask；And的tensor与Reg版本帮助区分标量按位与和双tensor按位与。 目标卡《ResetMask》补充：恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。
- [AscSetMaskNorm](../../../c_api/vector_compute/asc_set_mask_norm.md)（`same_topic`）：ResetMask说明恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。
- [Copy](../data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《ResetMask》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SetMaskNorm](set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《ResetMask》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [掩码操作](mask_operations.md)（`same_topic`）：掩码操作 与《ResetMask》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
<!-- cannbot:related:end -->
