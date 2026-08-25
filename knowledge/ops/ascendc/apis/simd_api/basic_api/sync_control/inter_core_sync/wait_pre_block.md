---
type: API
title: WaitPreBlock
description: 通过读取全局内存判断前序核是否完成，阻塞当前核直至前序核通过NotifyNextBlock通知，与InitDetermineComputeWorkspace配合实现确定性计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/WaitPreBlock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# WaitPreBlock

头文件路径为："basic_api/kernel_operator_determine_compute_sync_intf.h"。

WaitPreBlock和NotifyNextBlock是核间同步控制接口。NotifyNextBlock通过写全局内存来通知其他核当前核已执行完成，其他核可以继续往下执行；WaitPreBlock通过读取全局内存，判断当前核是否可以继续往下执行。

WaitPreBlock和NotifyNextBlock必须与InitDetermineComputeWorkspace接口配合使用，这三个接口组合使用能够确保多个AIV核严格按照blockIdx的升序执行，适用于要求确定性计算的场景，确定性计算的具体含义

参数：gmWorkspace(输入): 临时空间，通过读取gmWorkspace，判断当前核是否可以继续往下执行，类型为GlobalTensor。；ubWorkspace(输入): 临时空间，用于操作gmWorkspace，类型为LocalTensor。

约束：- 要实现确定性计算，需要保证每个核调用NotifyNextBlock/WaitPreBlock接口的次数相同。如果调用了NotifyNextBlock没有与之配对的WaitPreBlock，会导致非确定性计算、输出结果可能不符合预期；如果调用了WaitPreBlock没有与之配对的NotifyNextBlock，会导致程序卡死。
- 使用接口前，请确保已经调用InitDetermineComputeWorkspace接口，初始化共享内存。
- gmWorkspace申请的空间最少要求为：GetBlockNum()*32Bytes，ubWorkspace申请的空间最少要求为：GetBlockNum()*32+32Bytes。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core 支持。

<!-- cannbot:related:start -->
## 相关

- [GetBlockNum](../../tool_interface/system_resources_and_variables/get_block_num.md)（`related`）：WaitPreBlock 与《GetBlockNum》的实质衔接是：WaitPreBlock 必须与 NotifyNextBlock 等次数配对并先初始化 workspace；GetBlockNum 决定 GM/UB workspace 下限，关键特性说明其按 blockIdx 串行的确定性语义。
- [关键特性说明](key_features.md)（`related`）：WaitPreBlock 与《关键特性说明》的实质衔接是：WaitPreBlock 必须与 NotifyNextBlock 等次数配对并先初始化 workspace；GetBlockNum 决定 GM/UB workspace 下限，关键特性说明其按 blockIdx 串行的确定性语义。
- [InitDetermineComputeWorkspace](init_determine_compute_workspace.md)（`same_topic`）：InitDetermineComputeWorkspace：InitDetermineComputeWorkspace初始化确定性核间顺序执行所需GM空间，随后每核严格调用WaitPreBlock/NotifyNextBlock；workspace指南说明共享区的申请与传入。 目标卡《WaitPreBlock》补充：通过读取全局内存判断前序核是否完成，阻塞当前核直至前序核通过NotifyNextBlock通知，与InitDetermineComputeWorkspace配合实现确定性计算。
- [NotifyNextBlock](notify_next_block.md)（`same_topic`）：WaitPreBlock 与《NotifyNextBlock》的实质衔接是：WaitPreBlock 必须与 NotifyNextBlock 等次数配对并先初始化 workspace；GetBlockNum 决定 GM/UB workspace 下限，关键特性说明其按 blockIdx 串行的确定性语义。
<!-- cannbot:related:end -->
