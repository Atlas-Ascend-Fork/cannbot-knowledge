---
type: API
title: ContextBuilder
description: ContextBuilder上下文构建接口索引。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/ContextBuilder.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# ContextBuilder

ContextBuilder 用于在 Host 侧构建算子的 Tiling 和 Kernel 运行上下文，支持设置输入输出（Inputs、Outputs）、算子名称与类型（SetOpNameType）、输入输出 Tensor 描述（AddInputTd、AddOutputTd）和属性（AddAttr）。还提供编译信息（CompileInfo）、平台信息（AddPlatformInfo）、Tiling 数据（TilingData）和 Workspace 的注入，最终通过 BuildTilingContext 或 BuildKernelRunContext 生成上下文。
