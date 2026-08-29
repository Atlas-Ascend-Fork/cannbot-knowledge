---
type: API
title: SetInferDataType
description: 使用图模式时，需要调用该接口注册DataType推导函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/SetInferDataType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SetInferDataType

## 功能说明
使用图模式时，需要调用该接口注册DataType推导函数。
## 函数原型
## 参数说明
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [SetInferShape](set_infer_shape.md)（`same_topic`）：使用图模式时，需要调用该接口注册DataType推导函数。 使用图模式时，需要调用该接口注册Shape推导函数。 图模式 OpDef 分别需要 dtype 和 shape 推导注册，两接口共同闭合输出元数据推导。
<!-- cannbot:related:end -->
