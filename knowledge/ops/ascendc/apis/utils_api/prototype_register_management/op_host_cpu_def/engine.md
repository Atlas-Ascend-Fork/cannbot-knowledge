---
type: API
title: Engine（原型注册管理）
description: 配置算子调用的引擎，入参固定为“DNN_VM_HOST_CPU”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpHostCPUDef/Engine.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Engine

## 功能说明
配置算子调用的引擎，入参固定为“DNN_VM_HOST_CPU”。
## 函数原型
## 参数说明
## 返回值说明
OpHostCPUDef算子定义，OpHostCPUDef请参考OpHostCPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Engine（原型注册管理）](../op_aicpu_def/engine.md)（`same_topic`）：Engine（原型注册管理）说明配置算子调用的引擎，入参固定为“DNN_VM_AICPU”。
- [OpHostCPUDef](op_host_cpu_def.md)（`same_topic`）：Engine 为 HostCPU 实现指定执行引擎，是 OpHostCPUDef 的关键运行配置。
- [OpKernelLib](op_kernel_lib.md)（`same_topic`）：OpKernelLib 与《Engine（原型注册管理）》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
<!-- cannbot:related:end -->
