---
type: API
title: TBuf简介
description: 使用Ascend C编程的过程中，可能会用到一些临时变量。这些临时变量占用的内存可以使用TBuf数据结构来管理，存储位置通过模板参数来设置，可以设置为不同的TPosition逻辑位置。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBuf/TBuf_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBuf简介

使用Ascend C编程的过程中，可能会用到一些临时变量。这些临时变量占用的内存可以使用TBuf数据结构来管理，存储位置通过模板参数来设置，可以设置为不同的TPosition逻辑位置。

TBuf继承自TQueBind父类，继承关系如下：

TBuf占用的存储空间通过TPipe进行管理，您可以通过InitBuffer接口为TBuf进行内存初始化操作，之后即可通过Get获取指定长度的Tensor参与计算。

使用InitBuffer为TBuf分配内存和为队列分配内存有以下差异：

-   为TBuf分配的内存空间只能参与计算，无法执行队列的入队出队操作。
-   调用一次内存初始化接口，TPipe只会为TBuf分配一块内存，为队列可以通过参数设置申请多块内存。如果要使用多个临时变量，需要定义多个TBuf数据结构，对每个TBuf数据结构分别调用InitBuffer接口进行内存初始化。
-   TBuf获取的Tensor无需释放。

<!-- cannbot:related:start -->
## 相关

- [TBuf 三参数 InitBuffer 触发 isTQue 静态断言](../../../../../runbooks/compilation/tbuf_initbuffer_uses_two_arguments.md)（`exemplifies`）：TBuf占用的存储空间通过TPipe进行管理，您可以通过InitBuffer接口为TBuf进行内存初始化操作；保留 `TQue` 的 `(queue, depth, bytes)` 三参数调用；仅对 `TBuf` 删除队列深度参数，改用 `(buffer, bytes)` 两参数调用。。API 介绍要求 TPipe::InitBuffer 初始化 TBuf，运行手册补齐 TBuf 与 TQue 不同的重载签名及静态断言排障。
<!-- cannbot:related:end -->
