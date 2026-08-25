---
type: API
title: GroupDim
description: 获取当前线程所属线程块的线程配置，与接口dim_threads功能相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/group_dim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GroupDim

获取当前线程所属线程块的线程配置，与接口dim_threads功能相同。
函数原型：static dim3 group_dim()
返回值：当前线程所属线程块的线程配置。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《GroupDim》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [DimThreads](dim_threads.md)（`same_topic`）：GroupDim 与《DimThreads》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [GroupDim](../grid_group/group_dim.md)（`same_topic`）：GroupDim 与《GroupDim》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [GroupIndex](group_index.md)（`same_topic`）：GroupDim 与《GroupIndex》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [NumThreads](num_threads.md)（`same_topic`）：GroupDim 与《NumThreads》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadBlock](thread_block.md)（`same_topic`）：GroupDim 与《ThreadBlock》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadBlock协作组size](size.md)（`same_topic`）：GroupDim 与《ThreadBlock协作组size》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadIndex](thread_index.md)（`same_topic`）：GroupDim 与《ThreadIndex》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadRank](thread_rank.md)（`same_topic`）：GroupDim 与《ThreadRank》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [thread_block简介](thread_block_intro.md)（`same_topic`）：GroupDim 与《thread_block简介》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
<!-- cannbot:related:end -->
