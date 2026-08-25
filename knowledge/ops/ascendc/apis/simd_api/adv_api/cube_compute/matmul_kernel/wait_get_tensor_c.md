---
type: API
title: WaitGetTensorC
description: 当使用GetTensorC异步接口将结果矩阵从GM拷贝到UB，且UB后续需要进行Vector计算时，需要调用WaitGetTensorC进行同步。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/WaitGetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# WaitGetTensorC

当使用GetTensorC异步接口将结果矩阵从GM拷贝到UB，且UB后续需要进行Vector计算时，需要调用WaitGetTensorC进行同步。

函数原型：__aicore__ inline void WaitGetTensorC()

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetTensorC](get_tensor_c.md)（`related`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《WaitGetTensorC》说明当使用GetTensorC异步接口将结果矩阵从GM拷贝到UB，且UB后续需要进行Vector计算时，需要调用WaitGetTensorC进行同步。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [SetWorkspace](set_workspace.md)（`related`）：异步取 C 到 UB 的使用流程依赖 Matmul 初始化和 workspace 配置，错误资源配置会先于等待点失败。
- [WaitIterateAll](wait_iterate_all.md)（`related`）：WaitIterateAll 等待 Cube 计算，而 WaitGetTensorC 等待 C 搬运；两类等待点分别保护计算完成和搬运后消费。
- [AsyncGetTensorC](async_get_tensor_c.md)（`same_topic`）：AsyncGetTensorC 发起异步结果获取，WaitGetTensorC 正是等待该传输完成后再交给 Vector 使用。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：焦点处理Matmul 高阶 API 的对象配置、迭代与取结果调用顺序；WaitGetTensorC正文界定“当使用GetTensorC异步接口将结果矩阵从GM拷贝到UB，且UB后续需要进行Vector计算时，需要调用WaitGetTensorC进行同步”。候选是用法正文明确需要的注册、Init、SetTensor、Iterate、GetTensorC、Wait/End 阶段；只保留这条执行路径。
<!-- cannbot:related:end -->
