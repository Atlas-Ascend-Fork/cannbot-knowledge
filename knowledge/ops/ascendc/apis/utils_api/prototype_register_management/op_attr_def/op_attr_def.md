---
type: API
title: OpAttrDef
description: OpAttrDef算子属性定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAttrDef/OpAttrDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpAttrDef

OpAttrDef 用于定义算子属性，支持通过链式调用设置属性名称、数据类型（Bool/Float/Int/String 及对应 List 变体）、属性类型（OPTIONAL 或 REQUIRED）、默认值、版本号和注释。OPTIONAL 属性必须设置默认值。Version 接口用于新增可选属性时保持 aclnn 接口兼容性，版本号从 1 开始连续配置。
Comment 接口用于设置算子属性注释，在自动生成算子原型头文件时同步生成注释，辅助理解算子原型并自动生成文档说明。
本入口包含 OpAttrDef 类成员函数说明与 Comment 接口说明两部分导航。
