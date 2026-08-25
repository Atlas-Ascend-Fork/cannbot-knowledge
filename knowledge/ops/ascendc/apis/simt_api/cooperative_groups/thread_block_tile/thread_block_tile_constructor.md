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

- [ThreadBlockTile协作组sync](sync.md)（`related`）：ThreadBlockTile协作组sync 与《thread_block_tile构造函数》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《thread_block_tile构造函数》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [NumThreads](num_threads.md)（`same_topic`）：NumThreads 与《thread_block_tile构造函数》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [thread_block_tile简介](thread_block_tile_intro.md)（`same_topic`）：《thread_block_tile简介》明确“thread_block_tile是一个模板类，用于管理指定大小的线程子组。”；它与《thread_block_tile构造函数》的“thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。”在实际调用参数、数据流或结果校验上直接衔接。
- [tiled_partition](../tiled_partition.md)（`same_topic`）：《thread_block_tile构造函数》明确“thread_block_tile不提供默认构造函数，可通过tiled_partition接口从另一个协作组中划分得到。”；它与《tiled_partition》的“将线程组划分为多个更小、固定大小的子组，提供模板和非模板版本，分别用于编译时和运行时确定划分大小，模板版本支持跨Warp。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
