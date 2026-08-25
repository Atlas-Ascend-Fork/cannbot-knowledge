---
type: API
title: AscGetSystemCycle
description: 读取当前系统cycle计数器，用于性能统计与耗时测量。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_system_cycle.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetSystemCycle

读取当前系统cycle计数器，返回int64_t类型的当前计数值。该计数器为只读系统计数器，宽度64bit，复位值为0，随系统时钟持续递增，反映硬件运行以来的累计cycle数，常用于性能统计、耗时测量与执行序的时序判断。本接口在AIC与AIV上均可调用，返回值含义一致。
函数原型：int64_t asc_get_system_cycle()
返回值：返回系统Cycle数。
约束：该接口是PIPE_S流水，若需要测试其他流水的指令时间，需要在调用该接口前插入对应流水的同步。；本接口为只读查询接口，读取的是只读系统计数器，不修改任何寄存器或存储状态，可在AIC与AIV上下文中调用。；返回值由系统时钟计数器实时提供，随系统时钟持续递增，不反映Kernel启动配置或其他静态参数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscGetProgramCounter](asc_get_program_counter.md)（`related`）：ProgramCounter 标识当前指令位置，SystemCycle 提供时间轴；二者结合可做位置标记与性能耗时诊断。
- [AscTimeStamp](../../../utils_api/tuning_interface/asc_time_stamp.md)（`related`）：“AscGetSystemCycle”处理读取当前系统cycle计数器，用于性能统计与耗时测量。；“AscTimeStamp”明确SIMD场景下提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点，便于调试和性能分析。。实质衔接：AscGetSystemCycle 提供原始 cycle；GetSystemCycle 是同义层接口，PrintTimeStamp/AscTimeStamp 是直接消费该计数器的打点能力。
- [PrintTimeStamp](../../basic_api/debug_interface/onboard_print/print_time_stamp.md)（`related`）：“AscGetSystemCycle”处理读取当前系统cycle计数器，用于性能统计与耗时测量。；“PrintTimeStamp”明确提供时间戳打点功能，用于在算子Kernel代码中标记关键执行点并打印当前系统cycle数。。实质衔接：AscGetSystemCycle 提供原始 cycle；GetSystemCycle 是同义层接口，PrintTimeStamp/AscTimeStamp 是直接消费该计数器的打点能力。
- [GetSystemCycle](../../basic_api/tool_interface/system_resources_and_variables/get_system_cycle_isasi.md)（`same_topic`）：GetSystemCycle 与 AscGetSystemCycle 都读取同一个系统 cycle 计数器，并以两次读数差计算耗时；它们是 Basic API 与 C API 的直接对应。
<!-- cannbot:related:end -->
