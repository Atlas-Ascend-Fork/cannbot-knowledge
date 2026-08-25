---
type: API
title: Comment
description: 设置input/output参数的注释，用于自动生成算子原型头文件时同步生成注释，辅助理解算子原型并支持自动生成文档说明。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/Comment.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Comment

## 功能说明
设置input/output参数的注释。用于在自动生成算子原型头文件时，同步生成算子原型注释。
基于OpDef算子原型定义，自定义算子工程可以实现如下自动化能力：自动生成图模式场景使用的算子原型头文件，开发者可以使用生成的算子原型进行构图、图编译、图执行等操作。
生成的注释有助于辅助理解算子原型，并可以基于这些注释自动生成算子原型的文档说明。通常情况下，内置CANN算子使用较多。开发者可以按需使用。
## 函数原型
## 参数说明
## 返回值说明
算子参数定义，OpParamDef请参考OpParamDef。
## 约束说明
无
