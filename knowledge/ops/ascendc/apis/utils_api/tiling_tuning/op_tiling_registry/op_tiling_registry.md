---
type: API
title: OpTilingRegistry
description: OpTilingRegistry注册接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/OpTilingRegistry.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# OpTilingRegistry

OpTilingRegistry 用于注册和管理算子的 Tiling 函数，提供构造析构、Tiling 函数获取（GetTilingFunc）和 Tiling 库动态加载（LoadTilingLibrary）接口。通过该注册机制，算子的 Tiling 策略可以在运行时动态绑定，支持 Tiling 库的独立编译与加载。
