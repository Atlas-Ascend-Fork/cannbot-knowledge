---
type: API
title: GroupDim
description: 获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/group_dim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GroupDim

获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
函数原型：static dim3 group_dim()
返回值：当前Grid的线程块维度配置。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [NumBlocks](num_blocks.md)（`related`）：“GroupDim”定义：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。；“NumBlocks”定义：获取当前Grid内的线程块总数。。实质衔接：GroupDim 与 DimBlocks 返回同一 Grid 三维块配置，NumBlocks 将三维配置折叠为总块数；grid_group 说明对象获取与作用域。
- [NumThreads](num_threads.md)（`related`）：NumThreads：grid_group 的 NumThreads 与 size共同给出网格总线程数，ThreadRank据此界定合法索引，GroupDim/NumBlocks说明总数的分解，构造函数提供对象来源。 目标卡《GroupDim》补充：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
- [grid_group简介](grid_group_intro.md)（`related`）：“GroupDim”定义：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。；“grid_group简介”定义：grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。。实质衔接：GroupDim 与 DimBlocks 返回同一 Grid 三维块配置，NumBlocks 将三维配置折叠为总块数；grid_group 说明对象获取与作用域。
- [DimBlocks](dim_blocks.md)（`same_topic`）：“GroupDim”定义：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。；“DimBlocks”定义：获取当前Grid的线程块维度配置。。实质衔接：GroupDim 与 DimBlocks 返回同一 Grid 三维块配置，NumBlocks 将三维配置折叠为总块数；grid_group 说明对象获取与作用域。
- [GroupDim](../thread_block/group_dim.md)（`same_topic`）：GroupDim 与《GroupDim》的衔接是：GroupDim 返回 thread_block 的三维规模；DimThreads、NumThreads、ThreadIndex、GroupIndex、size/rank 和构造函数共同把该规模转换为线程坐标与线性索引。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《GroupDim》补充：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。
<!-- cannbot:related:end -->
