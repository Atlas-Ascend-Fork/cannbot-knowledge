---
type: API
title: OpAICPUDef
description: OpAICPUDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/OpAICPUDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# OpAICPUDef

OpAICPUDef 用于定义算子在 AICPU 上的执行属性，包括引擎类型（Engine）、分片标志（FlagPartial）、计算开销（ComputeCost）、异步执行标志（FlagAsync）、Kernel 库与 SO 路径（OpkernelLib、KernelSo）、入口函数名（FunctionName）和扩展配置（ExtendCfgInfo）。用于 AICore 无法覆盖的场景下的算子下沉到 AICPU 执行。
