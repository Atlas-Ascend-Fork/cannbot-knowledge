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

<!-- cannbot:related:start -->
## 相关

- [Comment](../op_def/comment.md)（`related`）：OpParamDef::Comment 为 input/output 参数生成注释，与 OpDef::Comment 的算子级说明形成层级化文档。
- [Comment（原型注册管理）](../op_attr_def/comment.md)（`related`）：OpParamDef 的 Comment 为输入输出参数生成注释，而本接口为属性生成注释，需按元数据对象选用。
- [Input（OpDef）](../op_def/input.md)（`same_topic`）：Comment 与《Input（OpDef）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [Input（原型注册管理）](../op_ai_core_config/input.md)（`same_topic`）：Comment 与《Input（原型注册管理）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [OpParamDef](op_param_def.md)（`same_topic`）：Comment 与《OpParamDef》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [Output（OpDef）](../op_def/output.md)（`same_topic`）：Comment 与《Output（OpDef）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [原型注册与管理](../prototype_register_management.md)（`same_topic`）：Comment 与《原型注册与管理》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
- [构造&拷贝构造函数（OpParamDef）](constructor_and_copy_constructor.md)（`same_topic`）：Comment 与《构造&拷贝构造函数（OpParamDef）》的实质衔接是：Comment 写入 OpParamDef 的 input/output 注释并传播到自动生成原型和文档；构造、Input/Output、OpDef 与另一注册层 Comment 是同一元数据链。
<!-- cannbot:related:end -->
