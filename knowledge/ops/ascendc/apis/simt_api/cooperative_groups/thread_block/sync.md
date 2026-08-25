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

<!-- cannbot:related:start -->
## 相关

- [ThreadBlockTile协作组sync](../thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《ThreadBlock协作组sync》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《ThreadBlock协作组sync》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [ThreadBlock](thread_block.md)（`same_topic`）：Sync 对整个 thread_block 建立屏障，参与范围由该 group 对象界定。
- [sync（协作组）](../sync.md)（`same_topic`）：对 thread_block 调用时同步范围收缩到当前线程块，避免不必要的跨块等待。
<!-- cannbot:related:end -->
