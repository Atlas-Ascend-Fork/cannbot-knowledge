---
type: API
title: BuildKernelRunContext
description: 构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/BuildKernelRunContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# BuildKernelRunContext

## 功能说明
构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。
## 函数原型
## 参数说明
无
## 返回值说明
KernelRunContextHolder的共享指针，可通过GetContext()函数获取KernelContext对象。
## 约束说明
无
