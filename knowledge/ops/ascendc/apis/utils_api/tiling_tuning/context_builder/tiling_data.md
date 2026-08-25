---
type: API
title: TilingData
description: 传入指向TilingData的void\ 指针
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/TilingData.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# TilingData

## 功能说明
传入指向TilingData的void* 指针
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
由于TilingContext与KernelContext、TilingParseContext内部数据排序不同，TilingData()只支持以调用BuildTilingContext()为前提来使用；其他场景建议用Outputs接口，否则发生未定义行为。

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：“TilingData”处理传入指向TilingData的void\ 指针；“TilingDebug”明确通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。。实质衔接：ContextBuilder::TilingData 只有在 BuildTilingContext 前提下有效，其他 Context 应改用 Outputs；TilingDebug 展示该上下文构造流程。
- [Workspace（Utils API）](workspace.md)（`related`）：TilingData 与 Workspace 具有相同的内部排序前提：只允许配合 BuildTilingContext，其他上下文改走 Outputs。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：“TilingData”处理传入指向TilingData的void\ 指针；“BuildTilingContext”明确构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。实质衔接：ContextBuilder::TilingData 只有在 BuildTilingContext 前提下有效，其他 Context 应改用 Outputs；TilingDebug 展示该上下文构造流程。
- [Outputs（Utils API）](outputs.md)（`same_topic`）：“TilingData”处理传入指向TilingData的void\ 指针；“Outputs（Utils API）”明确将void\ 指针的vector设置为KernelContext的output。。实质衔接：ContextBuilder::TilingData 只有在 BuildTilingContext 前提下有效，其他 Context 应改用 Outputs；TilingDebug 展示该上下文构造流程。
<!-- cannbot:related:end -->
