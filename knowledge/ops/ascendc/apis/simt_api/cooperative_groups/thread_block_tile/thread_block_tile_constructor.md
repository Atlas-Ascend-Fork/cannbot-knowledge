---
type: API
title: thread_block_tile构造函数
description: thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/thread_block_tile_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# thread_block_tile构造函数

thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。
函数原型：thread_block_tile<Size, ParentT> tiled_partition(const ParentT& g)
返回值：返回划分后当前线程所属的thread_block_tile组。
约束：Size必须是2的幂，当前可选值为1、2、4、8、16、32、64、128、256、512、1024、2048；Size大于32时必须使用block_tile_memory创建父thread_block，该对象必须位于Global Memory或Unified Buffer，不能在栈上创建，且Unified Buffer对象性能更优；模板版本要求父组线程数可被Size整除，且Size小于父组大小。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [tiled_partition](../tiled_partition.md)（`related`）：tiled_partition API用于将一个线程组划分为多个更小、固定大小的子组，以便线程在以更精细的粒度上进行协作。；thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。前者定义划分操作，后者把该操作确定为 thread_block_tile 的构造入口。
<!-- cannbot:related:end -->
