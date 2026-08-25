---
type: API
title: 掩码操作
description: Memory矢量计算掩码操作接口索引页，包含SetMaskCount、SetMaskNorm、SetVectorMask与ResetMask。
tags: [task.lookup, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/mask_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 掩码操作

Memory 矢量计算的掩码操作接口集合。SetMaskCount/SetMaskNorm 切换 mask 计数模式与正常模式；SetVectorMask 设置矢量计算的 mask 寄存器；ResetMask 重置 mask 为默认值。mask 用于控制矢量计算的有效元素范围，使用 count 模式后必须调用 ResetMask 恢复，否则影响后续计算。

<!-- cannbot:related:start -->
## 相关

- [AscSetMaskCount](../../../c_api/vector_compute/asc_set_mask_count.md)（`same_topic`）：掩码操作 与《AscSetMaskCount》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
- [AscSetMaskNorm](../../../c_api/vector_compute/asc_set_mask_norm.md)（`same_topic`）：掩码操作 与《AscSetMaskNorm》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
- [ResetMask](reset_mask.md)（`same_topic`）：掩码操作 与《ResetMask》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
- [SetMaskCount](set_mask_count.md)（`same_topic`）：掩码操作 与《SetMaskCount》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
- [SetMaskNorm](set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《掩码操作》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [SetVectorMask](set_vector_mask.md)（`same_topic`）：掩码操作 与《SetVectorMask》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
<!-- cannbot:related:end -->
