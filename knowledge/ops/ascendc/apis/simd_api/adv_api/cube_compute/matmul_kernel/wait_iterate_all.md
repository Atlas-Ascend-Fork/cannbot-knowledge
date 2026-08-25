---
type: API
title: WaitIterateAll
description: 等待IterateAll异步接口返回，支持连续输出到Global Memory。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/WaitIterateAll.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# WaitIterateAll

等待IterateAll异步接口返回，支持连续输出到Global Memory。

函数原型：__aicore__ inline void WaitIterateAll()

约束：
- 配套IterateAll异步接口使用。
- 仅支持连续输出至Global Memory。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../../../../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_iterate_avoid_sync.md)（`explains`）：异步提交后必须在真正消费/释放前 WaitIterateAll。
- [异步场景处理](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/async_scenario.md)（`explains`）：WaitIterateAll 是指南指定的 IterateAll 异步完成等待点，使后续消费者在结果真正就绪后继续。
- [AsyncGetTensorC](async_get_tensor_c.md)（`related`）：WaitIterateAll 与《AsyncGetTensorC》的实质衔接是：WaitIterateAll 是 IterateAll 连续写 GM 异步路径的完成屏障；异步场景、Matmul 用法及 TensorC 获取协议说明何时等待以及等待后何时可消费输出。
- [Matmul使用说明](matmul_usage.md)（`related`）：WaitIterateAll 与《Matmul使用说明》的实质衔接是：WaitIterateAll 是 IterateAll 连续写 GM 异步路径的完成屏障；异步场景、Matmul 用法及 TensorC 获取协议说明何时等待以及等待后何时可消费输出。
- [WaitGetTensorC](wait_get_tensor_c.md)（`related`）：WaitIterateAll 等待 Cube 计算，而 WaitGetTensorC 等待 C 搬运；两类等待点分别保护计算完成和搬运后消费。
- [IterateAll](iterate_all.md)（`same_topic`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《WaitIterateAll》说明等待IterateAll异步接口返回，支持连续输出到Global Memory。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
<!-- cannbot:related:end -->
