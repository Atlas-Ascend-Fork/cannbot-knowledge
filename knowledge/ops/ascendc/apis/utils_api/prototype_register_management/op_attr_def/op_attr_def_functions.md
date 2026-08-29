---
type: API
title: OpAttrDef
description: class OpAttrDef {
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAttrDef/OpAttrDef_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# OpAttrDef

## 功能说明
定义算子属性。
## 函数原型
## 函数说明
OpAttrDef类成员函数说明
函数名称：入参说明：功能说明
OpAttrDef：name: 算子属性名称。：构造算子属性定义OpAttrDef，并设置属性名称。
OpAttrDef：attr_def: 已构造完成的算子属性OpAttrDef。：拷贝构造OpAttrDef，复制被拷贝对象的属性名称、属性数据类型、属性类型、默认值、版本号和注释等配置。
AttrType：attr_type: 属性类型：设置算子属性类型，取值为：OPTIONAL（可选）、REQUIRED（必选）。
Bool：无：设置算子属性数据类型为Bool
Bool：value：设置算子属性数据类型为Bool，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
Float：无：设置算子属性数据类型为Float
Float：value：设置算子属性数据类型为Float，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
Int：无：设置算子属性数据类型为Int
Int：value：设置算子属性数据类型为Int，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
String：无：设置算子属性数据类型为String
String：value：设置算子属性数据类型为String，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListBool：无：设置算子属性数据类型为ListBool
ListBool：value：设置算子属性数据类型为ListBool，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListFloat：无：设置算子属性数据类型为ListFloat
ListFloat：value：设置算子属性数据类型为ListFloat，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListInt：无：设置算子属性数据类型为ListInt
ListInt：value：设置算子属性数据类型为ListInt，并设置属性默认值为value。属性类型设置为OPTIONAL时必须调用该类接口设置默认值。
ListListInt：无：设置算子属性数据类型为ListListInt
ListListInt：value
