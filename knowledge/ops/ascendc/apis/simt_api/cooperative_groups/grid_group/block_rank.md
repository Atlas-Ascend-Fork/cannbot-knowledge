---
type: API
title: BlockRank
description: 获取当前线程所属线程块在Grid内所有线程块中的排名，排名从0开始计数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/block_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BlockRank

获取当前线程所属线程块在Grid内所有线程块中的排名，排名从0开始计数。
函数原型：static unsigned long long block_rank()
返回值：当前线程所属线程块在Grid内的排名。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [NumBlocks](num_blocks.md)（`related`）：NumBlocks 给出 rank 的上界，可用于校验 BlockRank 是否落在 [0,num_blocks)。
- [BlockIndex](block_index.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；BlockRank正文界定“获取当前线程所属线程块在Grid内所有线程块中的排名，排名从0开始计数”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《BlockRank》补充：获取当前线程所属线程块在Grid内所有线程块中的排名，排名从0开始计数。
<!-- cannbot:related:end -->
