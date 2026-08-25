---
type: Guide
title: SIMT协作组简介（高级编程）
description: 协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/simt_cooperative_groups.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SIMT协作组简介

协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
Ascend C SIMT编程模型中仅提供asc_syncthreads()接口来实现线程块内所有线程的同步。当开发者希望以更细粒度的方式同步线程，从而实现更灵活的设计时，往往需要自行通过内存栅栏接口实现相应的同步逻辑。协作组提供安全可靠的机制，协助开发者实现灵活、高效的线程协作。
## 协作组使用方法
协作组中最重要的概念是使用一个对象表示一组线程，然后通过对象方法控制组内线程。对象可以明确表达开发者的意图，将协作组对象传递到某个函数可以清晰地表达“哪些线程必须共同调用该函数”。
协作组提供了自定义线程组的方法以及操作线程组的接口，全量的协作组API列表可在SIMT协作组API中获取。使用协作组API时需要包含以下头文件，并使用协作组命名空间。
## 协作组类型
协作组分为隐式组和显式组。隐式组与核函数中的代码无关，它代表的是核函数的启动配置，即创建了多少个线程块，每个线程块中有多少个线程来执行核函数。隐式组为划分出更细粒度的协作组提供了起点。显式组是在核函数中由开发者手动划分出的协作组。
当前提供以下协作组类型：
- 隐式组：
- grid_group：对当前Grid中所有SIMT线程的抽象，提供Grid级别的信息查询和跨线程块同步接口。
- thread_block：对线程块的抽象，提供线程块级别的线程管理和同步接口。
- 显式组：
- thread_block_tile：由父组划分得到的固定大小线程子组，支持组内同步、shfl类和vote类线程操作。
- coalesced_group：当前Warp内处于同一执行路径的活跃线程集合，常用于处理分支发散后的线程协作。
### grid_group
grid_group表示当前核函数启动的Grid协作组，覆盖Grid内所有线程块及其SIMT线程，通过this_grid()获取。它适合需要在多个线程块之间建立执行顺序的场景。
grid_group提供Grid级别的信息查询能力和跨线程块的同步能力，例如：
- thread_rank()：获取当前线程在Grid内所有SIMT线程中的线性rank。
- block_rank()：获取当前线程所属线程块在Grid内的线性rank。
- num_threads()：获取Grid内SIMT线程总数。
- num_blocks()：获取Grid内线程块总数。
- sync()：同步Grid内所有SIMT线程。
grid_group仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
### thread_block
thread_block表示当前线程所在的线程块，通过this_thread_block()获取。它是进一步划分子协作组的常用起点。
thread_block提供线程块级别的信息查询和同步能力，例如：
- thread_rank()：获取当前线程在线程块内的线性rank。
- thread_index()：获取当前线程在线程块内的三维索引。

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup](../../../apis/simt_api/cooperative_groups/coalesced_group/coalesced_group.md)（`explains`）：CoalescedGroup 与《SIMT协作组简介（高级编程）》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [GridGroup](../../../apis/simt_api/cooperative_groups/grid_group/grid_group.md)（`explains`）：焦点处理grid_group 与 thread_block 协作范围的选择；SIMT协作组简介（高级编程）正文说明“协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑”。候选解释 grid 级和 block 级协作对象的不同同步/查询范围，避免选错作用域。
- [Grid协作组sync](../../../apis/simt_api/cooperative_groups/grid_group/sync.md)（`explains`）：SIMT协作组简介（高级编程）说明协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
- [ThreadBlockTile协作组sync](../../../apis/simt_api/cooperative_groups/thread_block_tile/sync.md)（`explains`）：ThreadBlockTile协作组sync 与《SIMT协作组简介（高级编程）》的实质衔接是：thread_block_tile::sync 依赖 tiled_partition 形成的 tile；tile 构造、线程秩与通用 cooperative-group sync 明确参与者和内存可见性边界。
- [ThreadRank](../../../apis/simt_api/cooperative_groups/coalesced_group/thread_rank.md)（`explains`）：“ThreadRank”处理获取当前线程在coalesced_group组内的排名，排名从0开始。；“SIMT协作组简介（高级编程）”明确协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。。实质衔接：ThreadRank 的返回范围由 coalesced_group 活跃线程集合和 num_threads 决定，构造函数给出对象来源，指南解释发散后的分组语义。
- [grid_group简介](../../../apis/simt_api/cooperative_groups/grid_group/grid_group_intro.md)（`explains`）：SIMT协作组简介（高级编程）说明协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。
- [协作组](../../../apis/simt_api/cooperative_groups/cooperative_groups.md)（`explains`）：高级编程指南给出协作组在线程划分、组内同步和 Warp 分支场景中的使用方式，补全接口汇总页之外的编程流程。
- [协作组简介](../../../apis/simt_api/cooperative_groups/cooperative_groups_intro.md)（`explains`）：高级指南给出隐式/显式组、作用域选择和使用方法；API 简介补齐 tiled_partition/binary_partition 及通用 sync，是同一 cooperative_groups 模型的接口入口。
<!-- cannbot:related:end -->
