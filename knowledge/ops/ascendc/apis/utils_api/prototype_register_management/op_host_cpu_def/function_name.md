---
type: API
title: FunctionName
description: 配置自定义算子调用的kernel函数接口名称，functionName固定为“RunCpuKernel”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpHostCPUDef/FunctionName.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# FunctionName

## 功能说明
配置自定义算子调用的kernel函数接口名称，functionName固定为“RunCpuKernel”。
## 函数原型
## 参数说明
## 返回值说明
OpHostCPUDef算子定义，OpHostCPUDef请参考OpHostCPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [KernelSo](kernel_so.md)（`related`）：KernelSo 定位实现库，FunctionName 固定库内入口 RunCpuKernel；运行时装载需要库名和函数名两级定位。
- [FunctionName](../op_aicpu_def/function_name.md)（`same_topic`）：FunctionName 与《FunctionName》的实质衔接是：FunctionName 在 OpAICPUDef 中指定 RunCpuKernel，OpHostCPUDef 对应方法及 Engine/OpkernelLib 决定该入口由哪个运行引擎和库加载。
- [OpHostCPUDef](op_host_cpu_def.md)（`same_topic`）：FunctionName 把注册对象绑定到实际 HostCPU 函数符号，是从定义到实现的直接契约。
- [OpKernelLib](op_kernel_lib.md)（`same_topic`）：OpKernelLib 与《FunctionName》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
<!-- cannbot:related:end -->
