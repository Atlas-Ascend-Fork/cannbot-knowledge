---
type: API
title: Comment（原型注册管理）
description: 设置算子属性的注释。用于在自动生成算子原型头文件时，同步生成算子原型注释。 基于OpDef算子原型定义，自定义算子工程可以实现如下自动化能力：自动生成图模式场景使用的算子原型头文件，开发者可以使用生成的算子原型进行构图、图编译、图执行等操作。
  生成的注释有助于辅助理解算子原型，并可以基于这些注释自动生成算子原型的文档说明。通常情况下，内置CANN算子使用较多。开发者可以按需使用。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAttrDef/Comment.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Comment

## 功能说明
设置算子属性的注释。用于在自动生成算子原型头文件时，同步生成算子原型注释。
基于OpDef算子原型定义，自定义算子工程可以实现如下自动化能力：自动生成图模式场景使用的算子原型头文件，开发者可以使用生成的算子原型进行构图、图编译、图执行等操作。
生成的注释有助于辅助理解算子原型，并可以基于这些注释自动生成算子原型的文档说明。通常情况下，内置CANN算子使用较多。开发者可以按需使用。
## 函数原型
## 参数说明
## 返回值说明
算子属性定义，OpAttrDef请参考OpAttrDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [Comment](../op_def/comment.md)（`related`）：OpAttrDef::Comment 为单个算子属性生成注释，focal OpDef::Comment 则描述整个算子及分组；二者共同组成原型文档。
- [Comment](../op_param_def/comment.md)（`related`）：OpParamDef 的 Comment 为输入输出参数生成注释，而本接口为属性生成注释，需按元数据对象选用。
- [OpAttrDef](op_attr_def.md)（`same_topic`）：OpAttrDef 与《Comment（原型注册管理）》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
<!-- cannbot:related:end -->
