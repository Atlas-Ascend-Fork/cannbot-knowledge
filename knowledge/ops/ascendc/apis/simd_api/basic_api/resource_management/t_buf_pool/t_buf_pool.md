---
type: API
title: TBufPool
description: TBufPool接口索引页，包含简介、构造函数、InitBufPool、InitBuffer与Reset。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/TBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBufPool

TBufPool 接口集合，用于管理 AscendC 片上 Buffer 池，支持多 TBuf 共享池内存。通过构造函数创建实例，InitBufPool/InitBuffer 初始化池与 buffer，Reset 重置池状态。相比单个 TBuf，TBufPool 在多 buffer 场景下可更高效利用内存，适用于需要多个临时 buffer 的算子。
