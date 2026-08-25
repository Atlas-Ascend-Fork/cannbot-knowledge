---
type: API
title: TilingData结构定义
description: 定义TilingData类并添加成员变量以保存Tiling参数，继承TilingDef基类后提供set/get字段、序列化保存和长度获取等接口。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_data_structure_register/TilingData_struct_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TilingData结构定义

## 功能说明
定义一个TilingData的类，添加所需的成员变量（TilingData字段），用于保存所需TilingData参数。完成该TilingData类的定义后，该类通过继承TilingDef类（用来存放、处理用户自定义Tiling结构体成员变量的基类）提供以下接口：
-   set_\{field_name\}接口：用于设置TilingData类的字段值，field_name为定义TilingData类时添加的字段名。
-   get_\{field_name\}接口：用于获取字段名为field_name的字段值。
-   SaveToBuffer接口：完成TilingData的序列化和保存。
-   GetDataSize接口：获取TilingData的长度。
-   CheckAlignAndGenPlaceHolder：该接口是内部关联接口，用于框架侧检查Tiling结构体中成员变量是否满足字节对齐要求，并对不对齐的变量进行补齐，开发者无需关注。
-   SetDataPtr接口：该接口为预留接口，开发者无需关注。
## 函数原型
-   定义一个TilingData类
-   添加通用数据类型的TilingData字段
-   添加数组类型的TilingData字段，数组的元素数据类型为通用数据类型
-   添加结构体类型的TilingData字段
-   定义结束
## 参数说明
BEGIN_TILING_DATA_DEF参数说明
TILING_DATA_FIELD_DEF参数说明
TILING_DATA_FIELD_DEF_ARR参数说明
TILING_DATA_FIELD_DEF_STRUCT参数说明
## 约束说明
-   使用时需要包含头文件register/tilingdata_base.h。
-   TILING_DATA_FIELD_DEF和TILING_DATA_FIELD_DEF_ARR中定义的变量，仅支持int8_t, uint8_t, int16_t, uint16_t, int32_t, uint32_t, int64_t, uint64_t, float数据类型。
-   TILING_DATA_FIELD_DEF_STRUCT中struct_type仅支持用BEGIN_TILING_DATA_DEF等定义的tiling结构体，不支持直接使用c++语法定义的结构体类型。
-   用户在host侧设置参数值和使用tiling数据需要使用set_xxx和get_xxx接口（xxx请替换为字段名），具体使用方法见调用示例。
-   tiling数据成员需要满足字节对齐要求，即：当前数据成员dataVar位于结构体的偏移offset满足， offset % sizeof(dataVar) == 0。
-   tiling结构体是全局属性，需注意应通过结构体名作为全局唯一标记，不同算子若注册同名不同结构tiling结构体则会发生未定义行为。
