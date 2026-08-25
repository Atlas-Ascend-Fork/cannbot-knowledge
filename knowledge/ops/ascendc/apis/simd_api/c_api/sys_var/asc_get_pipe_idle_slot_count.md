---
type: API
title: 指令发射队列空闲槽位查询
description: 本接口为试验接口，在后续版本中可能会调整或改进，不保证后续兼容性
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_pipe_idle_slot_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 指令发射队列空闲槽位查询

本接口为试验接口，在后续版本中可能会调整或改进，不保证后续兼容性。请开发者在使用过程中关注后续版本更新。 本接口用于获取指定流水线对应发射队列（Issue Queue）当前的空闲槽位数量。空闲槽位表示发射队列还能接收的待发射指令数量，可用于观察队列占用情况。包含以下六个函数，各函数查询的流水线、适用的AI Core和最大空闲槽位数量如下： 表1  接口、流水线与最大值对应关系
函数原型：uint8_t asc_get_pipe_mte2_idle_slot_count()
返回值：返回对应发射队列当前的空闲槽位数量，数据类型为uint8_t。
约束：使用本接口前，需要包含头文件，头文件路径为：c_api/experimental/asc_get_pipe_idle_slot_count.h。；使用前需要增加编译选项-DCANN_ASC_USE_EXPERIMENTAL开启试验特性。；各接口仅支持表1 接口、流水线与最大值对应关系所列的AI Core类型。在不支持的AI Core类型上调用时，接口返回0。此时无法区分发射队列没有空闲槽位和当前AI Core类型不支持该接口这两种情况。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
