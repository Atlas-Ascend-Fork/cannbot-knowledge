---
type: API
title: 扩展语法
description: 扩展语法索引，包含函数执行空间限定符、内存空间限定符、内置类型、变量、宏与核函数配置。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/SIMT_programming_intro/extended_syntax/extended_syntax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 扩展语法

SIMT 编程模式下的扩展语法索引，包含函数执行空间限定符（如 __aicore__）、内存空间限定符、内置数据类型、内置变量、内置宏和核函数配置六部分。这些扩展语法为 Ascend C SIMT 编程模型提供编译器级支持，是编写纯 SIMT 算子的基础。

<!-- cannbot:related:start -->
## 相关

- [核函数配置](kernel_function_config.md)（`related`）：《核函数配置》的任务是“核函数是SIMT编程的Device侧入口函数，负责协调整个算子的执行流程。函数定义语法为：”。《扩展语法》具体提供“扩展语法索引，包含函数执行空间限定符、内存空间限定符、内置类型、变量、宏与核函数配置。”，它直接用于SIMT Kernel 入口的执行/内存限定符、内置变量和 launch 头文件。
<!-- cannbot:related:end -->
