---
type: API
title: TilingData结构注册
description: 注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_data_structure_register/TilingData_struct_register.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TilingData结构注册

## 功能说明
注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。
## 函数原型
## 参数说明
参数说明
## 约束说明
-   使用时需要包含头文件register/tilingdata_base.h。
-   中间结构体和定制tilingkey结构体需注意op_type命名规则，具体见调用示例。
-   算子定制tilingkey结构体需保证必须注册op_type默认结构体。
-   tiling结构体是全局属性，需注意应通过结构体名作为全局唯一标记，不同算子若注册同名不同结构tiling结构体则会发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [TilingData结构定义](tiling_data_struct_definition.md)（`related`）：“定义一个TilingData的类，添加所需的成员变量（TilingData字段），用于保存所需TilingData参数。”；“注册定义的TilingData结构体并和自定义算子绑定。具体使用说明请参考调用示例。”。结构定义先产生字段与序列化类型，注册步骤再把该类型绑定到算子。
<!-- cannbot:related:end -->
