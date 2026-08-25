---
type: API
title: SetVectorMask
description: 矢量计算时设置mask，支持Normal模式控制单次迭代参与计算元素和Counter模式控制总计算元素个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetVectorMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetVectorMask

设置 Vector Mask，控制矢量计算接口中参与计算的元素。支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Vector算子灵活运用Counter模式](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/vector_counter_mode.md)（`explains`）：指南用 15000 个 half 元素对比 Normal 主尾块与 Counter 单次总 count，说明 SetVectorMask 在 Counter 模式下为何减少 Scalar 计算和指令数。
- [如何使用掩码操作API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_mask_api.md)（`explains`）：如何使用掩码操作API 与《SetVectorMask》的实质衔接是：掩码指南直接覆盖 Move/Create/UpdateMask、Normal/Counter 设置和 Reset；两张故障卡约束模板类型与可修改参数。
- [AscSetVectorMask](../../../c_api/vector_compute/asc_set_vector_mask.md)（`related`）：C++ Memory API 的 SetVectorMask 提供同类全局 mask 配置，可在 C/C++ 路线间对照。
- [MoveMask](../../reg_vector_compute/mask_reg_compute/move_mask.md)（`related`）：MoveMask reads the legacy MASK0/MASK1 state established by SetVectorMask, so this setter is its required producer.
- [ResetMask](reset_mask.md)（`related`）：手工 SetVectorMask 完成后需用 ResetMask 恢复默认状态，避免后续矢量指令继承当前 mask。
- [SIMD计算掩码](../simd_compute/mask.md)（`related`）：《SetVectorMask》明确“矢量计算时设置mask，支持Normal模式控制单次迭代参与计算元素和Counter模式控制总计算元素个数。”；它与《SIMD计算掩码》的“Mask（掩码）是Ascend C中用于控制数据元素是否参与计算的标识位序列。每一位掩码对应数据中的一个元素的位置，通过有效位和无效位标记，实现对数据操作的精细化开关控制。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetMaskCount](set_mask_count.md)（`related`）：SetMaskCount 先切换 Counter 模式，SetVectorMask 再以总元素数配置 mask；两者共同免除主块/尾块的手工 repeat 计算。
- [SubRelu](../composite_compute/sub_relu.md)（`related`）：SubRelu 与《SetVectorMask》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [Ands](../logical_compute/ands.md)（`same_topic`）：Ands：Ands在 isSetMask=false时依赖SetMaskCount/Norm/VectorMask并要求ResetMask；And的tensor与Reg版本帮助区分标量按位与和双tensor按位与。 目标卡《SetVectorMask》补充：矢量计算时设置mask，支持Normal模式控制单次迭代参与计算元素和Counter模式控制总计算元素个数。
- [Copy](../data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《SetVectorMask》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SetMaskNorm](set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《SetVectorMask》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [掩码操作](mask_operations.md)（`same_topic`）：掩码操作 与《SetVectorMask》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
<!-- cannbot:related:end -->
