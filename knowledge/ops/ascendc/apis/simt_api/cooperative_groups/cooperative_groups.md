---
type: API
title: 协作组
description: SIMT API协作组类接口汇总，提供grid_group、thread_block、coalesced_group、thread_block_tile等线程组抽象与同步能力。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/cooperative_groups.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 协作组

cooperative_groups是Ascend C SIMT编程模型的拓展，用于组织协作线程组，实现更细粒度的线程并行协作。头文件为simt_api/cooperative_groups.h，所有API位于cooperative_groups命名空间下。
提供四种协作组类型：thread_block（线程块抽象）、coalesced_group（Warp活跃线程子集）、thread_block_tile（手动划分线程子组）、grid_group（Grid内所有线程抽象）。
划分操作含tiled_partition（按指定大小划分子组）和binary_partition（按0/1标签二分）。通用操作sync同步指定协作组内所有线程。grid_group仅支持SIMT编程场景，不支持SIMD与SIMT混合编程。

<!-- cannbot:related:start -->
## 相关

- [SIMT协作组简介（高级编程）](../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：高级编程指南给出协作组在线程划分、组内同步和 Warp 分支场景中的使用方式，补全接口汇总页之外的编程流程。
- [CoalescedGroup](coalesced_group/coalesced_group.md)（`related`）：CoalescedGroup 把分支后仍活跃的 Warp 线程组成子组，并提供投票与 shuffle，具体化汇总页的动态活跃线程协作能力。
- [GridGroup](grid_group/grid_group.md)（`related`）：GridGroup 是 cooperative_groups 的 Grid 级协作对象，覆盖跨 Thread Block 的组级操作。
- [ThreadBlock](thread_block/thread_block.md)（`related`）：ThreadBlock 是汇总页列出的四种组之一，定义整线程块的索引、维度和块内 sync，覆盖最常用的块级协作范围。
- [ThreadBlockTile](thread_block_tile/thread_block_tile.md)（`related`）：ThreadBlockTile 是 cooperative_groups 提供的固定大小线程块子组，用于组内同步与 shuffle。
- [ThreadBlockTile协作组sync](thread_block_tile/sync.md)（`related`）：ThreadBlockTile协作组sync 与《协作组》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [Ballot](thread_block_tile/ballot.md)（`same_topic`）：Ballot 与《协作组》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [NumThreads](thread_block_tile/num_threads.md)（`same_topic`）：NumThreads 与《协作组》的实质衔接是：NumThreads 返回当前 thread_block_tile 的规模；tile 构造、size、rank、ballot 和 partition 决定成员集合，其他 group 的同名接口不能混用对象作用域。
- [binary_partition](binary_partition.md)（`same_topic`）：binary_partition 与《协作组》的实质衔接是：binary_partition 与 tiled_partition 都从 cooperative group 派生子组，meta_group rank/size、size 与 sync 决定分区后的线程身份和同步范围。
- [协作组简介](cooperative_groups_intro.md)（`same_topic`）：协作组汇总页与简介共同定义四类线程组、tiled/binary 划分和 sync 操作，并补充命名空间与头文件。
<!-- cannbot:related:end -->
