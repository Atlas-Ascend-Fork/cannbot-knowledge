---
type: API
title: ThreadIndex
description: 获取当前线程在线程块中的索引，返回值与内置变量threadIdx相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/thread_index.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadIndex

获取当前线程在线程块中的索引，返回值与内置变量threadIdx相同。
函数原型：static dim3 thread_index()
返回值：当前线程在线程块中的索引。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [GroupIndex](group_index.md)（`related`）：GroupIndex 标识 block 在 grid 中的位置，需与 block 内 ThreadIndex 组合计算全局索引。
- [NumThreads](num_threads.md)（`related`）：ThreadIndex 给出当前线程的三维坐标，需要结合 DimThreads/NumThreads 才能做线性索引和越界判断。
- [ThreadRank](thread_rank.md)（`related`）：ThreadRank 提供线性序号，可由 ThreadIndex 和 DimThreads 推导；两者按索引表达选型。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《ThreadIndex》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [DimThreads](dim_threads.md)（`same_topic`）：DimThreads 给出三维尺寸，ThreadIndex 的每一维必须落在该范围内。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《ThreadIndex》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadBlock](thread_block.md)（`same_topic`）：ThreadIndex 是 thread_block group 的坐标查询，类型页界定其作用域。
- [ThreadBlock协作组size](size.md)（`same_topic`）：ThreadBlock协作组size 与《ThreadIndex》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
<!-- cannbot:related:end -->
