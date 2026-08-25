---
type: API
title: Engine（原型注册管理）
description: 配置算子调用的引擎，入参固定为“DNN_VM_AICPU”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/Engine.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Engine

## 功能说明
配置算子调用的引擎，入参固定为“DNN_VM_AICPU”。
## 函数原型
## 参数说明
## 返回值说明
OpAICPUDef算子定义，OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [KernelSo](kernel_so.md)（`related`）：AICPU 原型注册时 Engine 选择执行引擎，KernelSo 同时指定承载实现的共享库，两字段共同定位运行时实现。
- [Engine（原型注册管理）](../op_host_cpu_def/engine.md)（`same_topic`）：Engine（原型注册管理）说明配置算子调用的引擎，入参固定为“DNN_VM_AICPU”。
- [OpkernelLib](opkernel_lib.md)（`same_topic`）：OpkernelLib 与《Engine（原型注册管理）》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
<!-- cannbot:related:end -->
