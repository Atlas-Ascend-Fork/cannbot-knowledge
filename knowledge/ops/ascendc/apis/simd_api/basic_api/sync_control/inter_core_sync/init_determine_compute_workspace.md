---
type: API
title: InitDetermineComputeWorkspace
description: 基于核间顺序执行的确定性计算初始化接口，初始化GM共享内存后才能调用WaitPreBlock和NotifyNextBlock完成核间顺序执行。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/InitDetermineComputeWorkspace.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitDetermineComputeWorkspace

头文件路径为："basic_api/kernel_operator_determine_compute_sync_intf.h"。

InitDetermineComputeWorkspace是基于核间顺序执行的确定性计算的初始化配置接口，能够初始化GM共享内存的值，完成初始化后才可以调用WaitPreBlock和NotifyNextBlock。以上三个接口共同完成基于核间顺序执行的确定性计算，确定性计算的具体含义

参数：gmWorkspace(输入): 临时空间，初始化核间同步的共享内存，类型为GlobalTensor。；ubWorkspace(输入): 临时空间，用于操作gmWorkspace，类型为LocalTensor。

约束：- gmWorkspace申请的空间最少要求为：GetBlockNum()*32Bytes，ubWorkspace申请的空间最少要求为：GetBlockNum()*32+32Bytes。
- 与IBSet/SyncAll不同，该接口输入参数gmWorkspace缓存的值不需要初始化为0。
- 使用该接口进行多核控制时，算子调用时指定的逻辑AI Core核数numBlocks必须保证不大于实际运行该算子的AI处理器核数，否则框架进行多轮调度时会插入异常同步，导致Kernel“卡死”现象。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core 支持。
