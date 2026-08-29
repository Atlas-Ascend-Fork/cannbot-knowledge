---
type: API
title: OpHostCPUDef
description: OpHostCPUDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpHostCPUDef/OpHostCPUDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# OpHostCPUDef

OpHostCPUDef 用于定义算子在 Host CPU 上的执行属性，包括引擎类型（Engine）、分片标志（FlagPartial）、计算开销（ComputeCost）、异步执行标志（FlagAsync）、Kernel 库与 SO 路径（OpKernelLib、KernelSo）、入口函数名（FunctionName）和扩展配置（ExtendCfgInfo）。用于算子需要在 Host 侧 CPU 执行的场景。
