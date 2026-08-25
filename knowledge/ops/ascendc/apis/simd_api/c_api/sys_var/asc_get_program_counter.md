---
type: API
title: AscGetProgramCounter
description: 获取程序计数器的指针，用于记录当前程序执行位置。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_program_counter.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetProgramCounter

获取程序计数器的指针，程序计数器用于记录当前程序执行的位置。
函数原型：int64_t asc_get_program_counter()
返回值：返回int64_t类型的程序计数器指针。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscGetSystemCycle](asc_get_system_cycle.md)（`related`）：ProgramCounter 标识当前指令位置，SystemCycle 提供时间轴；二者结合可做位置标记与性能耗时诊断。
- [GetProgramCounter](../../basic_api/tool_interface/system_resources_and_variables/get_program_counter_isasi.md)（`same_topic`）：《GetProgramCounter》处理“获取程序计数器的值，以追踪当前程序执行的位置。”。《AscGetProgramCounter》提供“获取程序计数器的指针，用于记录当前程序执行位置。”，其具体合同或探针直接接入程序计数器的 C++/C 两层获取入口。
<!-- cannbot:related:end -->
