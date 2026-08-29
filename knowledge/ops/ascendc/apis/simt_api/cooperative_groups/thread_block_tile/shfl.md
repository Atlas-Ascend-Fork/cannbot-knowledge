---
type: API
title: ThreadBlockTile协作组shfl
description: thread_block_tile组内线程的数据交换接口，用于获取组内指定rank线程输入的var值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/shfl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile协作组shfl

thread_block_tile组内线程的数据交换接口，用于获取组内指定rank线程输入的var值。
函数原型：T shfl(T var, int src_rank) const
返回值：thread_block_tile组内指定线程输入的var值。
约束：在跨Warp的thread_block_tile场景（Size>32）下；必须保证thread_block_tile组内线程指定相同的src_rank，否则是未定义行为。；必须保证thread_block_tile组内线程均处于活跃状态，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
