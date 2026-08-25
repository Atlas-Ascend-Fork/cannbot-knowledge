---
type: API
title: FunctionName
description: 配置自定义算子调用的kernel函数接口名称，functionName固定为“RunCpuKernel”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/FunctionName.md
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
OpAICPUDef算子定义，OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [KernelSo](kernel_so.md)（`related`）：《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。；《FunctionName》说明配置自定义算子调用的kernel函数接口名称，functionName固定为“RunCpuKernel”。。二者在KernelSo、FunctionName、OpkernelLib和UserDefined共同确定AICPU实现动态库及入口符号的注册合同上存在可执行的直接衔接。
- [OpkernelLib](opkernel_lib.md)（`related`）：OpkernelLib 与《FunctionName》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [UserDefined](user_defined.md)（`related`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《FunctionName》说明配置自定义算子调用的kernel函数接口名称，functionName固定为“RunCpuKernel”。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [FunctionName](../op_host_cpu_def/function_name.md)（`same_topic`）：FunctionName 与《FunctionName》的实质衔接是：FunctionName 在 OpAICPUDef 中指定 RunCpuKernel，OpHostCPUDef 对应方法及 Engine/OpkernelLib 决定该入口由哪个运行引擎和库加载。
- [OpAICPUDef](op_aicpu_def.md)（`same_topic`）：FunctionName 与《OpAICPUDef》的实质衔接是：FunctionName 在 OpAICPUDef 中指定 RunCpuKernel，OpHostCPUDef 对应方法及 Engine/OpkernelLib 决定该入口由哪个运行引擎和库加载。
<!-- cannbot:related:end -->
