---
type: API
title: AddOutputTd
description: 为算子增加输入Tensor的描述。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddOutputTd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddOutputTd

为算子增加输出 Tensor 的描述信息。函数签名为 ContextBuilder& AddOutputTd(int32_t index, ge::DataType dtype, ge::Format originFormat, ge::Format storageFormat, gert::StorageShape storageShape)。
参数 index 为算子输出索引（从 0 开始）；dtype 为输出数据类型；originFormat 为原始格式；storageFormat 为运行时格式；storageShape 为输出 Shape。
返回当前 ContextBuilder 对象，支持链式调用。
约束：调用 AddOutputTd 前需要先调用 NodeIoNum 与 IrInstanceNum 接口设置算子输入输出个数与实例化个数。
典型用法：builder.NodeIoNum(1,1).IrInstanceNum({1}).AddOutputTd(0, ge::DT_FLOAT16, ge::FORMAT_ND, ge::FORMAT_ND, output_shape)。

<!-- cannbot:related:start -->
## 相关

- [GetOutputViewTensor 私有致 op_host 编译失败](../../../../runbooks/compilation/getoutputviewtensor_op_host.md)（`exemplifies`）：AddOutputTd 与《GetOutputViewTensor 私有致 op_host 编译失败》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [BuildTilingContext](build_tiling_context.md)（`related`）：BuildTilingContext 与《AddOutputTd》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [Inputs（Utils API）](inputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《AddOutputTd》说明为算子增加输入Tensor的描述。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [NodeIoNum](node_io_num.md)（`related`）：NodeIoNum 建立输出槽位数量后，AddOutputTd 填充输出描述，数量必须与声明保持一致。
- [Output（OpDef）](../../prototype_register_management/op_def/output.md)（`related`）：AddOutputTd 与《Output（OpDef）》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [Workspace（Utils API）](workspace.md)（`related`）：AddOutputTd 与《Workspace（Utils API）》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [AddInputTd](add_input_td.md)（`same_topic`）：AddOutputTd 与《AddInputTd》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [ContextBuilder](context_builder.md)（`same_topic`）：AddOutputTd 与《ContextBuilder》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：ContextBuilder构造函数 与《AddOutputTd》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [Outputs（Utils API）](outputs.md)（`same_topic`）：AddOutputTd 与《Outputs（Utils API）》的实质衔接是：AddOutputTd 与输入/输出/工作空间描述共同构造 tiling context；context builder、output view 故障和 OpDef Output 说明其 host 侧消费位置。
<!-- cannbot:related:end -->
