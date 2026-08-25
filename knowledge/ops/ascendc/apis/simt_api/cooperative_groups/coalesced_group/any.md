---
type: API
title: CoalescedGroup协作组any
description: 判断coalesced_group组内是否有线程的输入不为0。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/any.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# CoalescedGroup协作组any

判断coalesced_group组内是否有线程的输入不为0。
函数原型：int any(int predicate) const
返回值：当coalesced_group组内所有线程的输入均为0，返回0，否则返回1。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Ballot](ballot.md)（`related`）：ballot 保留每个线程 predicate 的位图，而 any 只压缩为单个布尔结果；需要定位命中线程时应选 ballot。
- [CoalescedGroup协作组all](all.md)（`related`）：all 与 any 分别判断组内全真和至少一真，共享 predicate 聚合契约并支持互补的分支条件。
<!-- cannbot:related:end -->
