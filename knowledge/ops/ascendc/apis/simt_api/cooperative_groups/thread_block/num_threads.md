---
type: API
title: NumThreads
description: 获取当前线程所属线程块内的线程总数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/num_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# NumThreads

获取当前线程所属线程块内的线程总数。
函数原型：static unsigned int num_threads()
返回值：当前线程所属线程块内的线程总数，即blockDim.x  blockDim.y  blockDim.z。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSyncthreads](../../sync_and_memory_fence/sync_interface/asc_syncthreads.md)（`related`）：《AscSyncthreads》处理“阻塞当前线程块内所有线程直到所有线程到达同步点，确保同步点前的内存操作对块内所有线程可见，常用于数据共享和并行归约。”。《NumThreads》明确“获取当前线程所属线程块内的线程总数。”，可直接用于核对SIMT block 内同步、thread fence 可见性和线程组规模合同。
- [ThreadIndex](thread_index.md)（`related`）：ThreadIndex 给出当前线程的三维坐标，需要结合 DimThreads/NumThreads 才能做线性索引和越界判断。
- [ThreadRank](thread_rank.md)（`related`）：ThreadRank 提供线性线程序号，与 NumThreads 一起界定合法 rank 范围。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《NumThreads》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [DimThreads](dim_threads.md)（`same_topic`）：DimThreads 返回线程块的三维尺寸，而 NumThreads 返回三维乘积；两者用于从形状到总线程数的同一查询。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《NumThreads》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [NumThreads](../coalesced_group/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [NumThreads](../thread_block_tile/num_threads.md)（`same_topic`）：NumThreads 与《NumThreads》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [ThreadBlock协作组size](size.md)（`same_topic`）：ThreadBlock协作组size 与《NumThreads》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
<!-- cannbot:related:end -->
