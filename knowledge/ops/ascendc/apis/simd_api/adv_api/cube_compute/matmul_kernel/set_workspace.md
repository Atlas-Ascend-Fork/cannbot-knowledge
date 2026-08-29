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

- [IterateNBatch](iterate_n_batch.md)（`same_topic`）：IterateNBatch计算时，调用本接口申请一块临时空间来缓存计算结果，然后根据同步或异步场景进行其它接口的调用。在调用该接口前，需将MatmulConfig中的isNBatch参数设为true，开启多Batch输入多Batch输出功能，并调用SetWorkspace接口申请临时空间，用于缓存计算结果，即IterateNBatch的结果输出至SetWorkspace指定的Global Memory内存中。SetWorkspace 卡定义缓存结果的 GM 空间，IterateNBatch 卡把这块空间列为调用前置并规定结果写入位置；二者构成同一次多 Batch Matmul 调用的资源申请和输出合同。
<!-- cannbot:related:end -->
