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

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：TilingDebug 需在调用函数前构造输入输出描述、属性、平台和 tiling/workspace 容器；ContextBuilder 汇总这些上下文入口。
- [BuildKernelRunContext](build_kernel_run_context.md)（`related`）：同一 Builder 也可构造 KernelRunContext 供 TilingParse 验证，与 BuildTilingContext 对应两种调测目标。
- [IrInstanceNum](ir_instance_num.md)（`related`）：IrInstanceNum 与《ContextBuilder》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《ContextBuilder》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddOutputTd](add_output_td.md)（`same_topic`）：AddOutputTd 与《ContextBuilder》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [AddPlatformInfo](add_platform_info.md)（`same_topic`）：AddPlatformInfo 与《ContextBuilder》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：BuildTilingContext 与《ContextBuilder》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [CompileInfo](compile_info.md)（`same_topic`）：CompileInfo 与《ContextBuilder》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：ContextBuilder构造函数 与《ContextBuilder》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [GetTilingFunc](../op_tiling_registry/get_tiling_func.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；ContextBuilder正文界定“ContextBuilder上下文构建接口索引”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [Inputs（Utils API）](inputs.md)（`same_topic`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《ContextBuilder》说明ContextBuilder上下文构建接口索引。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [KernelRunContextHolder结构定义](kernel_run_context_holder_struct_definition.md)（`same_topic`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《ContextBuilder》说明ContextBuilder上下文构建接口索引。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [Outputs（Utils API）](outputs.md)（`same_topic`）：Outputs（Utils API） 与《ContextBuilder》的实质衔接是：Outputs 与 Inputs/Workspace/NodeIoNum 一起填充 ContextBuilder；构造后 BuildKernelRunContext 生成 holder，GetContext 再取得 KernelContext，ContextBuilder 入口页记录这条链式构建流程。
- [Workspace（Utils API）](workspace.md)（`same_topic`）：ContextBuilder 索引明确列出 Workspace 注入和最终 BuildTilingContext/BuildKernelRunContext 两种构建出口。
<!-- cannbot:related:end -->
