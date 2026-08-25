---
type: API
title: GroupIndex
description: 获取当前线程所属的线程块在网格（grid）中的三维索引，返回值与内置变量blockIdx相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/group_index.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GroupIndex

获取当前线程所属的线程块在网格（grid）中的三维索引，返回值与内置变量blockIdx相同。
函数原型：static dim3 group_index()
返回值：当前线程所属的线程块在网格中的三维索引。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [ThreadIndex](thread_index.md)（`related`）：GroupIndex 标识 block 在 grid 中的位置，需与 block 内 ThreadIndex 组合计算全局索引。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《GroupIndex》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [BlockIndex](../grid_group/block_index.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；GroupIndex正文界定“获取当前线程所属的线程块在网格（grid）中的三维索引，返回值与内置变量blockIdx相同”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《GroupIndex》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank 与《GroupIndex》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
<!-- cannbot:related:end -->
