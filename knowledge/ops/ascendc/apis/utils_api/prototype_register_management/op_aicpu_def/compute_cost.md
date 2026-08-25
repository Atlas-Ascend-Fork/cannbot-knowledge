---
type: API
title: ComputeCost
description: 此参数为预留参数，请保持固定值“100”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/ComputeCost.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# ComputeCost

## 功能说明
此参数为预留参数，请保持固定值“100”。
## 函数原型
## 参数说明
## 返回值说明
OpAICPUDef算子定义，OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [ComputeCost](../op_host_cpu_def/compute_cost.md)（`same_topic`）：ComputeCost 与《ComputeCost》的实质衔接是：两张 ComputeCost 都要求固定值 100，但分别属于 OpAICPUDef 与 OpHostCPUDef；类定义决定该预留属性挂载在哪类 CPU kernel 注册上。
- [OpAICPUDef](op_aicpu_def.md)（`same_topic`）：ComputeCost 与《OpAICPUDef》的实质衔接是：两张 ComputeCost 都要求固定值 100，但分别属于 OpAICPUDef 与 OpHostCPUDef；类定义决定该预留属性挂载在哪类 CPU kernel 注册上。
<!-- cannbot:related:end -->
