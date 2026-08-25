---
type: API
title: SetOpNameType
description: ContextBuilder &SetOpNameType(const std::string& opName, const std::string&
  opType)
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/SetOpNameType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# SetOpNameType

设置算子的名字与类型。函数原型：ContextBuilder &SetOpNameType(const std::string& opName, const std::string& opType)。参数：opName（输入，算子名字）、opType（输入，算子类型）。返回值：当前ContextBuilder对象的引用，支持链式调用。无约束。在构造TilingContext时必须首先调用此方法设置算子名和类型，后续才能添加输入输出描述和属性。
