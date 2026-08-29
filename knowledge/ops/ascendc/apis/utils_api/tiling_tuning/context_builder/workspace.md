---
type: API
title: Workspace（Utils API）
description: 传入指向gert::ContinuousVector的指针。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/Workspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Workspace

## 功能说明
传入指向gert::ContinuousVector的指针。
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
由于TilingContext与KernelContext、TilingParseContext内部数据排序不同，Workspace()只支持以调用BuildTilingContext()为前提来使用；其他场景建议用Outputs接口，否则发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [BuildTilingContext](build_tiling_context.md)（`related`）：“由于TilingContext与KernelContext、TilingParseContext内部数据排序不同，Workspace()只支持以调用BuildTilingContext()为前提来使用；其他场景建议用Outputs接口，否则发生未定义行为。”把 BuildTilingContext 设为 Workspace() 的硬前置条件；“构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。”说明该构造调用产出可取得 TilingContext 的 holder。该边用于避免在 KernelContext/TilingParseContext 排布下误读 workspace。
<!-- cannbot:related:end -->
