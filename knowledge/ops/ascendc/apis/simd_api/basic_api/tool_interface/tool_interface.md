---
type: API
title: 工具接口
description: 工具接口API总览，涵盖系统初始化、执行模式、NumericLimits工具类与系统资源变量等子模块。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/tool_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 工具接口

工具接口 API 总览，涵盖四个子模块：系统初始化、执行模式、NumericLimits 工具类与系统资源变量。
系统初始化模块提供 InitSocState 等接口，用于初始化 AI Core 全局状态。
执行模式模块用于配置算子执行模式相关参数。
NumericLimits 工具类提供各数据类型的数值极限信息，如最大值、最小值等。
系统资源与变量模块提供系统级资源管理和变量查询接口。
