---
type: API
title: Memory矢量计算
description: Memory矢量计算API总览，涵盖Vector逻辑架构、SIMD计算说明及算术、逻辑、转换、归约、搬运等子模块。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/memory_vector_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Memory矢量计算

AscendC Memory 矢量计算 API 总览，基于 UB 侧 LocalTensor 执行 SIMD 计算。涵盖 Vector 逻辑架构与 SIMD 计算说明，按功能分为基础算术、逻辑计算、复合计算、比较与选择、类型转换、归约计算、数据排布转换、数据填充、离散与聚合、排序组合、数据重排、掩码操作、数据搬运等子模块。各子模块提供独立配置接口，使用前需关注 mask 设置与数据对齐。

<!-- cannbot:related:start -->
## 相关

- [MemoryVectorComputation](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/memory_vector_computation.md)（`explains`）：C++ Tensor 编程指南说明 LocalTensor 版本的资源和队列流程。
- [Memory矢量计算编程](../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/memory_vector_computation.md)（`explains`）：Memory矢量计算编程 与《Memory矢量计算》的实质衔接是：Memory 矢量编程采用 GM→UB→计算→GM，并区分连续、非连续和非对齐搬运；SIMD 架构、TPipe、Memory API、边界表和 C include 入口展开该数据流。
- [Memory矢量计算](../../c_api/vector_compute/memory_vector_compute.md)（`related`）：C Vector 总页提供相同 Memory 计算能力的 C 接口索引，可按语言层映射。
- [Memory矢量计算接口边界值汇总](../../../appendix/memory_vector_compute_interface_boundary_value_summary.md)（`related`）：边界值汇总用于核对各 Memory Vector 指令在 NaN/Inf 等输入下的输出。
<!-- cannbot:related:end -->
