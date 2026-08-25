---
type: API
title: 构造和析构函数
description: 创建与释放OpTilingRegistry对象。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/constructor_and_destructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# OpTilingRegistry构造和析构函数

创建与释放OpTilingRegistry对象。函数原型：OpTilingRegistry()（构造函数）和~OpTilingRegistry()（析构函数）。无参数、无返回值、无约束。OpTilingRegistry用于Tiling调优场景下注册和管理算子的Tiling策略，通过构造函数创建实例后可进行Tiling策略的注册和查询，析构时自动释放资源。调用示例：context_ascendc::OpTilingRegistry tmpIns;
