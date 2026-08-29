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

- [基于全局掩码复用的计算性能优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`explains`）：“在这些场景中，掩码配置保持不变的情况下，遵循“**一次性全局配置，后续复用**”的核心原则：在所有连续计算操作执行之前，通过调用**SetVectorMask**接口完成**全局掩码**的一次性、完整设置mask；随后，所有后续的向量计算接口调用均应将**isSetMask**参数设置为**false**，以明确指示接口跳过内部掩码设置流程，直接**复用已预置**的全局掩码状态。”与“设置 Vector Mask，控制矢量计算接口中参与计算的元素。支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。”提供双方正文证据。优化指南把 SetVectorMask 用作一次性全局配置并要求后续关闭 isSetMask，API 卡定义其 Count/Norm 掩码合同，指南解释了该 API 的复用用法。
- [ResetMask](reset_mask.md)（`related`）：焦点卡通过“设置 Vector Mask，控制矢量计算接口中参与计算的元素。”改变后续矢量指令状态，候选卡明确“使用完成后需要使用ResetMask将mask恢复为默认值。”；两卡闭合设置后的恢复生命周期，避免 mask 泄漏到后续计算。
- [SetMaskCount](set_mask_count.md)（`related`）：焦点卡说明 SetVectorMask “支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。”，候选卡用“设置Mask模式为Counter模式，直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。”定义调用前的 Count 模式选择；两者组成状态设置与 mask 数值写入顺序。
- [SetMaskNorm](set_mask_norm.md)（`related`）：焦点卡说明 SetVectorMask “支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。”，候选卡规定“设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。”；候选为同一接口选择 Norm 语义并决定 mask 如何解释。
<!-- cannbot:related:end -->
