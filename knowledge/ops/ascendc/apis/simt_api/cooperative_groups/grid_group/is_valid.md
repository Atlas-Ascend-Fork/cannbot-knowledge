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

- [GridGroupConstructor](grid_group_constructor.md)（`same_topic`）：this_grid 得到对象后可用 IsValid 验证当前执行配置是否支持 grid_group 操作。
- [Grid协作组sync](sync.md)（`same_topic`）：IsValid 专门回答该对象能否调用 sync；当前实现固定 true，随后可执行跨块同步。
<!-- cannbot:related:end -->
