---
type: API
title: ThreadRank
description: 获取当前线程在线程块内所有线程中的排名，排名从0开始。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadRank

获取当前线程在线程块内所有线程中的排名，排名从0开始。
函数原型：static unsigned int thread_rank()
返回值：当前线程在线程块内所有线程中的排名（等价于threadIdx.x + threadIdx.y  blockDim.x + threadIdx.z  blockDim.x * blockDim.y）。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [NumThreads](num_threads.md)（`related`）：ThreadRank 提供线性线程序号，与 NumThreads 一起界定合法 rank 范围。
- [ThreadIndex](thread_index.md)（`related`）：ThreadRank 提供线性序号，可由 ThreadIndex 和 DimThreads 推导；两者按索引表达选型。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《ThreadRank》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [DimThreads](dim_threads.md)（`same_topic`）：ThreadRank 与《DimThreads》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《ThreadRank》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [GroupIndex](group_index.md)（`same_topic`）：ThreadRank 与《GroupIndex》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [ThreadBlock](thread_block.md)（`same_topic`）：ThreadRank 与《ThreadBlock》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [ThreadBlock协作组size](size.md)（`same_topic`）：ThreadBlock协作组size 与《ThreadRank》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
- [ThreadRank](../coalesced_group/thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadRank》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [ThreadRank](../grid_group/thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadRank》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [ThreadRank](../thread_block_tile/thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadRank》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [thread_block简介](thread_block_intro.md)（`same_topic`）：ThreadRank 与《thread_block简介》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
<!-- cannbot:related:end -->
