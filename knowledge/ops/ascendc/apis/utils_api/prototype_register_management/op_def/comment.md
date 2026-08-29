---
type: API
title: Comment
description: 设置算子分组信息及原型注释（简述、约束等），用于自动生成算子原型头文件时同步生成注释和文档说明。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/Comment.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Comment

## 功能说明
设置算子分组信息以及算子原型注释，包括算子简述，算子约束等内容。用于在自动生成算子原型头文件时，同步生成算子原型注释。
基于OpDef算子原型定义，自定义算子工程可以实现如下自动化能力：自动生成图模式场景使用的算子原型头文件，开发者可以使用生成的算子原型进行构图、图编译、图执行等操作。
生成的注释有助于辅助理解算子原型，并可以基于这些注释自动生成算子原型的文档说明。通常情况下，内置CANN算子使用较多。开发者可以按需使用。
## 函数原型
## 参数说明
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
当用户使用CATEGORY参数设置算子分组名称时，会对应生成同名的代码文件。若文件名过长在编译时可能超过tar的打包文件名称长度限制，导致报错。
具体参考算子工程编译时出现文件名过长报错。
