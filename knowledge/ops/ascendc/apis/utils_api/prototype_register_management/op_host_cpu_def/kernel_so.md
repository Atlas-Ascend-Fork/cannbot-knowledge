---
type: API
title: KernelSo
description: 配置HostCPU算子实现文件编译生成的动态库文件的名称。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpHostCPUDef/KernelSo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# KernelSo

## 功能说明
配置HostCPU算子实现文件编译生成的动态库文件的名称。
## 函数原型
## 参数说明
## 返回值说明
OpHostCPUDef算子定义，OpHostCPUDef请参考OpHostCPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [FunctionName](function_name.md)（`related`）：KernelSo 定位实现库，FunctionName 固定库内入口 RunCpuKernel；运行时装载需要库名和函数名两级定位。
- [OpkernelLib](../op_aicpu_def/opkernel_lib.md)（`related`）：OpkernelLib 与《KernelSo》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [OpHostCPUDef](op_host_cpu_def.md)（`same_topic`）：KernelSo 指定承载函数的共享库，与 FunctionName 共同完成运行时加载。
- [OpKernelLib](op_kernel_lib.md)（`same_topic`）：OpKernelLib 与《KernelSo》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
<!-- cannbot:related:end -->
