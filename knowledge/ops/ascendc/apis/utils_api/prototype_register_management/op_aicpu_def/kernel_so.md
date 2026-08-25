---
type: API
title: KernelSo
description: 配置AICPU算子实现文件编译生成的动态库文件的名称。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/KernelSo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# KernelSo

## 功能说明
配置AICPU算子实现文件编译生成的动态库文件的名称。
## 函数原型
## 参数说明
## 返回值说明
OpAICPUDef算子定义，OpAICPUDef请参考OpAICPUDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。；《AICPU launcher 缺 OP_ATTR_NAMES 编译错》说明无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。。二者在KernelSo、FunctionName、OpkernelLib和UserDefined共同确定AICPU实现动态库及入口符号的注册合同上存在可执行的直接衔接。
- [Engine（原型注册管理）](engine.md)（`related`）：AICPU 原型注册时 Engine 选择执行引擎，KernelSo 同时指定承载实现的共享库，两字段共同定位运行时实现。
- [FunctionName](function_name.md)（`related`）：《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。；《FunctionName》说明配置自定义算子调用的kernel函数接口名称，functionName固定为“RunCpuKernel”。。二者在KernelSo、FunctionName、OpkernelLib和UserDefined共同确定AICPU实现动态库及入口符号的注册合同上存在可执行的直接衔接。
- [OpAICPUDef](op_aicpu_def.md)（`related`）：《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。；《OpAICPUDef》说明OpAICPUDef算子定义接口索引。。二者在KernelSo、FunctionName、OpkernelLib和UserDefined共同确定AICPU实现动态库及入口符号的注册合同上存在可执行的直接衔接。
- [UserDefined](user_defined.md)（`related`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [OpkernelLib](opkernel_lib.md)（`same_topic`）：OpkernelLib 与《KernelSo》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
<!-- cannbot:related:end -->
