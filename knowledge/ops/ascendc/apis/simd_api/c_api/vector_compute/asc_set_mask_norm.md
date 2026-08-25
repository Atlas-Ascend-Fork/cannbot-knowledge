---
type: API
title: AscSetMaskNorm
description: 设置Mask模式为Normal模式，该模式为系统默认模式。该模式下，Mask参数可控制高维切分计算过程中单次迭代内参与计算的元素。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_mask_norm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetMaskNorm

设置Mask模式为Normal模式，该模式为系统默认模式。该模式下，Mask参数可控制高维切分计算过程中单次迭代内参与计算的元素。
函数原型：void asc_set_mask_norm()
约束：该API需和asc_set_vector_mask配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSetMaskCount](asc_set_mask_count.md)（`same_topic`）：AscSetMaskCount说明设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
- [AscSetVectorMask](asc_set_vector_mask.md)（`same_topic`）：AscSetVectorMask说明为矢量计算接口设置参与计算的数据 Mask；调用前需通过 asc_set_mask_count 和 asc_set_mask_norm 选择 Mask 模式。
- [ResetMask](../../basic_api/memory_vector_compute/mask_operations/reset_mask.md)（`same_topic`）：ResetMask说明恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。
- [SetMaskCount](../../basic_api/memory_vector_compute/mask_operations/set_mask_count.md)（`same_topic`）：SetMaskCount说明设置Mask模式为Counter模式，直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。
- [SetMaskNorm](../../basic_api/memory_vector_compute/mask_operations/set_mask_norm.md)（`same_topic`）：SetMaskNorm 与《AscSetMaskNorm》的实质衔接是：SetMaskNorm 切到 Normal 模式后由 SetVectorMask 设置参与元素，结束时 ResetMask；C 对应入口、掩码指南和复用优化共享同一全局 mask 状态契约。
- [掩码操作](../../basic_api/memory_vector_compute/mask_operations/mask_operations.md)（`same_topic`）：掩码操作 与《AscSetMaskNorm》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
<!-- cannbot:related:end -->
