---
type: API
title: SIMT编程简介
description: SIMT编程简介，包含编程模型、扩展语法和API列表的导航入口。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/SIMT_programming_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SIMT编程简介

SIMT（Single Instruction Multiple Threads）编程范式以 Thread Block 为单位调度线程，每个 Thread 执行同一指令流但处理不同数据，适合需要线程级并行和细粒度数据交互的算子。
本入口提供三部分导航：编程模型说明 Thread、Thread Block、Grid 的层级关系与执行规则；扩展语法介绍 SIMT 所需的函数限定符与变量地址空间标注；API 列表汇总 SIMT 编程可用的计算、同步与内存接口。
使用 SIMT 编程前需确认目标硬件支持 SIMT 执行模式，并按编程模型正确划分线程层级。

<!-- cannbot:related:start -->
## 相关

- [AiCoreSimtProgrammingOverview](../../../guides/programming_guide/programming_model/ai_core_simt_programming/overview.md)（`explains`）：SIMT API 入口说明接口能力和使用边界，指南提供从场景选型到 Kernel 落地的完整推理链。
- [内存层级（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/memory_hierarchy.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；SIMT编程简介正文界定“SIMT编程简介，包含编程模型、扩展语法和API列表的导航入口”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [异构系统与编程模型](../../../guides/getting_started/quick_start/heterogeneous_system_and_programming_model.md)（`explains`）：异构系统与编程模型 与《SIMT编程简介》的实质衔接是：该快速入门从异构系统、host/device 编程模型扩展到 AI Core SIMT、SIMD/SIMT 混合和库 API；这些概述共同解释算子从 host tiling 到 device kernel 的边界。
- [编程模型概述](../../../guides/programming_guide/programming_model/programming_model_overview.md)（`explains`）：SIMT 接口入口补充概述未展开的 API 边界和平台支持。
- [核函数配置](extended_syntax/kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《SIMT编程简介》具体提供“SIMT编程简介，包含编程模型、扩展语法和API列表的导航入口。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
<!-- cannbot:related:end -->
