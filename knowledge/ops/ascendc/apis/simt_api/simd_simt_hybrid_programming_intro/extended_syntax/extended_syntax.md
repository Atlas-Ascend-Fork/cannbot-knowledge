---
type: API
title: 扩展语法
description: 扩展语法索引，包含函数执行空间限定符、内存空间限定符、内置类型、变量、宏与核函数配置。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMD_SIMT_hybrid_programming_intro/extended_syntax/extended_syntax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 扩展语法

SIMD 与 SIMT 混合编程模式下的扩展语法索引，包含函数执行空间限定符（如 __aicore__）、内存空间限定符、内置数据类型、内置变量、内置宏和核函数配置六部分。这些扩展语法为 Ascend C 混合编程模型提供编译器级支持，是编写 SIMD/SIMT 混合算子的基础。

<!-- cannbot:related:start -->
## 相关

- [扩展语法内置变量](builtin_variables.md)（`related`）：扩展语法内置变量 与《扩展语法》的实质衔接是：dim3 内置变量依赖扩展语法、核函数配置和公共头暴露；SIMT/mixed-SIMT 指南及 dim3 编译故障给出实际声明与使用链。
<!-- cannbot:related:end -->
