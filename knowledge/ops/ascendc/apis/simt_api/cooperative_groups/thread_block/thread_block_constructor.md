---
type: API
title: thread_block构造函数
description: thread_block不提供默认的构造函数，用户使用this_thread_block函数获取当前线程所属的thread_block对象。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_block_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# thread_block构造函数

thread_block不提供默认的构造函数，用户使用this_thread_block函数获取当前线程所属的thread_block对象。
函数原型：thread_block this_thread_block()
返回值：返回当前线程所属的thread_block对象。
约束：线程块实际启动线程数不能超过MaxBlockSize。；scratch对应的block_tile_memory对象必须位于Global Memory或Unified Buffer，不能是在栈空间中创建的对象。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
