---
type: API
title: Inputs（Utils API）
description: 将void\ 指针的vector设置为KernelContext的inputs
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/Inputs.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Inputs

将 void* 指针的 vector 设置为 KernelContext 的 inputs。函数签名为 ContextBuilder& Inputs(std::vector<void*> inputs)。
参数 inputs 为保存输入的 void* 指针 vector，每个元素对应一个输入的指针。
返回当前 ContextBuilder 对象，支持链式调用。
无特殊约束。
典型用法：auto contextBuilder = context_ascendc::ContextBuilder().Inputs({nullptr, reinterpret_cast<void*>(&platformInfo)})，将平台信息指针等作为输入设置到 KernelContext 中。

<!-- cannbot:related:start -->
## 相关

- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《optional input 未连接触发 InferShape 失败》说明OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [AddInputTd](add_input_td.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《AddInputTd》说明为算子增加输入Tensor的描述。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [AddOutputTd](add_output_td.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《AddOutputTd》说明为算子增加输入Tensor的描述。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [BuildKernelRunContext](build_kernel_run_context.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《BuildKernelRunContext》说明构造KernelRunContext并返回KernelRunContextHolder的智能指针，该对象可通过GetContext接口获取KernelContext类型的对象。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [BuildTilingContext](build_tiling_context.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《BuildTilingContext》说明构造KernelRunContextHolder的对象，该对象可通过GetContext接口获取TilingContext类型的对象。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [ContextBuilder构造函数](context_builder_constructor.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《ContextBuilder构造函数》说明创建ContextBuilder对象时，初始化数据成员。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [KernelRunContextHolder结构定义](kernel_run_context_holder_struct_definition.md)（`related`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [Outputs（Utils API）](outputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《Outputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的output。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [ContextBuilder](context_builder.md)（`same_topic`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《ContextBuilder》说明ContextBuilder上下文构建接口索引。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [IrInstanceNum](ir_instance_num.md)（`same_topic`）：IrInstanceNum 与《Inputs（Utils API）》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
<!-- cannbot:related:end -->
