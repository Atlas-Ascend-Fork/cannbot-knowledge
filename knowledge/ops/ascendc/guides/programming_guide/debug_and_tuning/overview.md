---
type: Guide
title: 调试与调优概述
description: 介绍Ascend C算子调试与调优整体方案，涵盖CPU域孪生调试、NPU域上板调试及性能调优工具。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/debug_and_tuning/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

Ascend C算子调试的整体方案如下：开发者通过调用Ascend C类库编写Ascend C算子Kernel侧源码，Kernel侧源码通过毕昇编译器进行编译，编译生成通用的CPU域的二进制或者NPU域的二进制文件。其中，CPU域的二进制可以通过gdb通用调试工具等调试手段进行调试；NPU域的二进制文件可使用printf/assert等接口进行数据打印，也可通过仿真打点图或者Profiling工具进行上板数据采集等方式进行调试。
具体的调试调优方法和使用的工具列表如下：
调试调优方法和使用的工具列表
