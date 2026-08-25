---
type: API
title: Outputs（Utils API）
description: 将void\ 指针的vector设置为KernelContext的output。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/Outputs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Outputs

将 void* 指针的 vector 设置为 KernelContext 的 outputs。函数签名为 ContextBuilder& Outputs(std::vector<void*> outputs)。
参数 outputs 为保存输出的 void* 指针 vector，每个元素对应一个输出的指针。
返回当前 ContextBuilder 对象，支持链式调用。
无特殊约束。
典型用法：auto contextBuilder = context_ascendc::ContextBuilder().Outputs({nullptr, reinterpret_cast<void*>(&platformInfo)})，将输出指针设置到 KernelContext 中。

<!-- cannbot:related:start -->
## 相关

- [BuildKernelRunContext](build_kernel_run_context.md)（`related`）：Outputs 配置输出 Tensor 描述，是 BuildKernelRunContext 生成完整 kernel 调用上下文前的另一必要输入。
- [BuildTilingContext](build_tiling_context.md)（`related`）：BuildTilingContext 与《Outputs（Utils API）》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [ContextBuilder构造函数](context_builder_constructor.md)（`related`）：ContextBuilder构造函数 与《Outputs（Utils API）》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [Inputs（Utils API）](inputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《Outputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的output。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [KernelRunContextHolder结构定义](kernel_run_context_holder_struct_definition.md)（`related`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《Outputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的output。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [Workspace（Utils API）](workspace.md)（`related`）：Workspace 正文明确指出非 BuildTilingContext 场景应改用 Outputs，目标卡给出 void* 输出表的合法注入方式。
- [AddOutputTd](add_output_td.md)（`same_topic`）：AddOutputTd 与《Outputs（Utils API）》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [CompileInfo](compile_info.md)（`same_topic`）：CompileInfo 与《Outputs（Utils API）》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder](context_builder.md)（`same_topic`）：Outputs（Utils API） 与《ContextBuilder》的实质衔接是：Outputs 与 Inputs/Workspace/NodeIoNum 一起填充 ContextBuilder；构造后 BuildKernelRunContext 生成 holder，GetContext 再取得 KernelContext，ContextBuilder 入口页记录这条链式构建流程。
- [IrInstanceNum](ir_instance_num.md)（`same_topic`）：IrInstanceNum 与《Outputs（Utils API）》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [NodeIoNum](node_io_num.md)（`same_topic`）：Outputs（Utils API） 与《NodeIoNum》的实质衔接是：Outputs 与 Inputs/Workspace/NodeIoNum 一起填充 ContextBuilder；构造后 BuildKernelRunContext 生成 holder，GetContext 再取得 KernelContext，ContextBuilder 入口页记录这条链式构建流程。
- [TilingData](tiling_data.md)（`same_topic`）：“TilingData”处理传入指向TilingData的void\ 指针；“Outputs（Utils API）”明确将void\ 指针的vector设置为KernelContext的output。。实质衔接：ContextBuilder::TilingData 只有在 BuildTilingContext 前提下有效，其他 Context 应改用 Outputs；TilingDebug 展示该上下文构造流程。
<!-- cannbot:related:end -->
