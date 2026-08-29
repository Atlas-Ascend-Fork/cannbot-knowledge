---
type: API
title: IsValid
description: 判断当前grid_group是否可使用sync()接口进行跨线程块同步。grid_group默认支持同步功能，因此接口固定返回true。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/is_valid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# IsValid

判断当前grid_group是否可使用sync()接口进行跨线程块同步。grid_group默认支持同步功能，因此接口固定返回true。
函数原型：bool is_valid() const
返回值：固定返回true
约束：仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Grid协作组sync](sync.md)（`related`）：判断当前grid_group是否可使用sync()接口进行跨线程块同步。grid_group默认支持同步功能，因此接口固定返回true。；同步当前Grid内所有SIMT线程。所有线程块中的所有线程都执行到该同步点位置后，Grid内线程才能继续执行。。IsValid 查询的能力对象就是 grid_group 的 sync 跨线程块同步，sync 卡进一步给出所有线程到达同步点的执行语义与约束，因此查询与被查询操作属于同一调用决策链。
<!-- cannbot:related:end -->
