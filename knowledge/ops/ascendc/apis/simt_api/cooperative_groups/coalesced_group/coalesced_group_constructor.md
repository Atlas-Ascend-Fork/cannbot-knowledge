---
type: API
title: coalesced_group构造函数
description: coalesced_group不提供默认的构造函数，用户使用coalesced_threads函数创建coalesced_group对象。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/coalesced_group_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# coalesced_group构造函数

coalesced_group不提供默认的构造函数，用户使用coalesced_threads函数创建coalesced_group对象。
函数原型：coalesced_group coalesced_threads()
返回值：返回一个coalesced_group对象，该对象包含当前Warp内所有活跃的线程。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Ballot](ballot.md)（`related`）：Ballot 与《coalesced_group构造函数》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup协作组size](size.md)（`related`）：《CoalescedGroup协作组size》说明获取coalesced_group组内线程总数，与接口num_threads功能相同。；《coalesced_group构造函数》说明coalesced_group不提供默认的构造函数，用户使用coalesced_threads函数创建coalesced_group对象。。二者在coalesced_group的size与num_threads等价，构造、活跃线程语义、thread_rank和分组操作共同决定返回值与lane映射上存在可执行的直接衔接。
- [NumThreads](num_threads.md)（`related`）：NumThreads 与《coalesced_group构造函数》的实质衔接是：NumThreads 返回 group 当前线程数，coalesced/thread-block/tile 对应入口、size、ThreadRank、构造与简介共同界定不同协作组作用域。
- [CoalescedGroup](coalesced_group.md)（`same_topic`）：CoalescedGroup 与《coalesced_group构造函数》的实质衔接是：CoalescedGroup 表示分支发散后当前 warp 的活跃子集；构造/简介、协作组总览、未 coalesce 故障和分支优化指南共同界定成员身份与适用场景。
- [CoalescedGroup协作组all](all.md)（`same_topic`）：CoalescedGroup协作组all 与《coalesced_group构造函数》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [ThreadRank](thread_rank.md)（`same_topic`）：“ThreadRank”处理获取当前线程在coalesced_group组内的排名，排名从0开始。；“coalesced_group构造函数”明确coalesced_group不提供默认的构造函数，用户使用coalesced_threads函数创建coalesced_group对象。。实质衔接：ThreadRank 的返回范围由 coalesced_group 活跃线程集合和 num_threads 决定，构造函数给出对象来源，指南解释发散后的分组语义。
- [coalesced_group简介](coalesced_group_intro.md)（`same_topic`）：coalesced_group简介 与《coalesced_group构造函数》的实质衔接是：coalesced_group 表示 warp 当前活跃子集，构造、meta rank/size、thread rank、partition 与 coalesce 故障/分支指南共同界定发散后的成员身份。
<!-- cannbot:related:end -->
