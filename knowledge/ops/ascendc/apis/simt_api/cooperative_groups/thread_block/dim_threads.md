---
type: API
title: DimThreads
description: 获取当前线程所属线程块的线程配置，返回值与内置变量blockDim相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block/dim_threads.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# DimThreads

获取当前线程所属线程块的线程配置，返回值与内置变量blockDim相同。
函数原型：static dim3 dim_threads()
返回值：当前线程所属线程块的线程配置。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [线程块数量配置优化](../../../../guides/operator_practice/simt_operator_optimization/execution_config/thread_block_config.md)（`explains`）：线程块数量配置优化说明SIMT算子线程块数量应结合物理核数与数据规模设置，大数据量匹配物理核数，小数据量需实测最优值。
- [thread_block构造函数](thread_block_constructor.md)（`related`）：thread_block构造函数 与《DimThreads》的实质衔接是：构造得到的 thread_block 对象承载当前 block 的 size、索引、维度和 sync 操作；这些成员方法只能在该协作组对象及其 scratch 约束下使用。
- [GroupDim](group_dim.md)（`same_topic`）：GroupDim 与《DimThreads》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [NumThreads](num_threads.md)（`same_topic`）：DimThreads 返回线程块的三维尺寸，而 NumThreads 返回三维乘积；两者用于从形状到总线程数的同一查询。
- [ThreadBlock](thread_block.md)（`same_topic`）：DimThreads 给出三维线程布局，补充 size 的总量信息。
- [ThreadBlock协作组size](size.md)（`same_topic`）：ThreadBlock协作组size 与《DimThreads》的实质衔接是：size 与 num_threads 等价；thread_block 构造、DimThreads、ThreadIndex/ThreadRank 和 GroupDim 把总线程数与三维坐标、线性 rank 关联起来。
- [ThreadIndex](thread_index.md)（`same_topic`）：DimThreads 给出三维尺寸，ThreadIndex 的每一维必须落在该范围内。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank 与《DimThreads》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
<!-- cannbot:related:end -->
