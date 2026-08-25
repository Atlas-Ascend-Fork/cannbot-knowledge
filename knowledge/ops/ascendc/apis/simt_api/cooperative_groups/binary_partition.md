---
type: API
title: binary_partition
description: 根据标签将父组划分为两个子组，标签相同的线程被分配到同一组中。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/binary_partition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# binary_partition

binary_partition API用于根据一个标签（0或1）将父组划分为两个子组，标签相同的线程会被分配到同一组中。
函数原型：coalesced_group binary_partition(const coalesced_group& g, bool pred)
返回值：返回划分出的子组coalesced_group对象。
约束：当g为thread_block_tile类型时，g必须满足Size小于等于32，否则编译报错。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
