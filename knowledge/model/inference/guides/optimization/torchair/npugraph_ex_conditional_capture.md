---
type: Guide
title: npugraph_ex torch.cond：设备条件、分支输出与原地限制
description: 记录主线条件捕获的版本、驱动、别名、多流与嵌套 mutation 失效边界。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/cond.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# npugraph_ex torch.cond：设备条件、分支输出与原地限制

## 版本与范围

依据 TorchAir 固定主线候选 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`。主线候选软件配套尚未确认，不推定 26.0/PyTorch2.8 支持。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 捕获条件

主线将两分支编译进同一 aclgraph，运行时由设备 bool 标量 Tensor pred 选择，不回读 Host。文档要求 torch_npu 包版本≥2.12，并依赖驱动/固件条件节点捕获接口；低版本缺接口或空条件指针分别有明确报错，不能只升级 TorchAir。

两分支返回数量、嵌套结构、dtype/device/layout、维数和 shape 必须一致。分支不能直接返回输入或其 view；确需该值时返回 clone，避免别名约束被破坏。

## Mutation 与资源 scope

分支原地写入参时，torch.cond 必须最外层，且调用位于 torch.no_grad()。固定主线文档指出嵌套 cond 的内层 mutation 在 PyTorch2.12+ 可能静默丢失、返回仍正确；2.10/2.11 为直接报错，aot_eager 也有相应表现。不能用返回值 parity 一项排除原地状态丢失。

跨流依赖需显式 Event，同一 Event 必须在使用它的分支内创建。外层 deterministic scope 会作用于分支；外层 limit_core_num 不保证作用于分支，需要在分支内分别配置。不要把两个 scope 的传播语义混同。

应同时比较两分支输出与调用后缓存，并覆盖 pred 真/假、嵌套及跨流场景；本卡不建议依赖上述嵌套原地写路径。


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/cond.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
