---
type: API
title: AddInputTd
description: 为算子增加输入Tensor的描述
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddInputTd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddInputTd

## 功能说明
为算子增加输入Tensor的描述
## 函数原型
## 参数说明
## 返回值说明
当前ContextBuilder的对象。
## 约束说明
输入的index需要基于算子IR定义，按照IrInstanceNum声明顺序来排布；
调用AddInputTd前需要调用NodeIoNum与IrInstanceNum接口

<!-- cannbot:related:start -->
## 相关

- [BuildTilingContext](build_tiling_context.md)（`related`）：添加全部输入描述后由 BuildTilingContext 生成可供 Tiling 函数调测的上下文，闭合构建流程。
- [Inputs（Utils API）](inputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《AddInputTd》说明为算子增加输入Tensor的描述。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [IrInstanceNum](ir_instance_num.md)（`related`）：IrInstanceNum 声明每类 IR 输入的实际实例数，AddInputTd 的 index 才能按 IR 顺序合法排布。
- [NodeIoNum](node_io_num.md)（`related`）：AddInputTd 前必须用 NodeIoNum 声明节点输入输出总数，否则 ContextBuilder 无法定位描述槽。
- [SetOpNameType](set_op_name_type.md)（`related`）：设置算子名和类型后才能添加输入 TensorDesc，二者有明确调用先后。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《AddInputTd》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddOutputTd](add_output_td.md)（`same_topic`）：AddOutputTd 与《AddInputTd》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：ContextBuilder构造函数 与《AddInputTd》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
<!-- cannbot:related:end -->
