---
type: API
title: TBuf
description: TBuf接口索引页，包含简介、构造函数、Get与GetWithOffset。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/TBuf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBuf

TBuf 接口集合，用于管理 AscendC 片上 Buffer。通过构造函数创建实例，配合 TPipe::InitBuffer 分配内存；Get 获取指定类型的 LocalTensor；GetWithOffset 获取带偏移的 LocalTensor，支持从一个 TBuf 中切分多段使用。TBuf 不含 Queue 语义，适用于无需队列管理的纯 buffer 场景。
