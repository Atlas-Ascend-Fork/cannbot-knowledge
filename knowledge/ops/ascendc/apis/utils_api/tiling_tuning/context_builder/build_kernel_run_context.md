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

- [ContextBuilder](context_builder.md)（`related`）：同一 Builder 也可构造 KernelRunContext 供 TilingParse 验证，与 BuildTilingContext 对应两种调测目标。
- [Inputs（Utils API）](inputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《BuildKernelRunContext》说明构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [IrInstanceNum](ir_instance_num.md)（`related`）：IrInstanceNum 与《BuildKernelRunContext》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [Outputs（Utils API）](outputs.md)（`related`）：Outputs 配置输出 Tensor 描述，是 BuildKernelRunContext 生成完整 kernel 调用上下文前的另一必要输入。
- [Utils API简介](intro.md)（`related`）：ContextBuilder 也可构造 KernelRunContext 供 TilingParse 验证，与 TilingContext 分别服务两类回调。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《BuildKernelRunContext》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddPlatformInfo](add_platform_info.md)（`same_topic`）：AddPlatformInfo 与《BuildKernelRunContext》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：BuildTilingContext 与《BuildKernelRunContext》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：ContextBuilder构造函数 与《BuildKernelRunContext》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [KernelRunContextHolder结构定义](kernel_run_context_holder_struct_definition.md)（`same_topic`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《BuildKernelRunContext》说明构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
<!-- cannbot:related:end -->
