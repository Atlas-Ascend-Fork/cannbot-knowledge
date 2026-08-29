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

<!-- cannbot:related:start -->
## 相关

- [BuildTilingContext](build_tiling_context.md)（`related`）：“构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。”与“构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。”是双方正文中的具体合同。两端都构造 KernelRunContextHolder 并通过 GetContext 暴露上下文，分别服务 KernelContext 与 TilingContext，互读能完成调测上下文构造链选型。
<!-- cannbot:related:end -->
