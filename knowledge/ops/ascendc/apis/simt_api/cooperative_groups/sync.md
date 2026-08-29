---
type: API
title: sync（协作组）
description: 同步指定协作组内的所有线程，功能等价于调用该协作组对象的成员函数sync()。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/sync.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# sync（协作组）

同步指定协作组内的所有线程，功能等价于调用该协作组对象的成员函数sync()。
函数原型：void sync(const GroupType& g)
约束：对于grid_group，该接口仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。；必须保证协作组内所有线程都能执行到同一个sync(g)调用，否则是未定义行为。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Grid协作组sync](grid_group/sync.md)（`same_topic`）：同步指定协作组内的所有线程，功能等价于调用该协作组对象的成员函数sync()。；同步当前Grid内所有SIMT线程。所有线程块中的所有线程都执行到该同步点位置后，Grid内线程才能继续执行。。自由函数 sync 明确等价于协作组对象的成员 sync，GridGroup 成员卡给出 Grid 内全部 SIMT 线程到达屏障后的继续条件，二者是同一 Grid 协作组同步合同的两种调用形式。
<!-- cannbot:related:end -->
