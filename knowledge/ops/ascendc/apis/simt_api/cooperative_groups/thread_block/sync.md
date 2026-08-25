---
type: API
title: ThreadBlock协作组sync
description: 同步线程块内所有线程，所有线程都执行到该同步点位置才能继续执行。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlock协作组sync

同步线程块内所有线程，所有线程都执行到该同步点位置才能继续执行。
函数原型：static void sync()
约束：必须保证线程块内所有线程都能执行到同一个sync()调用，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
