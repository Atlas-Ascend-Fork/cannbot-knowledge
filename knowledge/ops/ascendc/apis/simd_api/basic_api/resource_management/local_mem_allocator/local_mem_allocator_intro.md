---
type: API
title: LocalMemAllocator简介
description: LocalMemAllocator是在使用静态Tensor编程时用于内存管理的类，用户无需构建TPipe/TQue，而是直接创建LocalTensor对象（也可以直接通过LocalTensor构造函数进行构造）并开发算子，从而减少运行时的开销，实现更优的性能。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/LocalMemAllocator_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# LocalMemAllocator简介

LocalMemAllocator是在使用静态Tensor编程时用于内存管理的类，用户无需构建TPipe/TQue，而是直接创建LocalTensor对象（也可以直接通过LocalTensor构造函数进行构造）并开发算子，从而减少运行时的开销，实现更优的性能。
