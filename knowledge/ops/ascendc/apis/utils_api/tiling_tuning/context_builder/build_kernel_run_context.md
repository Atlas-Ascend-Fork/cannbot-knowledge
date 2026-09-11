---
type: API
title: BuildKernelRunContext
description: 构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/BuildKernelRunContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
---

# BuildKernelRunContext<a name="ZH-CN_TOPIC_0000002078653622"></a>

## 功能说明<a name="zh-cn_topic_0000001867409733_zh-cn_topic_0000001389787297_section36583473819"></a>

构造KernelRunContext并返回[KernelRunContextHolder](kernel_run_context_holder_struct_definition.md)的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。

## 函数原型<a name="zh-cn_topic_0000001867409733_zh-cn_topic_0000001389787297_section13230182415108"></a>

```
std::shared_ptr<KernelRunContextHolder> BuildKernelRunContext()
```

## 参数说明<a name="zh-cn_topic_0000001867409733_zh-cn_topic_0000001389787297_section75395119104"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001867409733_zh-cn_topic_0000001389787297_section25791320141317"></a>

KernelRunContextHolder的共享指针，可通过`GetContext<gert::KernelContext>()`函数获取KernelContext对象。

## 约束说明<a name="zh-cn_topic_0000001867409733_zh-cn_topic_0000001389787297_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001867409733_zh-cn_topic_0000001389787297_section320753512363"></a>

```
auto kernelContextHolder = context_ascendc::ContextBuilder().Inputs().Outputs().BuildKernelRunContext();
gert::KernelContext* tilingParseContext = kernelContextHolder->GetContext<gert::KernelContext>();
```



<!-- cannbot:related:start -->
## 相关

- [BuildTilingContext](build_tiling_context.md)（`related`）：“构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。”与“构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。”是双方正文中的具体合同。两端都构造 KernelRunContextHolder 并通过 GetContext 暴露上下文，分别服务 KernelContext 与 TilingContext，互读能完成调测上下文构造链选型。
<!-- cannbot:related:end -->
