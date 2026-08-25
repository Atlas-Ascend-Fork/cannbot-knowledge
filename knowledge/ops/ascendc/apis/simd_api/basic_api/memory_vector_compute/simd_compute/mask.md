---
type: API
title: SIMD计算掩码
description: Mask（掩码）是Ascend C中用于控制数据元素是否参与计算的标识位序列。每一位掩码对应数据中的一个元素的位置，通过有效位和无效位标记，实现对数据操作的精细化开关控制。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mask

SIMD Mask 机制，控制矢量计算中参与运算的元素。支持 Count 模式（按元素计数）和 Norm 模式（按比特位掩码）。通过 SetVectorMask/SetMaskCount/SetMaskNorm 配置。

<!-- cannbot:related:start -->
## 相关

- [ResetMask](../mask_operations/reset_mask.md)（`related`）：《ResetMask》明确“恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。”；它与《SIMD计算掩码》的“Mask（掩码）是Ascend C中用于控制数据元素是否参与计算的标识位序列。每一位掩码对应数据中的一个元素的位置，通过有效位和无效位标记，实现对数据操作的精细化开关控制。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetVectorMask](../mask_operations/set_vector_mask.md)（`related`）：《SetVectorMask》明确“矢量计算时设置mask，支持Normal模式控制单次迭代参与计算元素和Counter模式控制总计算元素个数。”；它与《SIMD计算掩码》的“Mask（掩码）是Ascend C中用于控制数据元素是否参与计算的标识位序列。每一位掩码对应数据中的一个元素的位置，通过有效位和无效位标记，实现对数据操作的精细化开关控制。”在实际调用参数、数据流或结果校验上直接衔接。
- [SubRelu](../composite_compute/sub_relu.md)（`related`）：SubRelu 与《SIMD计算掩码》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [Copy](../data_move/copy_ub_to_ub_mask_highdim_split.md)（`same_topic`）：Copy 与《SIMD计算掩码》的实质衔接是：该 Copy 是 UB 高维/掩码搬运；SetMaskNorm/Count/VectorMask、ResetMask、UB 搬运指南和 AscCopy 共同决定 mask 模式、stride 与恢复步骤。
- [SetMaskNorm](../mask_operations/set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《SIMD计算掩码》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
<!-- cannbot:related:end -->
