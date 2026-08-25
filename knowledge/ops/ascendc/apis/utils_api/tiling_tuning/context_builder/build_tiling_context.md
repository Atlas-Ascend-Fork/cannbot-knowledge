---
type: API
title: BuildTilingContext
description: 构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/BuildTilingContext.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# BuildTilingContext

## 功能说明
构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。
## 函数原型
## 参数说明
无
## 返回值说明
指向KernelRunContextHolder的共享指针。
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：BuildTilingContext 与《TilingDebug》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [AddInputTd](add_input_td.md)（`related`）：添加全部输入描述后由 BuildTilingContext 生成可供 Tiling 函数调测的上下文，闭合构建流程。
- [AddOutputTd](add_output_td.md)（`related`）：BuildTilingContext 与《AddOutputTd》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [Inputs（Utils API）](inputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《BuildTilingContext》说明构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [IrInstanceNum](ir_instance_num.md)（`related`）：IrInstanceNum 与《BuildTilingContext》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [NodeIoNum](node_io_num.md)（`related`）：完成 IO 数量、实例数和描述配置后由 BuildTilingContext 生成可调用 tiling 函数的上下文。
- [Outputs（Utils API）](outputs.md)（`related`）：BuildTilingContext 与《Outputs（Utils API）》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [PlatformInfo](platform_info.md)（`related`）：《PlatformInfo》说明将指向fe::PlatFormInfos的指针传入TilingContext。；《BuildTilingContext》说明构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。二者在PlatformInfo向ContextBuilder注入fe::PlatFormInfos且只允许BuildTilingContext路径；AddPlatformInfo与Tiling调测流程给出构造和消费闭环上存在可执行的直接衔接。
- [SetOpNameType](set_op_name_type.md)（`related`）：完成名字、类型和 IO 元数据配置后，由 BuildTilingContext 生成 tiling 调用上下文。
- [Tiling调测](../tiling_tuning.md)（`related`）：BuildTilingContext 与《Tiling调测》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [Utils API简介](intro.md)（`related`）：简介说明 ContextBuilder 用于手工构造 TilingContext，BuildTilingContext 是将 inputs、attrs、platform 等配置固化的终点。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《BuildTilingContext》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddPlatformInfo](add_platform_info.md)（`same_topic`）：AddPlatformInfo 与《BuildTilingContext》的实质衔接是：AddPlatformInfo 把 PlatformInfo 注入 ContextBuilder，随后 BuildTiling/KernelRunContext 消费；PlatformAscendC/Manager 是平台能力信息的来源。
- [BuildKernelRunContext](build_kernel_run_context.md)（`same_topic`）：BuildTilingContext 与《BuildKernelRunContext》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [CompileInfo](compile_info.md)（`same_topic`）：CompileInfo 与《BuildTilingContext》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder](context_builder.md)（`same_topic`）：BuildTilingContext 与《ContextBuilder》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：BuildTilingContext 与《ContextBuilder构造函数》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [KernelRunContextHolder结构定义](kernel_run_context_holder_struct_definition.md)（`same_topic`）：BuildTilingContext 与《KernelRunContextHolder结构定义》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [TilingData](tiling_data.md)（`same_topic`）：“TilingData”处理传入指向TilingData的void\ 指针；“BuildTilingContext”明确构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。实质衔接：ContextBuilder::TilingData 只有在 BuildTilingContext 前提下有效，其他 Context 应改用 Outputs；TilingDebug 展示该上下文构造流程。
- [Workspace（Utils API）](workspace.md)（`same_topic`）：Workspace 的约束要求后续走 BuildTilingContext；该接口正是将注入布局解释成 TilingContext 的消费者。
<!-- cannbot:related:end -->
