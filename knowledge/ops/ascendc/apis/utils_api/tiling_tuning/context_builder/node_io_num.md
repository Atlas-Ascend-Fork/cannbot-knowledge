---
type: API
title: NodeIoNum
description: 声明算子定义的输入与输出个数
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/NodeIoNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NodeIoNum

声明算子定义的输入与输出个数。函数签名为 ContextBuilder& NodeIoNum(size_t inputNum, size_t outputNum)。
参数 inputNum 为算子 IR 原型定义中的输入个数，outputNum 为输出个数。
返回当前 ContextBuilder 对象，支持链式调用。
约束：必须配合 IrInstanceNum 一同使用，先通过 NodeIoNum 设置输入输出个数，再通过 IrInstanceNum 设置每种输入的实例化个数。
典型用法：auto builder = ContextBuilder().NodeIoNum(5, 3)，表示该算子有 5 个输入和 3 个输出。

<!-- cannbot:related:start -->
## 相关

- [AddInputTd](add_input_td.md)（`related`）：AddInputTd 前必须用 NodeIoNum 声明节点输入输出总数，否则 ContextBuilder 无法定位描述槽。
- [AddOutputTd](add_output_td.md)（`related`）：NodeIoNum 建立输出槽位数量后，AddOutputTd 填充输出描述，数量必须与声明保持一致。
- [BuildTilingContext](build_tiling_context.md)（`related`）：完成 IO 数量、实例数和描述配置后由 BuildTilingContext 生成可调用 tiling 函数的上下文。
- [ContextBuilder构造函数](context_builder_constructor.md)（`related`）：ContextBuilder构造函数 与《NodeIoNum》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [IrInstanceNum](ir_instance_num.md)（`same_topic`）：IrInstanceNum 与《NodeIoNum》的实质衔接是：IrInstanceNum 必须在 NodeIoNum 后声明动态输入实例数，Inputs/Outputs、ContextBuilder 与 BuildContext 共同决定构造出的 tiling/kernel context。
- [Outputs（Utils API）](outputs.md)（`same_topic`）：Outputs（Utils API） 与《NodeIoNum》的实质衔接是：Outputs 与 Inputs/Workspace/NodeIoNum 一起填充 ContextBuilder；构造后 BuildKernelRunContext 生成 holder，GetContext 再取得 KernelContext，ContextBuilder 入口页记录这条链式构建流程。
<!-- cannbot:related:end -->
