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

- [AddOutputTd](add_output_td.md)（`related`）：AddOutputTd 与《Workspace（Utils API）》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [Outputs（Utils API）](outputs.md)（`related`）：Workspace 正文明确指出非 BuildTilingContext 场景应改用 Outputs，目标卡给出 void* 输出表的合法注入方式。
- [TilingData](tiling_data.md)（`related`）：TilingData 与 Workspace 具有相同的内部排序前提：只允许配合 BuildTilingContext，其他上下文改走 Outputs。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：Workspace 的约束要求后续走 BuildTilingContext；该接口正是将注入布局解释成 TilingContext 的消费者。
- [ContextBuilder](context_builder.md)（`same_topic`）：ContextBuilder 索引明确列出 Workspace 注入和最终 BuildTilingContext/BuildKernelRunContext 两种构建出口。
- [Utils API简介](intro.md)（`same_topic`）：ContextBuilder 介绍说明该类用于手工构造 TilingContext/KernelContext 做 Tiling 单测，Workspace 是其中的输出指针注入项。
<!-- cannbot:related:end -->
