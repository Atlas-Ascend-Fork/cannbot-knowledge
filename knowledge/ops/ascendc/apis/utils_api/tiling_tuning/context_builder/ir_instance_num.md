---
type: API
title: IrInstanceNum
description: 基于算子的IR定义，声明实例化时每种输入的实际个数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/IrInstanceNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# IrInstanceNum

基于算子 IR 定义，声明实例化时每种输入的实际个数。函数签名为 ContextBuilder& IrInstanceNum(std::vector<uint32_t> instanceNum)。
参数 instanceNum 为按输入 index 顺序声明的实例化个数向量，用于描述动态类型输入 Tensor 的实例数量。
返回当前 ContextBuilder 对象，支持链式调用。
约束：必须配合 NodeIoNum 一同使用，先通过 NodeIoNum 设置算子输入输出个数，再通过 IrInstanceNum 设置实例化个数。
典型用法：builder.NodeIoNum(5,3).IrInstanceNum({1, 1, 3, 1, 1})，表示 index 为 2 的动态类型输入有 3 个实例。

<!-- cannbot:related:start -->
## 相关

- [AddInputTd](add_input_td.md)（`related`）：IrInstanceNum 声明每类 IR 输入的实际实例数，AddInputTd 的 index 才能按 IR 顺序合法排布。
- [BuildKernelRunContext](build_kernel_run_context.md)（`related`）：IrInstanceNum 与《BuildKernelRunContext》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [BuildTilingContext](build_tiling_context.md)（`related`）：IrInstanceNum 与《BuildTilingContext》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [ContextBuilder](context_builder.md)（`related`）：IrInstanceNum 与《ContextBuilder》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [ContextBuilder构造函数](context_builder_constructor.md)（`related`）：ContextBuilder构造函数 与《IrInstanceNum》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [Inputs（Utils API）](inputs.md)（`same_topic`）：IrInstanceNum 与《Inputs（Utils API）》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [NodeIoNum](node_io_num.md)（`same_topic`）：IrInstanceNum 与《NodeIoNum》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [Outputs（Utils API）](outputs.md)（`same_topic`）：IrInstanceNum 与《Outputs（Utils API）》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
<!-- cannbot:related:end -->
