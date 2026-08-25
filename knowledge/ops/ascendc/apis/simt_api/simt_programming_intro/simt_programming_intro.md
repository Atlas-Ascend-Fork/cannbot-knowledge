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
