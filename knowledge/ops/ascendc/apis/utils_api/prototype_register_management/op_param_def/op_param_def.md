---
type: API
title: OpParamDef
description: OpParamDef算子参数定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/OpParamDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpParamDef

OpParamDef 用于定义算子的输入输出张量参数，包括参数类型（ParamType）、数据类型（DataType、DataTypeList）、格式（Format、FormatList）、标量与标量列表（Scalar、ScalarList）等属性。还支持值依赖（ValueDepend）、连续性控制（IgnoreContiguous、AutoContiguous）、版本管理（Version）、初始值（InitValue）和参数跟随（Follow）等高级配置。
