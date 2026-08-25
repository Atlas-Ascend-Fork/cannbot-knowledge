---
type: API
title: ThreadRank
description: 获取当前线程在coalesced_group组内的排名，排名从0开始。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/thread_rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadRank

获取当前线程在coalesced_group组内的排名，排名从0开始。
函数原型：unsigned long long thread_rank() const
返回值：当前线程在coalesced_group组内的排名。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [SIMT协作组简介（高级编程）](../../../../guides/programming_guide/advanced_programming/simt_cooperative_groups.md)（`explains`）：“ThreadRank”处理获取当前线程在coalesced_group组内的排名，排名从0开始。；“SIMT协作组简介（高级编程）”明确协作组（cooperative_groups）是Ascend C SIMT编程模型的扩展，用于组织协作线程组。协作组使开发者能够控制线程协作的粒度，实现更丰富、更高效的并行处理逻辑。。实质衔接：ThreadRank 的返回范围由 coalesced_group 活跃线程集合和 num_threads 决定，构造函数给出对象来源，指南解释发散后的分组语义。
- [Ballot](ballot.md)（`related`）：Ballot 与《ThreadRank》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup协作组size](size.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《ThreadRank》说明获取当前线程在coalesced_group组内的排名，排名从0开始。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：coalesced_group简介 与《ThreadRank》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
- [CoalescedGroup协作组all](all.md)（`same_topic`）：CoalescedGroup协作组all 与《ThreadRank》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [NumThreads](num_threads.md)（`same_topic`）：“ThreadRank”处理获取当前线程在coalesced_group组内的排名，排名从0开始。；“NumThreads”明确获取coalesced_group组内线程总数。。实质衔接：ThreadRank 的返回范围由 coalesced_group 活跃线程集合和 num_threads 决定，构造函数给出对象来源，指南解释发散后的分组语义。
- [ThreadRank](../thread_block/thread_rank.md)（`same_topic`）：ThreadRank 与《ThreadRank》的实质衔接是：ThreadRank 依赖当前 thread_block 的维度、线程索引和线程数把线程线性化；其他协作组的同名 rank 说明对象作用域不可混用。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`same_topic`）：“ThreadRank”处理获取当前线程在coalesced_group组内的排名，排名从0开始。；“coalesced_group构造函数”明确coalesced_group不提供默认的构造函数，用户使用coalesced_threads函数创建coalesced_group对象。。实质衔接：ThreadRank 的返回范围由 coalesced_group 活跃线程集合和 num_threads 决定，构造函数给出对象来源，指南解释发散后的分组语义。
<!-- cannbot:related:end -->
