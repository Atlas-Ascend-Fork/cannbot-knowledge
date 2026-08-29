---
type: API
title: ContextBuilder构造函数
description: 创建ContextBuilder对象时，初始化数据成员。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/ContextBuilder_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# ContextBuilder构造函数

创建ContextBuilder对象时初始化数据成员。函数原型：ContextBuilder()。无参数、无返回值、无约束。ContextBuilder类用于手动构造TilingContext或KernelContext对象，支持Tiling函数和TilingParse函数的独立验证。构造后通过链式调用SetOpNameType、NodeIoNum、AddInputTd、AddOutputTd、AddAttr等方法配置上下文，最后调用BuildTilingContext或BuildKernelRunContext生成目标上下文。
