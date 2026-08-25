---
type: API
title: SetWorkspace
description: Iterate计算的异步场景，调用本接口申请一块临时空间来缓存计算结果，然后调用GetTensorC时会在该临时空间中获取C的矩阵分片。
  IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetWorkspace

[Iterate](iterate.md)计算的异步场景，调用本接口申请一块临时空间来缓存计算结果，然后调用GetTensorC时会在该临时空间中获取C的矩阵分片。 IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。

函数原型：
template <class T> __aicore__ inline void SetWorkspace(GlobalTensor<T>& addr)
template <class T> __aicore__ inline void SetWorkspace(__gm__ const T* addr, int size)

参数：
- addr（输入）：用户传入的GM上的workspace空间，GlobalTensor类型。
- addr（输入）：用户传入的GM上的workspace空间，GM地址类型。
- size（输入）：传入GM地址时，需要配合传入元素个数。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [异步场景处理](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`explains`）：Iterate 异步模式必须在调用前用 SetWorkspace 提供缓存 C 分片的临时空间；否则后续计算会覆盖尚未取出的结果。
- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《SetWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [GetTensorC](get_tensor_c.md)（`related`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《SetWorkspace》说明Iterate计算的异步场景，调用本接口申请一块临时空间来缓存计算结果，然后调用GetTensorC时会在该临时空间中获取C的矩阵分片。 IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [GetUserWorkspace](../../../basic_api/resource_management/workspace/get_user_workspace.md)（`related`）：GetUserWorkspace 与《SetWorkspace》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [IterateNBatch](iterate_n_batch.md)（`related`）：IterateNBatch 明确要求先调用 SetWorkspace，并把 N 个多 Batch C 矩阵直接输出到该 GM 空间；这是 SetWorkspace 的强制消费点。
- [SetLocalWorkspace](set_local_workspace.md)（`related`）：SetWorkspace说明Iterate计算的异步场景，调用本接口申请一块临时空间来缓存计算结果，然后调用GetTensorC时会在该临时空间中获取C的矩阵分片。 IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。
- [WaitGetTensorC](wait_get_tensor_c.md)（`related`）：异步取 C 到 UB 的使用流程依赖 Matmul 初始化和 workspace 配置，错误资源配置会先于等待点失败。
- [GetBatchTensorC](get_batch_tensor_c.md)（`same_topic`）：GetBatchTensorC 与《SetWorkspace》的实质衔接是：GetBatchTensorC 只在 IterateNBatch 异步输出链中取回一片 batch C；Host batch 配置、workspace 和 WaitIterateBatch 决定该取回路径的形状与同步方式。
<!-- cannbot:related:end -->
