---
type: API
title: GetProgramCounter
description: 获取程序计数器的值，以追踪当前程序执行的位置。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetProgramCounter_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetProgramCounter

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取程序计数器的值，以追踪当前程序执行的位置。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetProgramCounter](../../../c_api/sys_var/asc_get_program_counter.md)（`same_topic`）：《GetProgramCounter》处理“获取程序计数器的值，以追踪当前程序执行的位置。”。《AscGetProgramCounter》提供“获取程序计数器的指针，用于记录当前程序执行位置。”，其具体合同或探针直接接入程序计数器的 C++/C 两层获取入口。
<!-- cannbot:related:end -->
