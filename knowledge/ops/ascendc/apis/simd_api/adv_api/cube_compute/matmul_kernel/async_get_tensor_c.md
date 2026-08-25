---
type: API
title: AsyncGetTensorC
description: 获取Iterate接口异步计算的结果矩阵。该接口功能已被GetTensorC覆盖，建议直接使用GetTensorC异步接口。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/AsyncGetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AsyncGetTensorC

获取Iterate接口异步计算的结果矩阵。该接口功能已被GetTensorC覆盖，建议直接使用GetTensorC异步接口。

函数原型：__aicore__ inline void AsyncGetTensorC(const LocalTensor<DstT>& c)

参数：
- c：输出结果矩阵

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBatchC](get_batch_c.md)（`related`）：GetBatchC 与《AsyncGetTensorC》的实质衔接是：GetBatchC 在 Batch Matmul 的 IterateBatch/NBatch 与等待流程后取回结果；Tensor 版本、batch 数配置和使用指南解释同一输出契约。
- [WaitIterateAll](wait_iterate_all.md)（`related`）：WaitIterateAll 与《AsyncGetTensorC》的实质衔接是：WaitIterateAll 是 IterateAll 连续写 GM 异步路径的完成屏障；异步场景、Matmul 用法及 TensorC 获取协议说明何时等待以及等待后何时可消费输出。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：《GetTensorC》说明Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。；《AsyncGetTensorC》说明获取Iterate接口异步计算的结果矩阵。该接口功能已被GetTensorC覆盖，建议直接使用GetTensorC异步接口。。二者在Iterate产出的C分片必须按同步或异步GetTensorC协议搬出，并在异步模式等待完成后才能复用资源上存在可执行的直接衔接。
- [Iterate](iterate.md)（`same_topic`）：Iterate 与《AsyncGetTensorC》的实质衔接是：Iterate 每次推进一块 baseM×baseN 并管理 L0C；Init/SetTensor 后需按同步模式配对 GetTensorC/Wait，IterateAll/NBatch/Batch 与异步指南给出替代执行契约。
- [WaitGetTensorC](wait_get_tensor_c.md)（`same_topic`）：AsyncGetTensorC 发起异步结果获取，WaitGetTensorC 正是等待该传输完成后再交给 Vector 使用。
<!-- cannbot:related:end -->
