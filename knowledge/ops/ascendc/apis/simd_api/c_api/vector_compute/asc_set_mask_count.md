---
type: API
title: AscSetMaskCount
description: 设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_mask_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetMaskCount

设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
函数原型：void asc_set_mask_count()
约束：该API需和asc_set_vector_mask配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [基于全局掩码复用的计算性能优化](../../../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`explains`）：计数模式可把一次 mask 配置跨多指令复用。
- [AscSetMaskNorm](asc_set_mask_norm.md)（`same_topic`）：AscSetMaskCount说明设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入数据计算数量，实际迭代次数由Vector计算单元自动推断。在前n个数据计算类的接口内部会自动设置该模式，不需要自行设置。
- [AscSetVectorMask](asc_set_vector_mask.md)（`same_topic`）：Counter 模式启用后必须由 AscSetVectorMask 传入实际计算数量，硬件据此推断迭代和尾块。
- [SetMaskCount](../../basic_api/memory_vector_compute/mask_operations/set_mask_count.md)（`same_topic`）：C API AscSetMaskCount 与 C++ SetMaskCount 都切换计数模式并设置有效元素数。
- [掩码操作](../../basic_api/memory_vector_compute/mask_operations/mask_operations.md)（`same_topic`）：掩码操作 与《AscSetMaskCount》的实质衔接是：掩码计数模式和连续模式必须通过 SetMaskCount/SetMaskNorm 切换并在计数模式结束后 ResetMask；C 入口是同一状态机的对应调用。
<!-- cannbot:related:end -->
