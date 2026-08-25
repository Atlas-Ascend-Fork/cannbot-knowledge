---
type: API
title: ThreadBlockTile协作组any
description: 判断thread_block_tile组内是否有线程的输入不为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/any.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile协作组any

判断thread_block_tile组内是否有线程的输入不为0。
函数原型：int any(int predicate) const
返回值：thread_block_tile组内所有线程的输入均为0，返回0，否则返回1。
约束：当thread_block_tile的模板参数Size大于32时，即Size为64、128、256、512、1024、2048的跨Warp协作组场景，必须保证thread_block_tile组内所有线程均处于活跃状态，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
