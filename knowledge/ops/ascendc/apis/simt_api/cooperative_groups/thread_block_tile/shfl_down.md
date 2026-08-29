---
type: API
title: ShflDown
description: 获取thread_block_tile组内当前线程向后偏移delta的线程的数据。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/thread_block_tile/shfl_down.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShflDown

获取thread_block_tile组内当前线程向后偏移delta的线程的数据。
函数原型：T shfl_down(T var, unsigned int delta) const
返回值：协作组内当前线程向后偏移delta的线程输入的var值。若偏移后超出组范围，返回当前线程输入的var值。
约束：仅支持thread_block_tile的模板参数Size小于等于32的场景，即仅支持单Warp内线程子组。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
