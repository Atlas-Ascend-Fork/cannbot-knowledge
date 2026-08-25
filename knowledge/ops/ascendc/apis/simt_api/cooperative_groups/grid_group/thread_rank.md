---
type: API
title: ThreadRank
description: 获取当前线程在Grid内所有线程中的排名，排名从0开始计数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/thread_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadRank

获取当前线程在Grid内所有线程中的排名，排名从0开始计数。
函数原型：static unsigned long long thread_rank()
返回值：当前线程在Grid内所有SIMT线程中的排名。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [NumThreads](num_threads.md)（`related`）：NumThreads：grid_group 的 NumThreads 与 size共同给出网格总线程数，ThreadRank据此界定合法索引，GroupDim/NumBlocks说明总数的分解，构造函数提供对象来源。 目标卡《ThreadRank》补充：获取当前线程在Grid内所有线程中的排名，排名从0开始计数。
- [BlockIndex](block_index.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《BlockIndex》补充：获取当前线程所属线程块在Grid中的三维索引。
- [BlockRank](block_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《BlockRank》补充：获取当前线程所属线程块在Grid内所有线程块中的排名，排名从0开始计数。
- [GridGroupConstructor](grid_group_constructor.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《GridGroupConstructor》补充：grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
- [Grid协作组size](size.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《Grid协作组size》补充：获取当前Grid内的SIMT线程总数，与接口num_threads功能相同。
- [GroupDim](group_dim.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《GroupDim》补充：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
- [NumBlocks](num_blocks.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《NumBlocks》补充：获取当前Grid内的线程块总数。
- [ThreadRank](../thread_block/thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadRank》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [grid_group简介](grid_group_intro.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《grid_group简介》补充：grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。
<!-- cannbot:related:end -->
