---
type: API
title: GridGroupConstructor
description: grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/grid_group_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GridGroupConstructor

grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
函数原型：grid_group this_grid()
返回值：当前Grid对应的grid_group对象。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Grid协作组sync](sync.md)（`related`）：GridGroupConstructor 返回的对象是 grid 级 sync 的调用主体，形成获取对象到跨块同步的使用链。
- [NumThreads](num_threads.md)（`related`）：NumThreads：grid_group 的 NumThreads 与 size共同给出网格总线程数，ThreadRank据此界定合法索引，GroupDim/NumBlocks说明总数的分解，构造函数提供对象来源。 目标卡《GridGroupConstructor》补充：grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
- [IsValid](is_valid.md)（`same_topic`）：this_grid 得到对象后可用 IsValid 验证当前执行配置是否支持 grid_group 操作。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《GridGroupConstructor》补充：grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
<!-- cannbot:related:end -->
