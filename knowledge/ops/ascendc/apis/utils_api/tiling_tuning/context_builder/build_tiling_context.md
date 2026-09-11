---
type: API
title: BuildTilingContext
description: 构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/BuildTilingContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# BuildTilingContext<a name="ZH-CN_TOPIC_0000002114097969"></a>

## 功能说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section36583473819"></a>

构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。

## 函数原型<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section13230182415108"></a>

```
std::shared_ptr<KernelRunContextHolder> BuildTilingContext()
```

## 参数说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section75395119104"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section25791320141317"></a>

指向KernelRunContextHolder的共享指针。

## 约束说明<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001867289945_zh-cn_topic_0000001389787297_section320753512363"></a>

```
auto tilingContextHolder = context_ascendc::ContextBuilder()
  .SetOpNameType(...,...)
  .NodeIoNum(...)
  .IrInstanceNum(...)
  .AddInputTd(...)
  .AddOutputTd(...)
  .AddAttr(...)
  .BuildTilingContext(...);
gert::TilingContext *tilingContext = tilingContextHolder->GetContext<gert::TilingContext>();
```



<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：使用ContextBuilder配置输入输出Tensor的形状、数据类型、格式及平台信息等，构建TilingContext。；构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。指南中的离线调测第一个核心动作由候选 API 生成可传给 Tiling 函数的上下文。
- [BuildKernelRunContext](build_kernel_run_context.md)（`related`）：“构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。”与“构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。”是双方正文中的具体合同。两端都构造 KernelRunContextHolder 并通过 GetContext 暴露上下文，分别服务 KernelContext 与 TilingContext，互读能完成调测上下文构造链选型。
- [Workspace（Utils API）](workspace.md)（`related`）：“由于TilingContext与KernelContext、TilingParseContext内部数据排序不同，Workspace()只支持以调用BuildTilingContext()为前提来使用；其他场景建议用Outputs接口，否则发生未定义行为。”把 BuildTilingContext 设为 Workspace() 的硬前置条件；“构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。”说明该构造调用产出可取得 TilingContext 的 holder。该边用于避免在 KernelContext/TilingParseContext 排布下误读 workspace。
<!-- cannbot:related:end -->
