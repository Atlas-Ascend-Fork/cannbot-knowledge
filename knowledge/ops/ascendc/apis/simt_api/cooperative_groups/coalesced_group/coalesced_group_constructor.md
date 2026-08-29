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
