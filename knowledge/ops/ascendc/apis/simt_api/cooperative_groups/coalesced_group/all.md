---
type: API
title: CoalescedGroup协作组all
description: 判断coalesced_group组内所有线程的输入是否均不为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/all.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# CoalescedGroup协作组all

判断coalesced_group组内所有线程的输入是否均不为0。
函数原型：int all(int predicate) const
返回值：当coalesced_group组内所有线程的输入均不为0，返回1，否则返回0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup协作组any](any.md)（`related`）：all 与 any 分别判断组内全真和至少一真，共享 predicate 聚合契约并支持互补的分支条件。
- [asc_all](../../warp_functions/warp_vote_functions/asc_all.md)（`related`）：asc_all 与《CoalescedGroup协作组all》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《CoalescedGroup协作组all》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup](coalesced_group.md)（`same_topic`）：CoalescedGroup协作组all 与《CoalescedGroup》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [CoalescedGroup协作组size](size.md)（`same_topic`）：CoalescedGroup协作组all 与《CoalescedGroup协作组size》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [ThreadBlockTile协作组all](../thread_block_tile/all.md)（`same_topic`）：CoalescedGroup协作组all 与《ThreadBlockTile协作组all》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [ThreadRank](thread_rank.md)（`same_topic`）：CoalescedGroup协作组all 与《ThreadRank》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`same_topic`）：CoalescedGroup协作组all 与《coalesced_group构造函数》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
- [coalesced_group简介](coalesced_group_intro.md)（`same_topic`）：CoalescedGroup协作组all 与《coalesced_group简介》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
<!-- cannbot:related:end -->
