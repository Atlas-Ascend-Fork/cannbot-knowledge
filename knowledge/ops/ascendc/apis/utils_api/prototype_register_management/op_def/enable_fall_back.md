---
type: API
title: EnableFallBack
description: 通过本接口启用fallback配置，启用后将自动生成一个fallback函数并注册给GE。fallback函数的核心逻辑是将GE的输入、输出及属性转换为aclnn单算子API所需的参数格式，随后调用aclnn接口。动态图场景下，GE可直接调用fallback函数（函数中调用了aclnn接口），从而简化调度流程。关于fallback下发算子的详细介绍请参考《图开发》。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/EnableFallBack.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# EnableFallBack

## 功能说明
通过本接口启用fallback配置，启用后将自动生成一个fallback函数并注册给GE。fallback函数的核心逻辑是将GE的输入、输出及属性转换为aclnn单算子API所需的参数格式，随后调用aclnn接口。动态图场景下，GE可直接调用fallback函数（函数中调用了aclnn接口），从而简化调度流程。关于fallback下发算子的详细介绍请参考《图开发》。
## 函数原型
## 参数说明
无
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
-   算子需要注册并实现InferShape函数。
-   算子需要注册并实现InferDataType函数。
