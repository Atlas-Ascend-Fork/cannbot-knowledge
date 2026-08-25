---
type: API
title: WaitPreTaskEnd
description: 算子层面支持SuperKernel特性Early-Start能力的接口，在子Kernel中调用后，调用前的指令可与前序子Kernel并行执行，提升整体性能。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_task_sync/WaitPreTaskEnd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# WaitPreTaskEnd

头文件路径为："basic_api/kernel_operator_common_intf.h"。

算子层面支持SuperKernel特性Early-Start能力的接口，调用后在TorchAir层面：1.GE图模式下进行默认启用; 2.npugraph_ex后端通过early_start选项进行控制启用。

在SuperKernel的子Kernel中调用，调用前的指令可以和前序其他的子Kernel实现并行，提升整体性能。如图1所示，SuperKernel按序调用子Kernel，为保证子Kernel之间数据互不干扰，会在子Kernel间插入算子间同步进行保序，子KernelN+1调用该接口之前的指令会和前序子KernelN实现并行。

参数：FORCE: 离线编译时是否强制启用Early-Start能力，不影响在线编译。 false：离线编译时不强制启用Early-Start能力； true：离线编译时启用。

约束：- 该接口适用于TorchAir图模式开发场景，且需在启用SuperKernel特性后方可生效。
- 在算子运行过程中，需要保证此接口在每个核上都被调用，且每个核上仅被调用一次。
- 若子Kernel某个TilingKey分支调用了此接口，则开发者需要保证当前算子可能会运行的所有TilingKey均调用了此接口，否则会出现因同步指令数量不匹配而卡住的现象。

仅 Ascend 950PR/Ascend 950DT，该接口生效、Atlas A3 训练系列产品/Atlas A3 推理系列产品，该接口生效、Atlas A2 训练系列产品/Atlas A2 推理系列产品，仅保证编译兼容，实际功能不生效。、Atlas 200I/500 A2 推理产品，仅保证编译兼容，实际功能不生效。、Atlas 推理系列产品AI Core，仅保证编译兼容，实际功能不生效。、Atlas 推理系列产品Vector Core，仅保证编译兼容，实际功能不生效。、Atlas 训练系列产品，仅保证编译兼容，实际功能不生效。、Kirin X90，仅保证编译兼容，实际功能不生效。、Kirin 9030，仅保证编译兼容，实际功能不生效。 支持。
