---
type: API
title: GetSystemCycle
description: 获取系统计数器当前的cycle值，通过前后差值可计算代码段执行时间。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetSystemCycle_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetSystemCycle

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取系统计数器当前的cycle值。通过计算代码段前后cycle值的差值，可得到代码段消耗的系统cycle数，再通过换算即可获得代码段的执行时间。

针对Ascend 950PR/Ascend 950DT，若换算成时间需要按照1GHz的频率，时间单位为us，换算公式为：time = (cycle数/1000)us。

针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，若换算成时间需要按照50MHz的频率，时间单位为us，换算公式为：time = (cycle数/50)us。

针对Atlas A2 训练系列产品/Atlas A2 推理系列产品，若换算成时间需要按照50MHz的频率，时间单位为us，换算公式为：time = (cycle数/50)us。

约束：该接口属于PIPE_S流水，若需要测试其他流水的指令时间，需要在调用该接口前通过PipeBarrier插入对应流水的同步，具体

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [选择低延迟指令，优化归约操作性能](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md)（`explains`）：指南的 cycle 对比通过 GetSystemCycle 测量，接口卡提供复现 ReduceRepeat/ReduceDataBlock 选择所需的计时原语。
- [PipeBarrier](../../sync_control/intra_core_sync/pipe_barrier_isasi.md)（`related`）：GetSystemCycle 正文要求测量 Vector/MTE 等异步流水前先做对应同步，否则时间戳只反映 Scalar 发射而非工作完成；PipeBarrier 提供这一前置完成性约束。
- [PrintTimeStamp](../../debug_interface/onboard_print/print_time_stamp.md)（`related`）：“PrintTimeStamp”处理提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。；“GetSystemCycle”明确获取系统计数器当前的cycle值，通过前后差值可计算代码段执行时间。。实质衔接：PrintTimeStamp 以系统 cycle 为时间基准；AscTimeStamp 是同一打点能力，MarkStamp 是流水标记替代，GetSystemCycle 提供换算基准。
- [AscGetSystemCycle](../../../c_api/sys_var/asc_get_system_cycle.md)（`same_topic`）：GetSystemCycle 与 AscGetSystemCycle 都读取同一个系统 cycle 计数器，并以两次读数差计算耗时；它们是 Basic API 与 C API 的直接对应。
<!-- cannbot:related:end -->
