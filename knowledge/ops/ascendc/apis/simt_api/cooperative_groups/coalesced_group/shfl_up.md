---
type: API
title: ShflUp
description: 获取coalesced_group组内当前线程向前偏移delta的线程的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/shfl_up.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShflUp

获取coalesced_group组内当前线程向前偏移delta的线程的数据。
函数原型：T shfl_up(T var, unsigned int delta) const
返回值：coalesced_group组内当前线程向前偏移delta的线程输入的var值。若偏移后超出组范围，返回当前线程输入的var值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
