---
type: API
title: ThreadBlockTile协作组all
description: 判断thread_block_tile组内所有线程的输入是否均不为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/all.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ThreadBlockTile协作组all

判断thread_block_tile组内所有线程的输入是否均不为0。
函数原型：int all(int predicate) const
返回值：thread_block_tile组内所有线程的输入均不为0，返回1，否则返回0。
约束：当thread_block_tile的模板参数Size大于32时，即Size为64、128、256、512、1024、2048的跨Warp协作组场景，必须保证thread_block_tile组内线程均处于活跃状态，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [ThreadBlockTile协作组any](any.md)（`related`）：all 要求 tile 内所有活跃线程 predicate 非零，any 只需至少一个；二者是 group vote 中全称与存在量词的直接选择。
- [asc_all](../../warp_functions/warp_vote_functions/asc_all.md)（`related`）：asc_all 与《ThreadBlockTile协作组all》的实质衔接是：asc_all 对活跃 warp predicate 做全真归约，any/ballot/activemask 与 cooperative-group all 是返回形式和作用域的直接对照。
- [Ballot](ballot.md)（`same_topic`）：Ballot 与《ThreadBlockTile协作组all》的实质衔接是：Ballot 把 thread_block_tile 各线程谓词压成位图；all/any、size、sync 与 tile 构造定义参与线程，warp vote 和分支优化说明结果的实际用途。
- [CoalescedGroup协作组all](../coalesced_group/all.md)（`same_topic`）：CoalescedGroup协作组all 与《ThreadBlockTile协作组all》的实质衔接是：coalesced_group::all 对当前活跃组做全真归约；构造/size/rank、any/ballot、tile all 与 warp asc_all 用于核对组作用域和返回形式。
<!-- cannbot:related:end -->
