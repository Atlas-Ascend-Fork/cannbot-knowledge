---
type: API
title: Input（OpDef）
description: 注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Input.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Input

## 功能说明
注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef实例，具体请参考OpParamDef。
## 约束说明
参数注册的顺序需要和算子kernel入口函数一致。
