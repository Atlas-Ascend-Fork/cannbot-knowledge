---
type: API
title: OpkernelLib
description: 配置算子调用的kernelLib，AICPU自定义算子调用的kernelLib固定为“CUSTAICPUKernel”。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/OpkernelLib.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpkernelLib

## 功能说明
配置算子调用的kernelLib，AICPU自定义算子调用的kernelLib固定为“CUSTAICPUKernel”。
## 函数原型
## 参数说明
## 返回值说明
OpAICPUDef算子定义，OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：OpkernelLib 与《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [AICPU（OpDef）](../op_def/aicpu.md)（`related`）：OpkernelLib 与《AICPU（OpDef）》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [FunctionName](function_name.md)（`related`）：OpkernelLib 与《FunctionName》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [KernelSo](../op_host_cpu_def/kernel_so.md)（`related`）：OpkernelLib 与《KernelSo》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [UserDefined](user_defined.md)（`related`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《OpkernelLib》说明配置算子调用的kernelLib，AICPU自定义算子调用的kernelLib固定为“CUSTAICPUKernel”。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [Engine（原型注册管理）](engine.md)（`same_topic`）：OpkernelLib 与《Engine（原型注册管理）》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [KernelSo](kernel_so.md)（`same_topic`）：OpkernelLib 与《KernelSo》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [OpAICPUDef](op_aicpu_def.md)（`same_topic`）：OpkernelLib 与《OpAICPUDef》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [OpKernelLib](../op_host_cpu_def/op_kernel_lib.md)（`same_topic`）：OpKernelLib 与《OpkernelLib》的实质衔接是：OpKernelLib、KernelSo、Engine、FunctionName 和 OpHostCPUDef 是 HostCPU 注册的一组直接字段；AICPU OpkernelLib提供不同后端固定库名对照。
<!-- cannbot:related:end -->
