---
type: API
title: BlockIndex
description: 获取当前线程所属线程块在Grid中的三维索引。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/block_index.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BlockIndex

获取当前线程所属线程块在Grid中的三维索引。
函数原型：static dim3 block_index()
返回值：当前线程所属线程块在Grid中的三维索引。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [多核共享首段行区间导致部分输出未写](../../../../runbooks/precision/multiblock_launch_must_derive_row_range_from_block_index.md)（`exemplifies`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；多核共享首段行区间导致部分输出未写正文界定“host 把首个行区间传给所有 block，多个核重复处理同一段；kernel 用 GetBlockIdx 推导本核区间后恢复覆盖”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [BlockRank](block_rank.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；BlockRank正文界定“获取当前线程所属线程块在Grid内所有线程块中的排名，排名从0开始计数”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [GridGroup](grid_group.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；GridGroup正文界定“SIMT协作线程组grid_group接口集合，涵盖构造、同步、线程和块索引查询等操作”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [GroupIndex](../thread_block/group_index.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；GroupIndex正文界定“获取当前线程所属的线程块在网格（grid）中的三维索引，返回值与内置变量blockIdx相同”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《BlockIndex》补充：获取当前线程所属线程块在Grid中的三维索引。
- [grid_group简介](grid_group_intro.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；grid_group简介正文界定“grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
<!-- cannbot:related:end -->
