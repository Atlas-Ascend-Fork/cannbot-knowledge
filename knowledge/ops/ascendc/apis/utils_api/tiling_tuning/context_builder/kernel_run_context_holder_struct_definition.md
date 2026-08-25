---
type: API
title: KernelRunContextHolder结构定义
description: 该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/KernelRunContextHolder_struct_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# KernelRunContextHolder结构定义

该结构体为 ContextBuilder 类最终的构造结果，可通过指定接口获取内部算子信息或 KernelContext 对象。
GetContext<T>() 将 context 成员转化为模板 T 的指针，T 可选 KernelContext 及其子类如 TilingContext。
MutableComputeNodeInfo() 返回构造的 gert::ComputeNodeInfo 类指针。
成员变量包括 valueHolder（保证内部值不析构的智能指针）、computeNodeExtendHolder（可转化为 ComputeNodeInfo 的智能指针）、context（指向 KernelRunContext 的指针）。
典型用法：通过 ContextBuilder().Inputs().Outputs().BuildKernelRunContext() 获取 holder，再调用 GetContext 或 MutableComputeNodeInfo 访问内部对象。
