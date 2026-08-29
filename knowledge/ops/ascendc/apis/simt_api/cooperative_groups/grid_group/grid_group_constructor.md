---
type: API
title: GridGroupConstructor
description: grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/grid_group_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GridGroupConstructor

grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。
函数原型：grid_group this_grid()
返回值：当前Grid对应的grid_group对象。
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [GridGroup](grid_group.md)（`related`）：grid_group对核函数启动的所有SIMT线程进行抽象，线程范围覆盖当前Grid中所有线程块及其线程。提供is_valid有效性查询和sync跨线程块同步。；grid_group不提供默认的构造函数，用户使用this_grid函数获取当前Grid对应的grid_group对象。。对象卡说明 grid_group 能力范围，构造卡给出取得该对象并使用这些能力的唯一入口。
<!-- cannbot:related:end -->
