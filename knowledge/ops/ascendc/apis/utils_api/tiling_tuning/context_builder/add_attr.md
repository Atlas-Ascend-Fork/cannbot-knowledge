---
type: API
title: AddAttr
description: 设置算子的属性以及对应值
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddAttr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddAttr

设置算子的属性名称及对应值。函数签名为 ContextBuilder& AddAttr(const std::string& attrName, attrValue)，通过重载支持 int64_t、bool、std::string、float 及对应 vector 类型。
参数 attrName 为算子属性名称，attrValue 为属性值，支持标量与向量两种形式。
返回当前 ContextBuilder 对象，支持链式调用。
约束：AddAttr 不支持重复添加同名的属性。
典型用法：builder.NodeIoNum(1,1).IrInstanceNum({1}).AddAttr("attr_1", 1).AddAttr("attr_2", true).AddAttr("attr_3", "stringValue")。
