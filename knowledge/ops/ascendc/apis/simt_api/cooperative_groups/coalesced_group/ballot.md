---
type: API
title: Ballot
description: 判断coalesced_group组内每个线程的输入是否非零。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/ballot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Ballot

判断coalesced_group组内每个线程的输入是否非零。
函数原型：unsigned int ballot(int predicate) const
返回值：32-bit的无符号整数：若coalesced_group组内线程输入的predicate不为0，则返回值中与线程rank对应的bit位为1，否则为0。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup协作组any](any.md)（`related`）：ballot 保留每个线程 predicate 的位图，而 any 只压缩为单个布尔结果；需要定位命中线程时应选 ballot。
- [CoalescedGroup协作组size](size.md)（`related`）：Ballot 与《CoalescedGroup协作组size》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup协作组sync](sync.md)（`related`）：Ballot 等组内集体操作前若存在数据依赖，需要用同一组的 sync 建立可见性和执行汇合。
- [ThreadRank](thread_rank.md)（`related`）：Ballot 与《ThreadRank》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [Warp Vote类函数](../../warp_functions/warp_vote_functions/warp_vote_functions.md)（`related`）：Warp Vote类函数 与《Ballot》的实质衔接是：该页自身仅列出 warp vote 成员，成员层级已由 part_of 表达；只保留直接使用 vote 做分支优化的指南及 cooperative-group Ballot 对照。
- [asc_ballot](../../warp_functions/warp_vote_functions/asc_ballot.md)（`related`）：Ballot 与《asc_ballot》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [coalesced_group构造函数](coalesced_group_constructor.md)（`related`）：Ballot 与《coalesced_group构造函数》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [coalesced_group简介](coalesced_group_intro.md)（`related`）：Ballot 与《coalesced_group简介》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [Ballot](../thread_block_tile/ballot.md)（`same_topic`）：Ballot 与《Ballot》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup](coalesced_group.md)（`same_topic`）：Ballot 与《CoalescedGroup》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
- [CoalescedGroup协作组all](all.md)（`same_topic`）：Ballot 与《CoalescedGroup协作组all》的实质衔接是：coalesced_group Ballot 依赖当前组的构造、thread rank 与 size 生成位图，asc_ballot 是 warp 入口，all/any 则是相同 predicate 的归约返回对照。
<!-- cannbot:related:end -->
