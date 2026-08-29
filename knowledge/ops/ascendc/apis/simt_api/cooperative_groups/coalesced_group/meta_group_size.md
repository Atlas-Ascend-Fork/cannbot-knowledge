---
type: API
title: MetaGroupSize
description: 获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/meta_group_size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# MetaGroupSize

获取当前线程所在的协作组其直接父组被划分时创建的子组的数量。
函数原型：unsigned long long meta_group_size() const
返回值：直接父组被划分时创建的子组的数量。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
