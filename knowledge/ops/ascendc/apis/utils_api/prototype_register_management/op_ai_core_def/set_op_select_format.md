---
type: API
title: SetOpSelectFormat
description: 如果您需要自行推导算子输入输出所支持的数据类型与格式，则可实现推导回调函数，并通过该接口进行注册。同时需要将DynamicFormatFlag配置为true，则算子融合时会自动调用推导函数进行数据类型与格式的设置，算子原型注册时无需配置输入输出支持的数据类型与格式。
  注意，如果算子原型已经注册过数据类型与格式，则以算子原型注册的数据类型与格式为准，即使注册了推导函数也不会执行。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICoreDef/SetOpSelectFormat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SetOpSelectFormat

## 功能说明
如果您需要自行推导算子输入输出所支持的数据类型与格式，则可实现推导回调函数，并通过该接口进行注册。同时需要将DynamicFormatFlag配置为true，则算子融合时会自动调用推导函数进行数据类型与格式的设置，算子原型注册时无需配置输入输出支持的数据类型与格式。
注意，如果算子原型已经注册过数据类型与格式，则以算子原型注册的数据类型与格式为准，即使注册了推导函数也不会执行。
## 函数原型
## 参数说明
## 返回值说明
OpAICoreDef算子定义，OpAICoreDef请参考OpAICoreDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [DynamicFormatFlag](../op_ai_core_config/dynamic_format_flag.md)（`related`）：标识是否根据SetOpSelectFormat设置的函数自动推导算子输入输出支持的dtype和format。设置为“true”，则无需在原型注册时配置固定的dtype与format，会调用推导函数来推导算子输入输出支持的dtype和format。；如果您需要自行推导算子输入输出所支持的数据类型与格式，则可实现推导回调函数，并通过该接口进行注册。同时需要将DynamicFormatFlag配置为true，则算子融合时会自动调用推导函数进行数据类型与格式的设置，算子原型注册时无需配置输入输出支持的数据类型与格式。。DynamicFormatFlag 打开动态推导开关，SetOpSelectFormat 注册实际回调；两者必须配合才能在融合时推导 dtype 和 format。
<!-- cannbot:related:end -->
