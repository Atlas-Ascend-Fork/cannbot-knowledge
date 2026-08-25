---
type: API
title: SimdSimtHybridProgrammingIntro
description: SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/SIMD_SIMT_hybrid_programming_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SimdSimtHybridProgrammingIntro

SIMD 与 SIMT 混合编程允许在同一算子中结合两种编程范式：SIMD 侧重 Vector/Cube 上的数据并行计算，SIMT 侧重 Thread Block 内的线程级并行。混合编程用于充分发挥硬件不同计算单元的吞吐能力。
本入口提供三部分导航：编程模型说明混合编程的执行模型与调度方式；扩展语法介绍混合编程所需的函数限定符与变量地址空间标注；API 列表汇总可用的混合编程接口。
使用前需确认目标硬件支持 SIMD 与 SIMT 混合执行，并遵循扩展语法对函数与变量的标注约束。

<!-- cannbot:related:start -->
## 相关

- [异构系统与编程模型](../../../guides/getting_started/quick_start/heterogeneous_system_and_programming_model.md)（`explains`）：异构系统与编程模型 与《SimdSimtHybridProgrammingIntro》的实质衔接是：该快速入门从异构系统、host/device 编程模型扩展到 AI Core SIMT、SIMD/SIMT 混合和库 API；这些概述共同解释算子从 host tiling 到 device kernel 的边界。
- [核函数与VF函数（SIMD与SIMT混合编程）](../../../guides/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/kernel_and_vf_functions.md)（`explains`）：焦点处理混合 SIMD/SIMT 中 kernel、VF、callee 的限定符和启动边界；SimdSimtHybridProgrammingIntro正文说明“SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航”。候选明确 kernel/VF/callee 的允许调用方向、地址空间和 launch API，或给出同机制编译失败。
- [通过SIMT实现分支判断](../../../guides/operator_practice/simd_simt_hybrid_optimization/compute_optimization/simt_branch_judgment.md)（`explains`）：《SimdSimtHybridProgrammingIntro》明确“SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航。”；它与《通过SIMT实现分支判断》的“>该性能优化建议适用于如下型号：”在实际调用参数、数据流或结果校验上直接衔接。
- [ProgrammingModel](programming_model.md)（`same_topic`）：《SimdSimtHybridProgrammingIntro》明确“SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航。”；它与《ProgrammingModel》的“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
