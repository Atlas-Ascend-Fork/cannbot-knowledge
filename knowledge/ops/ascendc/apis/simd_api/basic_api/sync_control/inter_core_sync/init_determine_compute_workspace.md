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

<!-- cannbot:related:start -->
## 相关

- [如何使用workspace](../../../../../guides/programming_guide/appendix/common_operations/how_to_use_workspace.md)（`explains`）：确定性核间同步需专用 GM workspace 并按参与核初始化。
- [核函数内删除Workspace相关冗余操作](../../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/remove_workspace_redundancy.md)（`explains`）：核函数内删除Workspace相关冗余操作 与《InitDetermineComputeWorkspace》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)（`related`）：CrossCoreWaitFlag：CrossCoreWaitFlag 必须与 CrossCoreSetFlag 成对，并依赖核间同步 workspace/flag 编号约定；两个 runbook分别给出方向和双 AIV subBlock 契约的可执行诊断。 目标卡《InitDetermineComputeWorkspace》补充：基于核间顺序执行的确定性计算初始化接口，初始化GM共享内存后才能调用WaitPreBlock和NotifyNextBlock完成核间顺序执行。
- [NotifyNextBlock](notify_next_block.md)（`same_topic`）：InitDetermineComputeWorkspace：InitDetermineComputeWorkspace初始化确定性核间顺序执行所需GM空间，随后每核严格调用WaitPreBlock/NotifyNextBlock；workspace指南说明共享区的申请与传入。 目标卡《NotifyNextBlock》补充：通过写全局内存通知后序核当前核已执行完成，与WaitPreBlock和InitDetermineComputeWorkspace配合实现AIV核按blockIdx升序执行的确定性计算。
- [WaitPreBlock](wait_pre_block.md)（`same_topic`）：InitDetermineComputeWorkspace：InitDetermineComputeWorkspace初始化确定性核间顺序执行所需GM空间，随后每核严格调用WaitPreBlock/NotifyNextBlock；workspace指南说明共享区的申请与传入。 目标卡《WaitPreBlock》补充：通过读取全局内存判断前序核是否完成，阻塞当前核直至前序核通过NotifyNextBlock通知，与InitDetermineComputeWorkspace配合实现确定性计算。
<!-- cannbot:related:end -->
