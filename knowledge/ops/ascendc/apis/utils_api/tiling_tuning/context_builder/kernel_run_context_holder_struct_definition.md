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

<!-- cannbot:related:start -->
## 相关

- [ContextBuilder构造函数](context_builder_constructor.md)（`related`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《ContextBuilder构造函数》说明创建ContextBuilder对象时，初始化数据成员。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [Inputs（Utils API）](inputs.md)（`related`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [Outputs（Utils API）](outputs.md)（`related`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《Outputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的output。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [BuildKernelRunContext](build_kernel_run_context.md)（`same_topic`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《BuildKernelRunContext》说明构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：BuildTilingContext 与《KernelRunContextHolder结构定义》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [ContextBuilder](context_builder.md)（`same_topic`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《ContextBuilder》说明ContextBuilder上下文构建接口索引。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
<!-- cannbot:related:end -->
