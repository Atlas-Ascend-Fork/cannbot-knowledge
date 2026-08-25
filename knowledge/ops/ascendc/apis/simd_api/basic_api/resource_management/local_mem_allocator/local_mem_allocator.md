---
type: API
title: LocalMemAllocator
description: LocalMemAllocator接口索引页，包含简介、构造函数、GetCurAddr与Alloc。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/LocalMemAllocator/LocalMemAllocator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalMemAllocator

LocalMemAllocator 接口集合，提供 local memory 的动态分配能力。通过构造函数创建分配器实例，Alloc 按指定大小分配内存并返回地址，GetCurAddr 查询当前分配位置。适用于运行时才能确定内存需求的场景，相比 TBuf/TQue 的静态分配更灵活，但需自行管理分配与释放。
