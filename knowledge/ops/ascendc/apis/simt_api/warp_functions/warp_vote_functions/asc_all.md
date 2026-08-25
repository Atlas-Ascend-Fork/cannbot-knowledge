---
type: API
title: asc_all
description: 判断是否所有活跃线程的输入均不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均不为0，返回1，否则返回0。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/asc_all.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_all

判断是否所有活跃线程的输入均不为0。

当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均不为0，返回1，否则返回0。Warp内所有活跃线程返回相同的结果。

函数原型：inline int32_t asc_all(int32_t predicate)

参数：predicate（输入）：操作数。

返回值：当Warp内所有活跃线程的输入均不为0，返回1，否则返回0。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [CoalescedGroup协作组all](../../cooperative_groups/coalesced_group/all.md)（`related`）：asc_all 与《CoalescedGroup协作组all》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [ThreadBlockTile协作组all](../../cooperative_groups/thread_block_tile/all.md)（`related`）：asc_all 与《ThreadBlockTile协作组all》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [coalesced_group简介](../../cooperative_groups/coalesced_group/coalesced_group_intro.md)（`related`）：asc_all 与《coalesced_group简介》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [Warp Vote类函数](warp_vote_functions.md)（`same_topic`）：asc_all 与《Warp Vote类函数》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [asc_activemask](asc_activemask.md)（`same_topic`）：asc_all 与《asc_activemask》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [asc_any](asc_any.md)（`same_topic`）：《asc_any》说明判断是否有活跃线程的输入不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均为0，返回0，否则返回1。Warp内所有活跃线程返回相同的结果。；《asc_all》说明判断是否所有活跃线程的输入均不为0。 当Warp内所有活跃线程执行本接口后，对所有活跃线程的输入操作数predicate进行判断，所有活跃线程的predicate均不为0，返回1，否则返回0。Warp内所有活跃线程返回相同的结果。。二者在asc_any对Warp活跃线程做投票，与all/ballot/activemask共同定义聚合谓词并影响分支收敛上存在可执行的直接衔接。
- [asc_ballot](asc_ballot.md)（`same_topic`）：asc_all 与《asc_ballot》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
<!-- cannbot:related:end -->
