---
type: API
title: SetMaskNorm
description: 设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetMaskNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetMaskNorm

设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, SetVectorMask, SetMaskCount。

本接口属于 UB 矢量计算掩码操作接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [基于全局掩码复用的计算性能优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`explains`）：SetMaskNorm 与《基于全局掩码复用的计算性能优化》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [如何使用掩码操作API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md)（`explains`）：SetMaskNorm 与《如何使用掩码操作API》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [AscGetMaskSpr](../../../c_api/reg/reg_data_types/asc_get_mask_spr.md)（`related`）：AscGetMaskSpr 读取当前 mask SPR，SetMaskNorm 是写入 normal mask 状态的直接来源，可用读取结果核验设置是否生效。
- [Or](../logical_compute/or.md)（`related`）：Or 与《SetMaskNorm》的衔接是：Or 在手动 mask 模式必须先用 SetMaskCount/SetMaskNorm 建立掩码并在结束后 ResetMask；Ors 和 Reg Or 是标量/Reg 形态的直接语义变体。
- [ReducePairElem](../reduction_compute/reduce_pair_elem.md)（`related`）：ReducePairElem 在 isSetMask=false 时要求调用者预先设置连续模式 mask，SetMaskNorm 正是建立该模式的前置步骤。
- [SubRelu](../composite_compute/sub_relu.md)（`related`）：SubRelu 与《SetMaskNorm》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [Ands](../logical_compute/ands.md)（`same_topic`）：Ands：Ands在 isSetMask=false时依赖SetMaskCount/Norm/VectorMask并要求ResetMask；And的tensor与Reg版本帮助区分标量按位与和双tensor按位与。 目标卡《SetMaskNorm》补充：设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。
- [AscSetMaskNorm](../../../c_api/vector_compute/asc_set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《AscSetMaskNorm》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [AscSetVectorMask](../../../c_api/vector_compute/asc_set_vector_mask.md)（`same_topic`）：SetMaskNorm 与《AscSetVectorMask》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [Copy](../data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《SetMaskNorm》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [Mask接口汇总（附录）](../../../../appendix/mask_interface_summary.md)（`same_topic`）：SetMaskNorm 与《Mask接口汇总（附录）》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [ResetMask](reset_mask.md)（`same_topic`）：SetMaskNorm 与《ResetMask》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [SIMD计算掩码](../simd_compute/mask.md)（`same_topic`）：SetMaskNorm 与《SIMD计算掩码》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [SetMaskCount](set_mask_count.md)（`same_topic`）：SetMaskNorm 与《SetMaskCount》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [SetVectorMask](set_vector_mask.md)（`same_topic`）：SetMaskNorm 与《SetVectorMask》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [掩码操作](mask_operations.md)（`same_topic`）：SetMaskNorm 与《掩码操作》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
<!-- cannbot:related:end -->
