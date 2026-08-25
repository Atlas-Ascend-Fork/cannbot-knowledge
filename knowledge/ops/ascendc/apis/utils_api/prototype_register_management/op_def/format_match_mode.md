---
type: API
title: FormatMatchMode
description: 设置输入输出tensor的format匹配模式。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/FormatMatchMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# FormatMatchMode

## 功能说明
设置输入输出tensor的format匹配模式。
## 函数原型
## 参数说明
## 返回值说明
OpDef算子定义，OpDef请参考OpDef。
## 约束说明
不调用该接口的情况下，默认将NCHW/NHWC/DHWCN/NCDHW/NCL格式的输入输出转成ND格式进行处理。
