---
type: API
title: Tiling调测
description: Tiling调测接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/Tiling_tuning.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Tiling调测

提供 Tiling 函数的离线调测能力，包含 OpTilingRegistry 和 ContextBuilder 两个类。OpTilingRegistry 用于加载 Tiling 实现的动态库并获取算子的 Tiling 函数指针，ContextBuilder 用于手动构造 TilingContext 或 KernelContext 以验证 Tiling 函数与 TilingParse 函数。
两者通常配合使用：ContextBuilder 构造输入参数，OpTilingRegistry 获取 Tiling 函数指针后调用执行。需包含头文件 tiling/context/context_builder.h 并链接 libtiling_api.a。
本入口包含 OpTilingRegistry 和 ContextBuilder 的成员函数导航。
