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

- [Ballot](ballot.md)（`related`）：“返回值：当coalesced_group组内所有线程的输入均为0，返回0，否则返回1。”与“返回值：32-bit的无符号整数：若coalesced_group组内线程输入的predicate不为0，则返回值中与线程rank对应的bit位为1，否则为0。”是双方正文中的具体合同。两端观察同一 coalesced_group 内各线程 predicate；Any 折叠为组级布尔值，Ballot 保留逐 rank 位图，互读可按后续分支需求选择结果粒度。
<!-- cannbot:related:end -->
