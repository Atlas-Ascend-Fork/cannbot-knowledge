---
type: API
title: ProgrammingModel
description: SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/programming_model.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 编程模型

SIMD 与 SIMT 混合编程支持根据算子特征精细化映射：规则逐元素计算用 SIMD 获得高吞吐，不规则或分支计算用 SIMT 缓解发散。同一算子可同时利用两者优势。

线程架构采用分层结构：Grid > Thread Block（最大 2048 线程）> Warp（32 线程）> Thread。Grid 中线程块总数不超过 65535，gridDim 为一维（y、z 必须为 1）。通过 asc_vf_call 调用 SIMT VF 时需显式指定 Thread Block 维度。线程索引：一维 idx = blockIdx.x * blockDim.x + threadIdx.x。

Warp 是基本调度和执行单位，含 32 线程执行相同指令。分支发散（Warp Divergence）时硬件串行执行各分支降低效率，线程数建议设为 32 的整数倍。

UB（Unified Buffer）为线程块内共享内存，总大小 256KB，从低到高依次为静态内存、动态内存、预留空间（8KB）、Data Cache（最小 32KB，最大 128KB）。DataCache = 256KB - 静态 - 动态 - 8KB，小于 32KB 会报错。动态内存可通过 extern 数组或 LocalMemAllocator::Alloc 申请，两者不可同时使用。

<!-- cannbot:related:start -->
## 相关

- [异构系统与编程模型](../../../guides/getting_started/quick_start/heterogeneous_system_and_programming_model.md)（`explains`）：异构系统与编程模型 与《ProgrammingModel》的实质衔接是：该快速入门从异构系统、host/device 编程模型扩展到 AI Core SIMT、SIMD/SIMT 混合和库 API；这些概述共同解释算子从 host tiling 到 device kernel 的边界。
- [编程模型概述](../../../guides/programming_guide/programming_model/programming_model_overview.md)（`explains`）：混合 API 模型说明 SIMD 批处理与 SIMT 控制流如何在同一 Kernel/VF 体系协作。
- [函数执行空间限定符](extended_syntax/function_execution_space_qualifier.md)（`related`）：《函数执行空间限定符》明确“SIMD与SIMT混合编程涉及多种类型的函数，它们之间遵循严格的调用关系和层级约束。本章节将会介绍整体函数类型和调用关系，并详细展开SIMT相关函数（__simt_vf__和__simt_callee__）的定义、调用语法及约束，其余限定符请参见对应章节。”；它与《ProgrammingModel》的“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”在实际调用参数、数据流或结果校验上直接衔接。
- [核函数配置](extended_syntax/kernel_function_config.md)（`related`）：《核函数配置》明确“核函数是SIMD与SIMT混合编程的Device侧入口函数，负责协调整个算子的执行流程，包括VF的调度和调用。vector计算单元的混合编程场景下，函数定义语法为：”；它与《ProgrammingModel》的“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”在实际调用参数、数据流或结果校验上直接衔接。
- [编程模型](../simt_programming_intro/programming_model.md)（`related`）：《ProgrammingModel》明确“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”；它与《编程模型》的“SIMT编程模型采用Grid、Thread Block、Warp、Thread分层线程结构，适合控制流复杂和访存模式不规则的算子场景。”在实际调用参数、数据流或结果校验上直接衔接。
- [SimdSimtHybridProgrammingIntro](simd_simt_hybrid_programming_intro.md)（`same_topic`）：《SimdSimtHybridProgrammingIntro》明确“SIMD与SIMT混合编程简介，包含编程模型、扩展语法和API列表导航。”；它与《ProgrammingModel》的“SIMD与SIMT混合编程支持根据算子特征精细化映射，规则计算用SIMD获得高吞吐，不规则计算用SIMT缓解发散。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
