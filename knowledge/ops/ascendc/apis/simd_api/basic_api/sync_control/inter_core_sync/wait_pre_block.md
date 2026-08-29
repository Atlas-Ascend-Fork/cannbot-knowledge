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

- [InitDetermineComputeWorkspace](init_determine_compute_workspace.md)（`related`）：“完成初始化后才可以调用WaitPreBlock和NotifyNextBlock”规定 Wait 的初始化依赖；“WaitPreBlock和NotifyNextBlock必须与InitDetermineComputeWorkspace接口配合使用”从等待接口侧确认三接口共同维持 blockIdx 升序。
- [NotifyNextBlock](notify_next_block.md)（`related`）：按“NotifyNextBlock通过写全局内存来通知其他核当前核已执行完成，其他核可以继续往下执行；WaitPreBlock通过读取全局内存，判断当前核是否可以继续往下执行。”把每次写通知与后序核读等待组成握手，并用“如果调用了NotifyNextBlock没有与之配对的WaitPreBlock，会导致非确定性计算、输出结果可能不符合预期；如果调用了WaitPreBlock没有与之配对的NotifyNextBlock，会导致程序卡死。”检查所有核的调用次数相同，能定位漏 Notify 或漏 Wait 的具体故障。
<!-- cannbot:related:end -->
