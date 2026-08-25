---
type: API
title: grid_group简介
description: grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/grid_group_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# grid_group简介

grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。

Public成员函数：is_valid、sync、thread_rank、block_rank、num_threads、size、num_blocks、dim_blocks、group_dim、block_index。头文件：simt_api/cooperative_groups.h。

约束：grid_group仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [SIMT协作组简介（高级编程）](../../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：SIMT协作组简介（高级编程）说明协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
- [GroupDim](group_dim.md)（`related`）：“GroupDim”定义：获取当前Grid的线程块维度配置，与接口dim_blocks功能相同。；“grid_group简介”定义：grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。。实质衔接：GroupDim 与 DimBlocks 返回同一 Grid 三维块配置，NumBlocks 将三维配置折叠为总块数；grid_group 说明对象获取与作用域。
- [NumThreads](num_threads.md)（`related`）：NumThreads：grid_group 的 NumThreads 与 size共同给出网格总线程数，ThreadRank据此界定合法索引，GroupDim/NumBlocks说明总数的分解，构造函数提供对象来源。 目标卡《grid_group简介》补充：grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。
- [协作组简介](../cooperative_groups_intro.md)（`related`）：grid_group 是简介列出的 Grid 全线程抽象，专页给出跨 block 查询与 sync 能力及纯 SIMT 限制。
- [BlockIndex](block_index.md)（`same_topic`）：焦点处理SIMT grid 中 block 索引及 grid_group 查询；grid_group简介正文界定“grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步”。候选把线性 block 排名映射到 grid_group/GroupIndex，并用多核漏写案例验证索引分片。
- [ThreadRank](thread_rank.md)（`same_topic`）：ThreadRank：grid_group ThreadRank以NumThreads/size为上界，BlockRank/BlockIndex与GroupDim/NumBlocks解释全局rank分解，构造函数给出group对象来源。 目标卡《grid_group简介》补充：grid_group是对一个核函数启动的所有SIMT线程的抽象，线程范围覆盖当前Grid中的所有线程块及其线程。通过grid_group可以查询Grid维度、线程块排名、全局线程排名，并通过sync()在Grid范围内进行跨线程块同步。
<!-- cannbot:related:end -->
