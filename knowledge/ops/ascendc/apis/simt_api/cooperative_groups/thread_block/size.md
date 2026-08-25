---
type: API
title: ThreadBlock协作组size
description: 获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlock协作组size

获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。
函数原型：static unsigned int size()
返回值：当前线程所属线程块内的线程总数。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSyncthreads](../../sync_and_memory_fence/sync_interface/asc_syncthreads.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《ThreadBlock协作组size》明确“获取当前线程所属线程块内的线程总数，与接口num_threads功能相同。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《ThreadBlock协作组size》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [DimThreads](dim_threads.md)（`same_topic`）：ThreadBlock协作组size 与《DimThreads》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《ThreadBlock协作组size》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [NumThreads](num_threads.md)（`same_topic`）：ThreadBlock协作组size 与《NumThreads》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
- [ThreadBlock](thread_block.md)（`same_topic`）：size 查询 block 内线程总数，是 thread_block 对象最基本的消费接口。
- [ThreadIndex](thread_index.md)（`same_topic`）：ThreadBlock协作组size 与《ThreadIndex》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadBlock协作组size 与《ThreadRank》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
<!-- cannbot:related:end -->
