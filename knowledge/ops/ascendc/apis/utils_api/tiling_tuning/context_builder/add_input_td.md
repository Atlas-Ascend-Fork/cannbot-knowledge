---
type: API
title: AddInputTd
description: 为算子增加输入Tensor的描述
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddInputTd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddInputTd

## 功能说明
为算子增加输入Tensor的描述
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
输入的index需要基于算子IR定义，按照IrInstanceNum声明顺序来排布；
调用AddInputTd前需要调用NodeIoNum与IrInstanceNum接口
