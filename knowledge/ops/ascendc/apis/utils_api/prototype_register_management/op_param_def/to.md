---
type: API
title: To
description: 配置后调用单算子API时将aclScalar/aclScalarList的数据类型转换为指定类型，支持直接传入数据类型或传入输入名称保持一致。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/To.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# To

## 功能说明
配置该参数后，在调用单算子API(aclnnxxx)接口时，会将aclScalar/aclScalarList的数据类型转换为该参数指定的数据类型。
指定的数据类型可以通过两种方式传入：
-   直接传入datatype；
-   传入输入的名称，表示数据类型和该输入的datatype保持一致。
该接口仅在如下场景支持：
-   通过单算子API执行的方式开发单算子调用应用。
-   间接调用单算子API(aclnnxxx)接口：Pytorch框架单算子直调的场景。
## 函数原型
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
无
