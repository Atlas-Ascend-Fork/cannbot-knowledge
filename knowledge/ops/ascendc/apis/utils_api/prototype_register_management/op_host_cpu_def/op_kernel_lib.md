---
type: API
title: OpKernelLib
description: 配置算子调用的kernelLib，HostCPU自定义算子调用的kernelLib固定为“CUSTHOSTCPUKernel”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpHostCPUDef/OpKernelLib.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpKernelLib

## 功能说明
配置算子调用的kernelLib，HostCPU自定义算子调用的kernelLib固定为“CUSTHOSTCPUKernel”。
## 函数原型
## 参数说明
## 返回值说明
OpHostCPUDef算子定义，OpHostCPUDef请参考OpHostCPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Engine（原型注册管理）](engine.md)（`same_topic`）：OpKernelLib 与《Engine（原型注册管理）》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
- [FunctionName](function_name.md)（`same_topic`）：OpKernelLib 与《FunctionName》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
- [KernelSo](kernel_so.md)（`same_topic`）：OpKernelLib 与《KernelSo》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
- [OpHostCPUDef](op_host_cpu_def.md)（`same_topic`）：OpKernelLib 与《OpHostCPUDef》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
- [OpkernelLib](../op_aicpu_def/opkernel_lib.md)（`same_topic`）：OpKernelLib 与《OpkernelLib》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
<!-- cannbot:related:end -->
