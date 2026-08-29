---
type: Guide
title: 特性
description: C++标准支持特性说明，列举不支持的C++特性。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/cpp_standard_support/syntax_restrictions/features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 特性

Ascend C 核函数编程不支持的 C++ 特性列表：不支持虚函数与虚继承、不支持运行时递归、不支持动态内存分配（malloc/new/free）、不支持 STL、不支持运行时 typeid、不支持文件系统 IO、不支持标准库 tuple 及算法类运算（相关库函数调用需标记 aicore）。这些限制源于 AICore 的执行模型约束，核函数需在编译时确定所有控制流与内存分配。
